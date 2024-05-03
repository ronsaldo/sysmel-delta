#include "compilerRiscV.h"
#include "assert.h"
#include "module.h"
#include "elf.h"
#include "coff.h"
#include "macho.h"
#include "dwarf.h"
#include "utils.h"
#include <string.h>

void sdvm_compiler_riscv_emitFunctionEpilogue(sdvm_functionCompilationState_t *state);

#define SDVM_RISCV_INTEGER_REG_DEF(name, regValue) \
const sdvm_compilerRegister_t sdvm_riscv32_ ## name = {\
    .kind = SdvmCompRegisterKindInteger, \
    .size = 4, \
    .value = regValue, \
}; \
const sdvm_compilerRegister_t sdvm_riscv64_ ## name = {\
    .kind = SdvmCompRegisterKindInteger, \
    .size = 8, \
    .value = regValue, \
}; \
const sdvm_compilerRegister_t sdvm_riscv64_ ## name##W = {\
    .kind = SdvmCompRegisterKindInteger, \
    .size = 4, \
    .value = regValue, \
};
#include "riscvRegs.inc"
#undef SDVM_RISCV_INTEGER_REG_DEF

static const sdvm_compilerRegister_t *sdvm_riscv32_abi_integerPassingRegisters[] = {
    &sdvm_riscv32_A0, &sdvm_riscv32_A1, &sdvm_riscv32_A2, &sdvm_riscv32_A3,
    &sdvm_riscv32_A4, &sdvm_riscv32_A5, &sdvm_riscv32_A6, &sdvm_riscv32_A7,
};
static const uint32_t sdvm_riscv32_abi_integerPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv32_abi_integerPassingRegisters);

static const sdvm_compilerRegister_t *sdvm_riscv64_abi_integerPassingRegisters[] = {
    &sdvm_riscv64_A0, &sdvm_riscv64_A1, &sdvm_riscv64_A2, &sdvm_riscv64_A3,
    &sdvm_riscv64_A4, &sdvm_riscv64_A5, &sdvm_riscv64_A6, &sdvm_riscv64_A7,
};
static const uint32_t sdvm_riscv64_abi_integerPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv64_abi_integerPassingRegisters);

static const sdvm_compilerRegister_t *sdvm_riscv64_abi_integerPassingDwordRegisters[] = {
    &sdvm_riscv64_A0W, &sdvm_riscv64_A1W, &sdvm_riscv64_A2W, &sdvm_riscv64_A3W,
    &sdvm_riscv64_A4W, &sdvm_riscv64_A5W, &sdvm_riscv64_A6W, &sdvm_riscv64_A7W,
};
static const uint32_t sdvm_riscv64_abi_integerPassingDwordRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv64_abi_integerPassingDwordRegisters);

static const sdvm_compilerRegisterValue_t sdvm_riscv_abi_allocatableIntegerRegisters[] = {
    // Temporary registers
    SDVM_RISCV_T0, SDVM_RISCV_T1, SDVM_RISCV_T2,SDVM_RISCV_T3, SDVM_RISCV_T4,
    SDVM_RISCV_T4,

    // Argument registers
    SDVM_RISCV_A0, SDVM_RISCV_A1, SDVM_RISCV_A2, SDVM_RISCV_A3,
    SDVM_RISCV_A4, SDVM_RISCV_A5, SDVM_RISCV_A6, SDVM_RISCV_A7,

    SDVM_RISCV_T5, // Temporary / Closure pointer
    SDVM_RISCV_T6, // Closure GC pointer

    // Call preserved registers.
    SDVM_RISCV_S1, SDVM_RISCV_S2, SDVM_RISCV_S3, SDVM_RISCV_S4,
    SDVM_RISCV_S5, SDVM_RISCV_S6, SDVM_RISCV_S7, SDVM_RISCV_S8,
    SDVM_RISCV_S9, SDVM_RISCV_S10, SDVM_RISCV_S11,
    
};
static const uint32_t sdvm_riscv_abi_allocatableIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv_abi_allocatableIntegerRegisters);

static const sdvm_compilerRegisterValue_t sdvm_riscv_abi_callPreservedIntegerRegisters[] = {
    SDVM_RISCV_S1, SDVM_RISCV_S2, SDVM_RISCV_S3, SDVM_RISCV_S4,
    SDVM_RISCV_S5, SDVM_RISCV_S6, SDVM_RISCV_S7, SDVM_RISCV_S8,
    SDVM_RISCV_S9, SDVM_RISCV_S10, SDVM_RISCV_S11,

    SDVM_RISCV_FP, SDVM_RISCV_RA, SDVM_RISCV_SP,
};
static const uint32_t sdvm_riscv_abi_callPreservedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv_abi_callPreservedIntegerRegisters);

static const sdvm_compilerRegisterValue_t sdvm_riscv_abi_callTouchedIntegerRegisters[] = {
    SDVM_RISCV_X0, SDVM_RISCV_X1, SDVM_RISCV_X2, SDVM_RISCV_X3,
    SDVM_RISCV_X4, SDVM_RISCV_X5, SDVM_RISCV_X6, SDVM_RISCV_X7,
    SDVM_RISCV_X8, SDVM_RISCV_X9, SDVM_RISCV_X10, SDVM_RISCV_X11,
    SDVM_RISCV_X12, SDVM_RISCV_X13, SDVM_RISCV_X14, SDVM_RISCV_X15,
    SDVM_RISCV_X16, SDVM_RISCV_X17,
};
static const uint32_t sdvm_riscv_abi_callTouchedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_riscv_abi_callTouchedIntegerRegisters);

const sdvm_compilerCallingConvention_t sdvm_riscv32_abi_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 4,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 4,
    .integerRegisterCount = sdvm_riscv32_abi_integerPassingRegisterCount,

    .integer32Registers = sdvm_riscv32_abi_integerPassingRegisters,
    .integerRegisters = sdvm_riscv32_abi_integerPassingRegisters,

    .closureRegister = &sdvm_riscv32_T5,
    .closureGCRegister = &sdvm_riscv32_T6,

    .firstInteger32ResultRegister = &sdvm_riscv32_A0,
    .firstIntegerResultRegister = &sdvm_riscv32_A0,
    .secondInteger32ResultRegister = &sdvm_riscv32_A1,
    .secondIntegerResultRegister = &sdvm_riscv32_A1,

    .allocatableIntegerRegisterCount = sdvm_riscv_abi_allocatableIntegerRegisterCount,
    .allocatableIntegerRegisters = sdvm_riscv_abi_allocatableIntegerRegisters,
    
    .callPreservedIntegerRegisterCount = sdvm_riscv_abi_callPreservedIntegerRegisterCount,
    .callPreservedIntegerRegisters = sdvm_riscv_abi_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = sdvm_riscv_abi_callTouchedIntegerRegisterCount,
    .callTouchedIntegerRegisters = sdvm_riscv_abi_callTouchedIntegerRegisters,
};

const sdvm_compilerCallingConvention_t sdvm_riscv64_abi_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 8,
    .integerRegisterCount = sdvm_riscv64_abi_integerPassingRegisterCount,

    .integer32Registers = sdvm_riscv64_abi_integerPassingDwordRegisters,
    .integer64Registers = sdvm_riscv64_abi_integerPassingRegisters,
    .integerRegisters = sdvm_riscv64_abi_integerPassingRegisters,

    .closureRegister = &sdvm_riscv64_T5,
    .closureGCRegister = &sdvm_riscv64_T6,

    .firstInteger32ResultRegister = &sdvm_riscv64_A0W,
    .firstInteger64ResultRegister = &sdvm_riscv64_A0,
    .firstIntegerResultRegister = &sdvm_riscv64_A0,
    .secondInteger32ResultRegister = &sdvm_riscv64_A1W,
    .secondInteger64ResultRegister = &sdvm_riscv64_A1,
    .secondIntegerResultRegister = &sdvm_riscv64_A1,

    .allocatableIntegerRegisterCount = sdvm_riscv_abi_allocatableIntegerRegisterCount,
    .allocatableIntegerRegisters = sdvm_riscv_abi_allocatableIntegerRegisters,
    
    .callPreservedIntegerRegisterCount = sdvm_riscv_abi_callPreservedIntegerRegisterCount,
    .callPreservedIntegerRegisters = sdvm_riscv_abi_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = sdvm_riscv_abi_callTouchedIntegerRegisterCount,
    .callTouchedIntegerRegisters = sdvm_riscv_abi_callTouchedIntegerRegisters,
};

size_t sdvm_compiler_riscv_addInstruction(sdvm_compiler_t *compiler, uint32_t instruction)
{
    size_t offset = compiler->textSection.contents.size;
    sdvm_compiler_addInstructionBytes(compiler, 4, &instruction);
    return offset;
}

void sdvm_compiler_riscv_alignUnreacheableCode(sdvm_compiler_t *compiler)
{
    if(compiler->textSection.alignment < 4)
        compiler->textSection.alignment = 4;
}

#pragma region GeneralPurposeInstructions

uint32_t sdvm_compiler_riscv_32_R_encode(uint32_t opcode, sdvm_riscv_registerIndex_t rd, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint8_t funct7)
{
    return opcode | (rd << 7) | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | (funct7 << 25);
}

uint32_t sdvm_compiler_riscv_32_I_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, int16_t imm)
{
    return opcode | (rd << 7) | (funct3 << 12) | (rs1 << 15) | (imm << 20);
}

uint32_t sdvm_compiler_riscv_32_S_encode(uint8_t opcode, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, int16_t imm)
{
    int32_t immHigh = imm >> 5;
    int32_t immLow = imm & 31;
    return opcode | (immLow << 7) | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | (immHigh << 25);
}

uint32_t sdvm_compiler_riscv_32_B_encodeImmediate(int16_t imm)
{
    int32_t immSign = (imm & (1<<12)) ? 1 : 0;
    int32_t immHigh = (imm >> 5) & 63;
    int32_t immLow = (imm >> 1) & 15;
    int32_t immExtraBit = (imm & (1<<11)) ? 1 : 0;
    return (((immLow<<1) | immExtraBit) << 7) | (immHigh << 25) | (immSign << 31);
}

uint32_t sdvm_compiler_riscv_32_B_encode(uint8_t opcode, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, int16_t imm)
{
    return opcode | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | sdvm_compiler_riscv_32_B_encodeImmediate(imm);
}

uint32_t sdvm_compiler_riscv_32_U_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    int32_t immPart = imm >> 12;
    return opcode | (rd << 7) | (immPart << 12);
}

uint32_t sdvm_compiler_riscv_32_J_encodeImmediate(int32_t imm)
{
    int32_t imm20 = (imm & (1<<20)) ? 1 : 0;
    int32_t imm10_1 = (imm >> 1) & 1023;
    int32_t imm11 = (imm & (1<<11)) ? 1 : 0;
    int32_t imm19_12 = (imm >> 12) & 255;
    return (imm19_12 << 12) | (imm11 << 20) | (imm10_1 << 21) | (imm20 << 31);
}

uint32_t sdvm_compiler_riscv_32_J_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    return opcode | (rd << 7) | sdvm_compiler_riscv_32_J_encodeImmediate(imm);
}

void sdvm_compiler_riscv_lui(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_U_encode(0x37, rd, imm));
}

void sdvm_compiler_riscv_auipc(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_U_encode(0x17, rd, imm));
}

void sdvm_compiler_riscv_jal(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_J_encode(0x6F, rd, imm));
}

void sdvm_compiler_riscv_jal_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_J_encode(0x6F, rd, 0), SdvmCompRelocationRiscVJal, label, 0);
}

void sdvm_compiler_riscv_jalr(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x67, rd, 0, rs, imm));
}

void sdvm_compiler_riscv_beq_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 0, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_bne_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 1, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_blt_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 4, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_bge_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 5, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_bltu_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 6, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_bgeu_label(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, sdvm_compiler_riscv_32_B_encode(0x63, 7, rs1, rs2, 0), SdvmCompRelocationRiscVBranch, label, 0);
}

void sdvm_compiler_riscv_lb(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 0, rs, imm));
}

void sdvm_compiler_riscv_lh(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 1, rs, imm));
}

void sdvm_compiler_riscv_lw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 2, rs, imm));
}

void sdvm_compiler_riscv_lbu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 4, rs, imm));
}

void sdvm_compiler_riscv_lhu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 5, rs, imm));
}

void sdvm_compiler_riscv_sb(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t src, sdvm_riscv_registerIndex_t base, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_S_encode(0x23, 0, base, src, imm));
}

void sdvm_compiler_riscv_sh(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t src, sdvm_riscv_registerIndex_t base, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_S_encode(0x23, 1, base, src, imm));
}

void sdvm_compiler_riscv_sw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t src, sdvm_riscv_registerIndex_t base, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_S_encode(0x23, 2, base, src, imm));
}

void sdvm_compiler_riscv_addi_noOpt(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 0, rs, imm));
}

void sdvm_compiler_riscv_addi(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    if(rd == rs && imm == 0)
        return;

    sdvm_compiler_riscv_addi_noOpt(compiler, rd, rs, imm);
}

void sdvm_compiler_riscv_slti(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 2, rs, imm));
}

void sdvm_compiler_riscv_sltiu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 3, rs, imm));
}

void sdvm_compiler_riscv_xori(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 4, rs, imm));
}

void sdvm_compiler_riscv_ori(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 6, rs, imm));
}

void sdvm_compiler_riscv_andi(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x13, rd, 7, rs, imm));
}

void sdvm_compiler_riscv_slli(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x13, rd, 1, rs, shift, 0));
}

void sdvm_compiler_riscv_srli(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x13, rd, 5, rs, shift, 0));
}

void sdvm_compiler_riscv_srai(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x13, rd, 5, rs, shift, 0x20));
}

void sdvm_compiler_riscv_add(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 0, rs1, rs2, 0));
}

void sdvm_compiler_riscv_sub(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 0, rs1, rs2, 0x20));
}

void sdvm_compiler_riscv_sll(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 1, rs1, rs2, 0));
}

void sdvm_compiler_riscv_slt(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 2, rs1, rs2, 0));
}

void sdvm_compiler_riscv_sltu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 3, rs1, rs2, 0));
}

void sdvm_compiler_riscv_xor(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 4, rs1, rs2, 0));
}

void sdvm_compiler_riscv_srl(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 5, rs1, rs2, 0));
}

void sdvm_compiler_riscv_sra(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 5, rs1, rs2, 0x20));
}

void sdvm_compiler_riscv_or(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 6, rs1, rs2, 0));
}

void sdvm_compiler_riscv_and(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 7, rs1, rs2, 0));
}

void sdvm_compiler_riscv_ebreak(sdvm_compiler_t *compiler)
{
    sdvm_compiler_riscv_addInstruction(compiler, 0x100073);
}

void sdvm_compiler_riscv_mul(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 0, rs1, rs2, 1));
}

void sdvm_compiler_riscv_mulh(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 1, rs1, rs2, 1));
}

void sdvm_compiler_riscv_mulhsu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 2, rs1, rs2, 1));
}

void sdvm_compiler_riscv_mulhu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 3, rs1, rs2, 1));
}

void sdvm_compiler_riscv_div(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 4, rs1, rs2, 1));
}

void sdvm_compiler_riscv_divu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 5, rs1, rs2, 1));
}

void sdvm_compiler_riscv_rem(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 6, rs1, rs2, 1));
}

void sdvm_compiler_riscv_remu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x33, rd, 7, rs1, rs2, 1));
}

#pragma endregion GeneralPurposeInstructions

#pragma region RV64
bool sdvm_compiler_isRiscV32(sdvm_compiler_t *compiler)
{
    return compiler->target->pointerSize == 4;
}

void sdvm_compiler_riscv_lwu(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_lw(compiler, rd, rs, imm);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 6, rs, imm));
}

void sdvm_compiler_riscv_ld(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_lw(compiler, rd, rs, imm);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x03, rd, 3, rs, imm));
}

void sdvm_compiler_riscv_sd(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t src, sdvm_riscv_registerIndex_t base, int16_t imm)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_sw(compiler, src, base, imm);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_S_encode(0x23, 3, base, src, imm));
}

void sdvm_compiler_riscv_slliw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_slli(compiler, rd, rs, shift);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x1B, rd, 1, rs, shift, 0));
}

void sdvm_compiler_riscv_srliw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_srli(compiler, rd, rs, shift);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x1B, rd, 5, rs, shift, 0));
}

void sdvm_compiler_riscv_sraiw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, uint8_t shift)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_srai(compiler, rd, rs, shift);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x1B, rd, 5, rs, shift, 0x20));
}

void sdvm_compiler_riscv_addiw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_addi(compiler, rd, rs, imm);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x1B, rd, 0, rs, imm));
}

void sdvm_compiler_riscv_addw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_add(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 0, rs1, rs2, 0));
}

void sdvm_compiler_riscv_subw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_sub(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 0, rs1, rs2, 0x20));
}

void sdvm_compiler_riscv_sllw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_sllw(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 1, rs1, rs2, 0));
}

void sdvm_compiler_riscv_srlw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_srlw(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 5, rs1, rs2, 0));
}

void sdvm_compiler_riscv_sraw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_sraw(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 5, rs1, rs2, 0x20));
}

void sdvm_compiler_riscv_mulw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_mul(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 0, rs1, rs2, 1));
}

void sdvm_compiler_riscv_divw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_div(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 4, rs1, rs2, 1));
}

void sdvm_compiler_riscv_divuw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_divu(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 5, rs1, rs2, 1));
}

void sdvm_compiler_riscv_remw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_rem(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 6, rs1, rs2, 1));
}

void sdvm_compiler_riscv_remuw(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2)
{
    if(sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_remu(compiler, rd, rs1, rs2);
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_R_encode(0x3B, rd, 7, rs1, rs2, 1));
}

#pragma endregion RV64

#pragma region PseudoInstructions

void sdvm_compiler_riscv_nop(sdvm_compiler_t *compiler)
{
    sdvm_compiler_riscv_addi_noOpt(compiler, SDVM_RISCV_ZERO, SDVM_RISCV_ZERO, 0);
}

void sdvm_compiler_riscv_mv(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs)
{
    if(rd == rs)
        return;
    sdvm_compiler_riscv_addi(compiler, rd, rs, 0);
}

void sdvm_compiler_riscv_ret(sdvm_compiler_t *compiler)
{
    sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_ZERO, SDVM_RISCV_RA, 0);
}

void sdvm_compiler_riscv_la(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerSymbolHandle_t symbolHandle)
{
    if(compiler->target->usesPIC)
    {
        sdvm_compiler_riscv_auipc(compiler, Rd, 0);
        sdvm_compiler_riscv_ld(compiler, Rd, Rd, 0);
    }
    else
    {
        sdvm_compiler_riscv_auipc(compiler, Rd, 0);
        sdvm_compiler_riscv_addi(compiler, Rd, Rd, 0);
    }
}

void sdvm_compiler_riscv_call_plt(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle)
{
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVCallPLT, symbolHandle, 0);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVRelax, 0, 0);
    sdvm_compiler_riscv_auipc(compiler, SDVM_RISCV_RA, 0);
    sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_RA, SDVM_RISCV_RA, 0);
}

void sdvm_compiler_riscv_call_local(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVCallPLT, symbolHandle, addend);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVRelax, 0, 0);
    sdvm_compiler_riscv_auipc(compiler, SDVM_RISCV_RA, 0);
    sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_RA, SDVM_RISCV_RA, 0);
}

void sdvm_compiler_riscv_lla(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    sdvm_compilerSymbolHandle_t relocSymbol = sdvm_compiler_addReferencedInstructionRelocation(compiler, SdvmCompRelocationRiscVRelativeHi20, symbolHandle, addend);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVRelax, 0, 0);
    sdvm_compiler_riscv_auipc(compiler, Rd, 0);

    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVRelativeLo12I, relocSymbol, 0);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRiscVRelax, 0, 0);
    sdvm_compiler_riscv_addi_noOpt(compiler, Rd, Rd, 0);
}

bool sdvm_compiler_riscv_isImm32(int64_t imm64)
{
    return imm64 == (int64_t)(int32_t)imm64;
}

bool sdvm_compiler_riscv_isShiftedConstant(int64_t imm64, int8_t shiftAmount)
{
    return imm64 == ((int64_t)(int32_t)(imm64 >> shiftAmount) << shiftAmount);
}

bool sdvm_compiler_riscv_isSupportedImm64(int64_t imm64)
{
    return sdvm_compiler_riscv_isImm32(imm64)
        || sdvm_compiler_riscv_isImm32(~imm64) 
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 8)
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 16)
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 32)
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 40)
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 48)
        || sdvm_compiler_riscv_isShiftedConstant(imm64, 56);
}

bool sdvm_compiler_riscv_isImm12(int32_t imm)
{
    int32_t imm12 = (imm & (1<<11) - 1) - (imm & (1<<11));
    return imm == imm12;
}

void sdvm_compiler_riscv_li32(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm32)
{
    if(imm32 == 0)
        return sdvm_compiler_riscv_mv(compiler, rd, SDVM_RISCV_ZERO);
    else if(sdvm_compiler_riscv_isImm12(imm32))
        return sdvm_compiler_riscv_addi(compiler, rd, SDVM_RISCV_ZERO, imm32);

    sdvm_compiler_riscv_lui(compiler, rd, imm32);
    sdvm_compiler_riscv_addi(compiler, rd, rd, imm32);
}

void sdvm_compiler_riscv_li32_neg(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm32)
{
    sdvm_compiler_riscv_li32(compiler, rd, ~imm32);
    sdvm_compiler_riscv_xori(compiler, rd, rd, -1);
}

void sdvm_compiler_riscv_li32_shifted(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int32_t imm32, int8_t shift)
{
    sdvm_compiler_riscv_li32(compiler, rd, ~imm32);
    sdvm_compiler_riscv_slli(compiler, rd, rd, shift);
}

void sdvm_compiler_riscv_li64(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, int64_t imm64)
{
    SDVM_ASSERT(sdvm_compiler_riscv_isSupportedImm64(imm64));
    if(sdvm_compiler_riscv_isImm32(imm64))
        return sdvm_compiler_riscv_li32(compiler, rd, imm64);
    else if(sdvm_compiler_riscv_isImm32(~imm64))
        return sdvm_compiler_riscv_li32_neg(compiler, rd, imm64);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 8))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 8);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 16))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 16);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 32))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 32);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 40))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 40);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 48))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 48);
    else if(sdvm_compiler_riscv_isShiftedConstant(imm64, 56))
        return sdvm_compiler_riscv_li32_shifted(compiler, rd, imm64, 56);

    abort();
}

void sdvm_compiler_riscv_sext_b(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    if (sdvm_compiler_isRiscV32(compiler))
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 24);
        sdvm_compiler_riscv_srai(compiler, Rd, Rd, 24);
    }
    else
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 56);
        sdvm_compiler_riscv_srai(compiler, Rd, Rd, 56);
    }
}

void sdvm_compiler_riscv_sext_h(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    if (sdvm_compiler_isRiscV32(compiler))
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 16);
        sdvm_compiler_riscv_srai(compiler, Rd, Rd, 16);
    }
    else
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 48);
        sdvm_compiler_riscv_srai(compiler, Rd, Rd, 48);
    }
}

void sdvm_compiler_riscv_sext_w(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    if (sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_mv(compiler, Rd, Rs);

    sdvm_compiler_riscv_addiw(compiler, Rd, Rs, 0);
}

void sdvm_compiler_riscv_zext_b(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    sdvm_compiler_riscv_andi(compiler, Rd, Rs, 255);
}

void sdvm_compiler_riscv_zext_h(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    if (sdvm_compiler_isRiscV32(compiler))
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 16);
        sdvm_compiler_riscv_srli(compiler, Rd, Rd, 16);
    }
    else
    {
        sdvm_compiler_riscv_slli(compiler, Rd, Rs, 48);
        sdvm_compiler_riscv_srli(compiler, Rd, Rd, 48);
    }
}

void sdvm_compiler_riscv_zext_w(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    if (sdvm_compiler_isRiscV32(compiler))
        return sdvm_compiler_riscv_mv(compiler, Rd, Rs);

    sdvm_compiler_riscv_slli(compiler, Rd, Rs, 32);
    sdvm_compiler_riscv_srli(compiler, Rd, Rd, 32);
}

void sdvm_compiler_riscv_seqz(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    sdvm_compiler_riscv_sltiu(compiler, Rd, Rs, 1);
}

void sdvm_compiler_riscv_snez(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    sdvm_compiler_riscv_sltu(compiler, Rd, SDVM_RISCV_ZERO, Rs);
}

void sdvm_compiler_riscv_sltz(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    sdvm_compiler_riscv_slt(compiler, Rd, Rs, SDVM_RISCV_ZERO);
}

void sdvm_compiler_riscv_sgtz(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs)
{
    sdvm_compiler_riscv_slt(compiler, Rd, SDVM_RISCV_ZERO, Rs);
}

void sdvm_compiler_riscv_seq(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sub(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_seqz(compiler, Rd, Rd);
}

void sdvm_compiler_riscv_seqw(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_subw(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_seqz(compiler, Rd, Rd);
}

void sdvm_compiler_riscv_sneqw(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_subw(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_seqz(compiler, Rd, Rd);
}

void sdvm_compiler_riscv_sneq(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sub(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_snez(compiler, Rd, Rd);
}

void sdvm_compiler_riscv_sgt(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_slt(compiler, Rd, Rs2, Rs1);
}

void sdvm_compiler_riscv_sle(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sgt(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_xori(compiler, Rd, Rd, 1);
}

void sdvm_compiler_riscv_sge(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_slt(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_xori(compiler, Rd, Rd, 1);
}

void sdvm_compiler_riscv_sgtu(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sltu(compiler, Rd, Rs2, Rs1);
}

void sdvm_compiler_riscv_sleu(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sgtu(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_xori(compiler, Rd, Rd, 1);
}

void sdvm_compiler_riscv_sgeu(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rs1, sdvm_compilerRegisterValue_t Rs2)
{
    sdvm_compiler_riscv_sltu(compiler, Rd, Rs1, Rs2);
    sdvm_compiler_riscv_xori(compiler, Rd, Rd, 1);
}

#pragma endregion

static sdvm_compilerInstructionPatternTable_t sdvm_riscv_instructionPatternTable = {
};

sdvm_compilerLocation_t sdvm_compilerLocation_riscv_immediateS32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateS32(value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv_immediateU32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateU32(value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv_immediateS64(sdvm_compiler_t *compiler, int64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_riscv_isSupportedImm64(value))
        return sdvm_compilerLocation_immediateS64(value);
    else
        return sdvm_compilerLocation_constSectionS64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv_immediateU64(sdvm_compiler_t *compiler, uint64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_riscv_isSupportedImm64(value))
        return sdvm_compilerLocation_immediateU64(value);
    else
        return sdvm_compilerLocation_constSectionU64(compiler, value);
}

void sdvm_compiler_riscv_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    uint32_t pointerSize = state->compiler->pointerSize;

    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_riscv_immediateS32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstUInt32:
            instruction->location = sdvm_compilerLocation_riscv_immediateU32(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64SExt:
        case SdvmConstUInt64SExt:
            instruction->location = sdvm_compilerLocation_riscv_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
        case SdvmConstUInt64ZExt:
            instruction->location = sdvm_compilerLocation_riscv_immediateU64(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstPointerSExt:
            if(pointerSize == 8)
                instruction->location = sdvm_compilerLocation_riscv_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            else
                instruction->location = sdvm_compilerLocation_riscv_immediateS32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstPointerZExt:
            if(pointerSize == 8)
                instruction->location = sdvm_compilerLocation_riscv_immediateU64(state->compiler, instruction->decoding.constant.signedPayload);
            else
                instruction->location = sdvm_compilerLocation_riscv_immediateU32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        default:
            sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
        }

        return;
    }

    switch (instruction->decoding.opcode)
    {
    case SdvmInstInt32Add:
    case SdvmInstInt32Sub:
    case SdvmInstInt32Mul:
    case SdvmInstInt32Div:
    case SdvmInstInt32UDiv:
    case SdvmInstInt32And:
    case SdvmInstInt32Or:
    case SdvmInstInt32Xor:
    case SdvmInstInt32Lsl:
    case SdvmInstInt32Lsr:
    case SdvmInstInt32Asr:
    case SdvmInstInt32Min:
    case SdvmInstInt32Max:
    case SdvmInstUInt32Add:
    case SdvmInstUInt32Sub:
    case SdvmInstUInt32Mul:
    case SdvmInstUInt32Div:
    case SdvmInstUInt32UDiv:
    case SdvmInstUInt32And:
    case SdvmInstUInt32Or:
    case SdvmInstUInt32Xor:
    case SdvmInstUInt32Lsl:
    case SdvmInstUInt32Lsr:
    case SdvmInstUInt32Asr:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstInt64Add:
    case SdvmInstInt64Sub:
    case SdvmInstInt64Div:
    case SdvmInstInt64UDiv:
    case SdvmInstInt64Lsl:
    case SdvmInstInt64Lsr:
    case SdvmInstInt64Asr:
    case SdvmInstUInt64Add:
    case SdvmInstUInt64Sub:
    case SdvmInstUInt64Div:
    case SdvmInstUInt64Lsl:
    case SdvmInstUInt64Lsr:
    case SdvmInstUInt64Asr:
    case SdvmInstUInt64UDiv:
        if(pointerSize == 8)
        {
            instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
            instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
            instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
            instruction->allowArg0DestinationShare = true;
            instruction->allowArg1DestinationShare = true;
        }
        else
        {
            // Convert into a function call.
            instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(sdvm_riscv32_A0, sdvm_riscv32_A1);
            instruction->arg1Location = sdvm_compilerLocation_specificRegisterPair(sdvm_riscv32_A2, sdvm_riscv32_A3);
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(sdvm_riscv32_A0, sdvm_riscv32_A1);
        }
        return;

    case SdvmInstInt64Mul:
    case SdvmInstUInt64Mul:
        if(pointerSize == 8)
        {
            instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
            instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
            instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
            instruction->allowArg0DestinationShare = true;
            instruction->allowArg1DestinationShare = true;
        }
        else
        {
            instruction->arg0Location = sdvm_compilerLocation_integerRegisterPair(4, 4);
            instruction->arg1Location = sdvm_compilerLocation_integerRegisterPair(4, 4);
            instruction->destinationLocation = sdvm_compilerLocation_integerRegisterPair(4, 4);
        }
        return;

    case SdvmInstInt64And:
    case SdvmInstInt64Or:
    case SdvmInstInt64Xor:
    case SdvmInstUInt64And:
    case SdvmInstUInt64Or:
    case SdvmInstUInt64Xor:
        if(pointerSize == 8)
        {
            instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
            instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
            instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
            instruction->allowArg0DestinationShare = true;
            instruction->allowArg1DestinationShare = true;
        }
        else
        {
            instruction->arg0Location = sdvm_compilerLocation_integerRegisterPair(4, 4);
            instruction->arg1Location = sdvm_compilerLocation_integerRegisterPair(4, 4);
            instruction->destinationLocation = sdvm_compilerLocation_integerRegisterPair(4, 4);
            instruction->allowArg0DestinationShare = true;
            instruction->allowArg1DestinationShare = true;
        }
        return;

    case SdvmInstFloat32Add:
    case SdvmInstFloat32Sub:
    case SdvmInstFloat32Mul:
    case SdvmInstFloat32Div:
    case SdvmInstFloat32Min:
    case SdvmInstFloat32Max:
        instruction->arg0Location = sdvm_compilerLocation_floatRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_floatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_floatRegister(4);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstFloat32Sqrt:
    case SdvmInstFloat32Floor:
    case SdvmInstFloat32Ceil:
    case SdvmInstFloat32Round:
    case SdvmInstFloat32Truncate:
        instruction->arg0Location = sdvm_compilerLocation_floatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_floatRegister(4);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstFloat64Add:
    case SdvmInstFloat64Sub:
    case SdvmInstFloat64Mul:
    case SdvmInstFloat64Div:
    case SdvmInstFloat64Min:
    case SdvmInstFloat64Max:
        instruction->arg0Location = sdvm_compilerLocation_floatRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_floatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_floatRegister(8);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstFloat64Sqrt:
    case SdvmInstFloat64Floor:
    case SdvmInstFloat64Ceil:
    case SdvmInstFloat64Round:
    case SdvmInstFloat64Truncate:
        instruction->arg0Location = sdvm_compilerLocation_floatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_floatRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    default:
        return sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
    }
}

void sdvm_compiler_riscv_computeFunctionLocationConstraints(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerTarget_t *target = state->compiler->target;
    state->callingConvention = target->defaultCC;
    state->currentCallCallingConvention = target->defaultCC;

    sdvm_functionCompilationState_computeLabelLocations(state);

    uint32_t i = 0;
    while(i < state->instructionCount)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        if(instruction->pattern)
        {
            instruction->pattern->constraints(state, instruction->pattern->size, instruction);
            i += instruction->pattern->size;
        }
        else
        {
            sdvm_compiler_riscv_computeInstructionLocationConstraints(state, instruction);
            ++i;
        }
    }
}

void sdvm_compiler_riscv_allocateFunctionRegisters(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    
    sdvm_linearScanRegisterAllocatorFile_t integerRegisterFile = {
        .allocatableRegisterCount = convention->allocatableIntegerRegisterCount,
        .allocatableRegisters = convention->allocatableIntegerRegisters
    };

    sdvm_linearScanRegisterAllocatorFile_t vectorRegisterFile = {
        .allocatableRegisterCount = convention->allocatableVectorRegisterCount,
        .allocatableRegisters = convention->allocatableVectorRegisters
    };

    sdvm_linearScanRegisterAllocator_t registerAllocator = {
        .compiler = state->compiler,
        .integerRegisterFile = &integerRegisterFile,
        .floatRegisterFile = &vectorRegisterFile,
        .vectorFloatRegisterFile = &vectorRegisterFile,
        .vectorIntegerRegisterFile = &vectorRegisterFile,
    };

    sdvm_compiler_allocateFunctionRegisters(state, &registerAllocator);
}

void sdvm_compiler_riscv_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_allocateFunctionSpillLocations(state);
}

void sdvm_compiler_riscv_computeFunctionStackLayout(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;

    state->requiresStackFrame = state->hasCallout
        || !sdvm_registerSet_isEmpty(&state->usedCallPreservedIntegerRegisterSet)
        || !sdvm_registerSet_isEmpty(&state->usedCallPreservedVectorRegisterSet)
        || state->temporarySegment.size > 0
        || state->calloutStackSegment.size > 0;

    uint32_t pointerSize = state->compiler->pointerSize;
    state->prologueStackSegment.size = 0;
    state->prologueStackSegment.alignment = 16;

    if(state->requiresStackFrame)
    {
        // Frame pointer and return address register.
        state->prologueStackSegment.size += pointerSize*2;
    }

    if(state->requiresStackFrame)
    {
        // Preserved integer registers.
        for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
        {
            if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, convention->callPreservedIntegerRegisters[i]))
                state->prologueStackSegment.size += pointerSize;
        }
    }

    sdvm_compiler_computeStackSegmentLayouts(state);

    SDVM_ASSERT(!state->requiresStackFramePointer);
    state->stackFrameRegister = SDVM_RISCV_SP;
    state->stackFramePointerAnchorOffset = state->calloutStackSegment.endOffset;

    sdvm_compiler_computeStackFrameOffsets(state);
}

void sdvm_compiler_riscv_ensureCIE(sdvm_moduleCompilationState_t *state)
{
    if(state->hasEmittedCIE)
        return;

    sdvm_dwarf_cfi_builder_t *cfi = &state->cfi;
    uint8_t pointerSize = state->compiler->target->pointerSize;

    sdvm_dwarf_cie_t ehCie = {0};
    ehCie.codeAlignmentFactor = 2;
    ehCie.dataAlignmentFactor = -pointerSize;
    ehCie.pointerSize = pointerSize;
    ehCie.returnAddressRegister = DW_RISCV_REG_RA;
    cfi->section = &state->compiler->ehFrameSection;
    cfi->pointerSize = pointerSize;
    cfi->initialStackFrameSize = 0;
    cfi->stackPointerRegister = DW_RISCV_REG_SP;

    sdvm_dwarf_cfi_beginCIE(cfi, &ehCie);
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, DW_RISCV_REG_SP, 0);
    sdvm_dwarf_cfi_endCIE(cfi);
    state->hasEmittedCIE = true;
}

void sdvm_compiler_riscv_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    uint32_t pointerSize = state->compiler->pointerSize;

    sdvm_compiler_riscv_ensureCIE(state->moduleState);
    sdvm_dwarf_cfi_beginFDE(cfi, &compiler->textSection, sdvm_compiler_getCurrentPC(compiler));

    if(state->debugFunctionTableEntry)
        sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, SdvmDebugLineInfoKindBeginPrologue, state->debugFunctionTableEntry->declarationLineInfo);

    if(!state->requiresStackFrame)
    {
        sdvm_dwarf_cfi_endPrologue(cfi);
        return;
    }

    int32_t stackSubtractionAmount = state->calloutStackSegment.endOffset;
    SDVM_ASSERT(stackSubtractionAmount >= (int32_t)pointerSize*2);
    sdvm_compiler_riscv_addi(compiler, SDVM_RISCV_SP, SDVM_RISCV_SP, -stackSubtractionAmount);
    sdvm_dwarf_cfi_stackSizeAdvance(cfi, sdvm_compiler_getCurrentPC(compiler), stackSubtractionAmount);

    sdvm_compiler_riscv_sd(compiler, SDVM_RISCV_RA, SDVM_RISCV_SP, stackSubtractionAmount - pointerSize);

    sdvm_compiler_riscv_sd(compiler, SDVM_RISCV_FP, SDVM_RISCV_SP, stackSubtractionAmount - pointerSize*2);

    sdvm_compiler_riscv_addi(compiler, SDVM_RISCV_FP, SDVM_RISCV_SP, stackSubtractionAmount);

    sdvm_dwarf_cfi_endPrologue(cfi);
}

void sdvm_compiler_riscv_emitMemoryToMemoryFixedSizedAlignedMove(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t sourcePointer, int32_t sourcePointerOffset, sdvm_riscv_registerIndex_t destinationPointer, int32_t destinationPointerOffset, size_t copySize, const sdvm_compilerScratchMoveRegisters_t *scratchMoveRegister)
{
    abort();
}

void sdvm_compiler_riscv_emitMoveFromLocationIntoIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        return sdvm_compiler_riscv_mv(compiler, reg->value, SDVM_RISCV_ZERO);
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
        return sdvm_compiler_riscv_li32(compiler, reg->value, sourceLocation->immediateS32);
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
        return sdvm_compiler_riscv_li64(compiler, reg->value, sourceLocation->immediateS64);
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        return sdvm_compiler_riscv_mv(compiler, reg->value, sourceLocation->firstRegister.value);
    case SdvmCompLocationStack:
    case SdvmCompLocationStackPair:
        switch(reg->size)
        {
        case 1:
            if(sourceLocation->isSigned)
                return sdvm_compiler_riscv_lb(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_riscv_lbu(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 2:
            if(sourceLocation->isSigned)
                return sdvm_compiler_riscv_lh(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_riscv_lhu(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 4:
            if(sourceLocation->isSigned)
                return sdvm_compiler_riscv_lw(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_riscv_lwu(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 8:
            return sdvm_compiler_riscv_ld(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        default: return abort();
        }
    case SdvmCompLocationLocalSymbolValue:
        return sdvm_compiler_riscv_lla(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
    default: return abort();
    }
}

void sdvm_compiler_riscv_emitMoveFromLocationIntoFloatRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    default: return abort();
    }
}

void sdvm_compiler_riscv_emitMoveFromLocationIntoRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(reg->kind)
    {
    case SdvmCompRegisterKindInteger:
        return sdvm_compiler_riscv_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindFloat:
        return sdvm_compiler_riscv_emitMoveFromLocationIntoFloatRegister(compiler, sourceLocation, reg);
    default: abort();
    }
}

void sdvm_compiler_riscv_emitMoveFromRegisterIntoStackLocation(sdvm_compiler_t *compiler, const sdvm_compilerRegister_t *sourceRegister, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        switch(sourceRegister->size)
        {
        case 1: return sdvm_compiler_riscv_sb(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 2: return sdvm_compiler_riscv_sh(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 4: return sdvm_compiler_riscv_sw(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 8: return sdvm_compiler_riscv_sd(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        default:
            return abort();
        }
    default:
        return abort();
    }
}

void sdvm_compiler_riscv_emitMoveFromLocationIntoStack(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
        return sdvm_compiler_riscv_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);
    case SdvmCompLocationRegisterPair:
        {
            sdvm_compiler_riscv_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);

            sdvm_compilerStackLocation_t nextLocation = *stackLocation;
            nextLocation.segmentOffset += sourceLocation->firstRegister.size;
            nextLocation.framePointerOffset += sourceLocation->firstRegister.size;

            return sdvm_compiler_riscv_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->secondRegister, &nextLocation);
        }
    case SdvmCompLocationStack:
        SDVM_ASSERT(destinationLocation->scratchMoveRegister.isValid);
        return sdvm_compiler_riscv_emitMemoryToMemoryFixedSizedAlignedMove(compiler,
            sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset,
            destinationLocation->firstStackLocation.framePointerRegister, destinationLocation->firstStackLocation.framePointerOffset,
            sourceLocation->firstStackLocation.size <= destinationLocation->firstStackLocation.size ? sourceLocation->firstStackLocation.size : destinationLocation->firstStackLocation.size,
            &destinationLocation->scratchMoveRegister);
    default: return abort();
    }
}

void sdvm_compiler_riscv_emitMoveFromLocationInto(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation)
{
    switch(destinationLocation->kind)
    {
    case SdvmCompLocationNull:
        // Ignored.
        return;
    case SdvmCompLocationRegister:
        return sdvm_compiler_riscv_emitMoveFromLocationIntoRegister(compiler, sourceLocation, &destinationLocation->firstRegister);
    case SdvmCompLocationRegisterPair:
        // TODO:
        return abort();
    case SdvmCompLocationStack:
        return sdvm_compiler_riscv_emitMoveFromLocationIntoStack(compiler, sourceLocation, destinationLocation, &destinationLocation->firstStackLocation);
    case SdvmCompLocationStackPair:
        return abort();
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateLabel:
    case SdvmCompLocationConstantSection:
    case SdvmCompLocationLocalSymbolValue:
    case SdvmCompLocationGlobalSymbolValue:
    case SdvmCompLocationStackAddress:
        return;
    default:
        return abort();
    }
}

bool sdvm_compiler_riscv_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_compiler_t *compiler = state->compiler;

    sdvm_compilerLocation_t *dest = &instruction->destinationLocation;
    sdvm_compilerLocation_t *arg0 = &instruction->arg0Location;
    sdvm_compilerLocation_t *arg1 = &instruction->arg1Location;

    uint32_t pointerSize = compiler->target->pointerSize;

    switch(instruction->decoding.opcode)
    {
    // Local only allocations. Handled by the register allocator.
    case SdvmInstAllocateLocal:
    case SdvmInstAllocateGCNoEscape:
        return true;

    // Argument instructions are handled by the register allocator.
    case SdvmInstBeginArguments:
    case SdvmInstArgInt8:
    case SdvmInstArgInt16:
    case SdvmInstArgInt32:
    case SdvmInstArgInt64:
    case SdvmInstArgUInt8:
    case SdvmInstArgUInt16:
    case SdvmInstArgUInt32:
    case SdvmInstArgUInt64:
    case SdvmInstArgPointer:
    case SdvmInstArgProcedureHandle:
    case SdvmInstArgGCPointer:
    case SdvmInstArgFloat32:
    case SdvmInstArgFloat32x2:
    case SdvmInstArgFloat32x4:
    case SdvmInstArgFloat64:
    case SdvmInstArgFloat64x2:
    case SdvmInstArgFloat64x4:
    case SdvmInstArgInt32x2:
    case SdvmInstArgInt32x4:
    case SdvmInstArgUInt32x2:
    case SdvmInstArgUInt32x4:

    case SdvmInstBeginCall:
    case SdvmInstCallArgInt8:
    case SdvmInstCallArgInt16:
    case SdvmInstCallArgInt32:
    case SdvmInstCallArgInt64:
    case SdvmInstCallArgUInt8:
    case SdvmInstCallArgUInt16:
    case SdvmInstCallArgUInt32:
    case SdvmInstCallArgUInt64:
    case SdvmInstCallArgPointer:
    case SdvmInstCallArgProcedureHandle:
    case SdvmInstCallArgGCPointer:
    case SdvmInstCallArgFloat32:
    case SdvmInstCallArgFloat32x2:
    case SdvmInstCallArgFloat32x4:
    case SdvmInstCallArgFloat64:
    case SdvmInstCallArgFloat64x2:
    case SdvmInstCallArgFloat64x4:
    case SdvmInstCallArgInt32x2:
    case SdvmInstCallArgInt32x4:
    case SdvmInstCallArgUInt32x2:
    case SdvmInstCallArgUInt32x4:
        return true;

    // Return instruction differences are handled by the register allocator.
    case SdvmInstReturnVoid:
    case SdvmInstReturnInt8:
    case SdvmInstReturnInt16:
    case SdvmInstReturnInt32:
    case SdvmInstReturnInt64:
    case SdvmInstReturnPointer:
    case SdvmInstReturnProcedureHandle:
    case SdvmInstReturnGCPointer:
    case SdvmInstReturnFloat32:
    case SdvmInstReturnFloat64:
    case SdvmInstReturnFloat32x2:
    case SdvmInstReturnFloat32x4:
    case SdvmInstReturnFloat64x2:
    case SdvmInstReturnFloat64x4:
    case SdvmInstReturnInt32x2:
    case SdvmInstReturnInt32x4:
    case SdvmInstReturnUInt32x2:
    case SdvmInstReturnUInt32x4:
        sdvm_compiler_riscv_emitFunctionEpilogue(state);
        sdvm_compiler_riscv_ret(compiler);
        return false;

    // Call instruction differences are handled by the register allocator.
    case SdvmInstCallVoid:
    case SdvmInstCallInt8:
    case SdvmInstCallInt16:
    case SdvmInstCallInt32:
    case SdvmInstCallInt64:
    case SdvmInstCallPointer:
    case SdvmInstCallProcedureHandle:
    case SdvmInstCallGCPointer:
    case SdvmInstCallFloat32:
    case SdvmInstCallFloat64:
        if(arg0->kind == SdvmCompLocationGlobalSymbolValue)
        {
            SDVM_ASSERT(arg0->symbolOffset == 0);
            sdvm_compiler_riscv_call_plt(compiler, arg0->symbolHandle);
        }
        else if(arg0->kind == SdvmCompLocationLocalSymbolValue)
        {
            sdvm_compiler_riscv_call_local(compiler, arg0->symbolHandle, arg0->symbolOffset);
        }
        else
        {
            sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_RA, arg0->firstRegister.value, 0);
        }
        return true;

    // Call instruction differences are handled by the register allocator.
    case SdvmInstCallClosureVoid:
    case SdvmInstCallClosureInt8:
    case SdvmInstCallClosureInt16:
    case SdvmInstCallClosureInt32:
    case SdvmInstCallClosureInt64:
    case SdvmInstCallClosurePointer:
    case SdvmInstCallClosureProcedureHandle:
    case SdvmInstCallClosureGCPointer:
    case SdvmInstCallClosureFloat32:
    case SdvmInstCallClosureFloat64:
        sdvm_compiler_riscv_ld(compiler, SDVM_RISCV_RA, arg0->firstRegister.value, 0);
        sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_RA, SDVM_RISCV_RA, 0);
        return true;

    case SdvmInstLoadInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lb(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lb(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lbu(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lbu(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lh(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lh(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lhu(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lb(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lwu(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lwu(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_lw(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_lw(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt64:
    case SdvmInstLoadUInt64:
        if(pointerSize == 8)
        {
            if(arg0->kind == SdvmCompLocationStackAddress)
                sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
            else
                sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        }
        else
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            if(arg0->kind == SdvmCompLocationStackAddress)
            {
                sdvm_compiler_riscv_lw(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
                sdvm_compiler_riscv_lw(compiler, dest->secondRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + 4);
            }
            else
            {
                sdvm_compiler_riscv_lw(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
                sdvm_compiler_riscv_lw(compiler, dest->secondRegister.value, arg0->firstRegister.value, 4);
            }
        }
        return true;
    case SdvmInstLoadPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadGCPointer:
        SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
            sdvm_compiler_riscv_ld(compiler, dest->secondRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + pointerSize);
        }
        else
        {
            sdvm_compiler_riscv_ld(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
            sdvm_compiler_riscv_ld(compiler, dest->secondRegister.value, arg0->firstRegister.value, pointerSize);
        }
        return true;

    case SdvmInstStoreInt8:
    case SdvmInstStoreUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_sb(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_sb(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt16:
    case SdvmInstStoreUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_sh(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_sh(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt32:
    case SdvmInstStoreUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_sw(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_sw(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt64:
    case SdvmInstStoreUInt64:
        if(pointerSize == 8)
        {
            if(arg0->kind == SdvmCompLocationStackAddress)
                sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
            else
                sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        }
        else
        {
            SDVM_ASSERT(arg1->kind == SdvmCompLocationRegisterPair);
            if(arg0->kind == SdvmCompLocationStackAddress)
            {
                sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
                sdvm_compiler_riscv_sd(compiler, arg1->secondRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + pointerSize);
            }
            else
            {
                sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
                sdvm_compiler_riscv_sd(compiler, arg1->secondRegister.value, arg0->firstRegister.value, pointerSize);
            }
        }
        return true;

    case SdvmInstStorePointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_riscv_sd(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreGCPointer:
        SDVM_ASSERT(arg1->kind == SdvmCompLocationRegisterPair);
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_riscv_sd(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
            sdvm_compiler_riscv_sd(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + pointerSize, arg1->secondRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_sd(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
            sdvm_compiler_riscv_sd(compiler, arg0->firstRegister.value, pointerSize, arg1->secondRegister.value);
        }
        return true;

    case SdvmInstJump:
        sdvm_compiler_riscv_jal_label(compiler, SDVM_RISCV_ZERO, arg0->immediateLabel);
        return true;
    case SdvmInstJumpIfTrue:
        sdvm_compiler_riscv_bne_label(compiler, arg0->firstRegister.value, SDVM_RISCV_ZERO, arg1->immediateLabel);
        return true;
    case SdvmInstJumpIfFalse:
        sdvm_compiler_riscv_beq_label(compiler, arg0->firstRegister.value, SDVM_RISCV_ZERO, arg1->immediateLabel);
        return true;

    case SdvmInstInt32Add:
    case SdvmInstUInt32Add:
        sdvm_compiler_riscv_addw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Sub:
    case SdvmInstUInt32Sub:
        sdvm_compiler_riscv_subw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Mul:
    case SdvmInstUInt32Mul:
        sdvm_compiler_riscv_mulw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Div:
    case SdvmInstUInt32Div:
        sdvm_compiler_riscv_divw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32UDiv:
    case SdvmInstUInt32UDiv:
        sdvm_compiler_riscv_divuw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Rem:
    case SdvmInstUInt32Rem:
        sdvm_compiler_riscv_remw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32URem:
    case SdvmInstUInt32URem:
        sdvm_compiler_riscv_remuw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt32And:
    case SdvmInstUInt32And:
        sdvm_compiler_riscv_and(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Or:
    case SdvmInstUInt32Or:
        sdvm_compiler_riscv_or(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Xor:
    case SdvmInstUInt32Xor:
        sdvm_compiler_riscv_xor(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Lsl:
    case SdvmInstUInt32Lsl:
        sdvm_compiler_riscv_sllw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Lsr:
    case SdvmInstUInt32Lsr:
        sdvm_compiler_riscv_srlw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Asr:
    case SdvmInstUInt32Asr:
        sdvm_compiler_riscv_sraw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt64Add:
    case SdvmInstUInt64Add:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_add(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            SDVM_ASSERT(false && "TODO: SdvmInstUInt64Add");
        }
        return true;
    case SdvmInstInt64Sub:
    case SdvmInstUInt64Sub:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_sub(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            SDVM_ASSERT(false && "TODO: SdvmInstUInt64Sub");
        }
        return true;
    case SdvmInstInt64Mul:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_mul(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_mul(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->secondRegister.value);
            sdvm_compiler_riscv_mulh(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_add(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_mul(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        return true;
    case SdvmInstUInt64Mul:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_mul(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_mul(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->secondRegister.value);
            sdvm_compiler_riscv_mulhu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_add(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_mul(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        return true;
    case SdvmInstInt64Div:
    case SdvmInstUInt64Div:
        if(pointerSize == 8)
            sdvm_compiler_riscv_div(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64Div/SdvmInstUInt64Div");
        return true;
    case SdvmInstInt64UDiv:
    case SdvmInstUInt64UDiv:
        if(pointerSize == 8)
            sdvm_compiler_riscv_divu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64UDiv/SdvmInstUInt64Div");
        return true;
    case SdvmInstInt64Rem:
    case SdvmInstUInt64Rem:
        if(pointerSize == 8)
            sdvm_compiler_riscv_rem(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64Rem/SdvmInstUInt64Div");
        return true;
    case SdvmInstInt64URem:
    case SdvmInstUInt64URem:
        if(pointerSize == 8)
            sdvm_compiler_riscv_remu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64URem/SdvmInstUInt64URem");
        return true;

    case SdvmInstInt64And:
    case SdvmInstUInt64And:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_and(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_and(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_and(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->secondRegister.value);
        }
        return true;
    case SdvmInstInt64Or:
    case SdvmInstUInt64Or:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_or(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_or(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_or(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->secondRegister.value);
        }
        return true;
    case SdvmInstInt64Xor:
    case SdvmInstUInt64Xor:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_xor(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        }
        else
        {
            sdvm_compiler_riscv_xor(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
            sdvm_compiler_riscv_xor(compiler, dest->secondRegister.value, arg0->secondRegister.value, arg1->secondRegister.value);
        }
        return true;
    case SdvmInstInt64Lsl:
    case SdvmInstUInt64Lsl:
        if(pointerSize == 8)
            sdvm_compiler_riscv_sll(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64Lsl/SdvmInstUInt64Lsl");
        return true;
    case SdvmInstInt64Lsr:
    case SdvmInstUInt64Lsr:
        if(pointerSize == 8)
            sdvm_compiler_riscv_srl(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64Lsr/SdvmInstUInt64Lsr");
        return true;
    case SdvmInstInt64Asr:
    case SdvmInstUInt64Asr:
        if(pointerSize == 8)
            sdvm_compiler_riscv_sra(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        else
            SDVM_ASSERT(false && "TODO: SdvmInstInt64Asr/SdvmInstUInt64Asr");
        return true;

    case SdvmInstPointerAddOffsetUInt32:
        sdvm_compiler_riscv_zext_w(compiler, arg1->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_riscv_add(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstPointerAddOffsetInt32:
    case SdvmInstPointerAddOffsetInt64:
    case SdvmInstPointerAddOffsetUInt64:
        sdvm_compiler_riscv_add(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt8Equals:
    case SdvmInstInt16Equals:
    case SdvmInstInt32Equals:
    case SdvmInstUInt8Equals:
    case SdvmInstUInt16Equals:
    case SdvmInstUInt32Equals:
        sdvm_compiler_riscv_seqw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8NotEquals:
    case SdvmInstInt16NotEquals:
    case SdvmInstInt32NotEquals:
    case SdvmInstUInt8NotEquals:
    case SdvmInstUInt16NotEquals:
    case SdvmInstUInt32NotEquals:
        sdvm_compiler_riscv_sneqw(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8LessThan:
    case SdvmInstInt16LessThan:
    case SdvmInstInt32LessThan:
        sdvm_compiler_riscv_slt(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8LessThan:
    case SdvmInstUInt16LessThan:
    case SdvmInstUInt32LessThan:
        sdvm_compiler_riscv_sltu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8LessOrEquals:
    case SdvmInstInt16LessOrEquals:
    case SdvmInstInt32LessOrEquals:
        sdvm_compiler_riscv_sle(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8LessOrEquals:
    case SdvmInstUInt16LessOrEquals:
    case SdvmInstUInt32LessOrEquals:
        sdvm_compiler_riscv_sleu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8GreaterThan:
    case SdvmInstInt16GreaterThan:
    case SdvmInstInt32GreaterThan:
        sdvm_compiler_riscv_sgt(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8GreaterThan:
    case SdvmInstUInt16GreaterThan:
    case SdvmInstUInt32GreaterThan:
        sdvm_compiler_riscv_sgtu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8GreaterOrEquals:
    case SdvmInstInt16GreaterOrEquals:
    case SdvmInstInt32GreaterOrEquals:
        sdvm_compiler_riscv_sge(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8GreaterOrEquals:
    case SdvmInstUInt16GreaterOrEquals:
    case SdvmInstUInt32GreaterOrEquals:
        sdvm_compiler_riscv_sgeu(compiler, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt8_Bitcast_UInt8:
    case SdvmInstInt16_Bitcast_UInt16:
    case SdvmInstInt32_Bitcast_UInt32:
    case SdvmInstInt64_Bitcast_UInt64:
    case SdvmInstUInt8_Bitcast_Int8:
    case SdvmInstUInt16_Bitcast_Int16:
    case SdvmInstUInt32_Bitcast_Int32:
    case SdvmInstUInt64_Bitcast_Int64:
        sdvm_compiler_riscv_mv(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_Int8:
    case SdvmInstUInt64_Truncate_Int8:
    case SdvmInstInt32_Truncate_Int8:
    case SdvmInstUInt32_Truncate_Int8:
    case SdvmInstInt16_Truncate_Int8:
    case SdvmInstUInt16_Truncate_Int8:
        sdvm_compiler_riscv_sext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_Int16:
    case SdvmInstUInt64_Truncate_Int16:
    case SdvmInstInt32_Truncate_Int16:
    case SdvmInstUInt32_Truncate_Int16:
        sdvm_compiler_riscv_sext_h(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_Int32:
    case SdvmInstUInt64_Truncate_Int32:
        sdvm_compiler_riscv_sext_w(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_UInt8:
    case SdvmInstUInt64_Truncate_UInt8:
    case SdvmInstInt32_Truncate_UInt8:
    case SdvmInstUInt32_Truncate_UInt8:
    case SdvmInstInt16_Truncate_UInt8:
    case SdvmInstUInt16_Truncate_UInt8:
        sdvm_compiler_riscv_zext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_UInt16:
    case SdvmInstUInt64_Truncate_UInt16:
    case SdvmInstInt32_Truncate_UInt16:
    case SdvmInstUInt32_Truncate_UInt16:
        sdvm_compiler_riscv_zext_h(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt64_Truncate_UInt32:
    case SdvmInstUInt64_Truncate_UInt32:
        sdvm_compiler_riscv_zext_w(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
        
    case SdvmInstInt8_SignExtend_Int16:
    case SdvmInstInt8_SignExtend_Int32:
        sdvm_compiler_riscv_sext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt8_SignExtend_Int64:
        sdvm_compiler_riscv_sext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        if(pointerSize == 4)
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_srai(compiler, dest->secondRegister.value, dest->firstRegister.value, 31);
        }
        return true;
    case SdvmInstInt16_SignExtend_Int32:
        sdvm_compiler_riscv_sext_h(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt16_SignExtend_Int64:
        sdvm_compiler_riscv_sext_h(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        if(pointerSize == 4)
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_srai(compiler, dest->secondRegister.value, dest->firstRegister.value, 31);
        }
        return true;
    case SdvmInstInt32_SignExtend_Int64:
        sdvm_compiler_riscv_sext_w(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        if(pointerSize == 4)
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_srai(compiler, dest->secondRegister.value, dest->firstRegister.value, 31);
        }
        return true;

    case SdvmInstInt8_ZeroExtend_UInt16:
    case SdvmInstInt8_ZeroExtend_UInt32:
    case SdvmInstUInt8_ZeroExtend_Int16:
    case SdvmInstUInt8_ZeroExtend_Int32:
    case SdvmInstUInt8_ZeroExtend_UInt16:
    case SdvmInstUInt8_ZeroExtend_UInt32:
        sdvm_compiler_riscv_zext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt8_ZeroExtend_UInt64:
    case SdvmInstUInt8_ZeroExtend_Int64:
    case SdvmInstUInt8_ZeroExtend_UInt64:
        sdvm_compiler_riscv_zext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        if(pointerSize == 4)
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_mv(compiler, dest->secondRegister.value, SDVM_RISCV_ZERO);
        }
        return true;
    case SdvmInstInt16_ZeroExtend_UInt32:
    case SdvmInstUInt16_ZeroExtend_Int32:
    case SdvmInstUInt16_ZeroExtend_UInt32:
        sdvm_compiler_riscv_zext_h(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt16_ZeroExtend_UInt64:
    case SdvmInstUInt16_ZeroExtend_Int64:
    case SdvmInstUInt16_ZeroExtend_UInt64:
        sdvm_compiler_riscv_zext_b(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        if(pointerSize == 8)
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_mv(compiler, dest->secondRegister.value, SDVM_RISCV_ZERO);
        }
        return true;

    case SdvmInstInt32_ZeroExtend_UInt64:
    case SdvmInstUInt32_ZeroExtend_Int64:
    case SdvmInstUInt32_ZeroExtend_UInt64:
        if(pointerSize == 8)
        {
            sdvm_compiler_riscv_zext_w(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        }
        else
        {
            SDVM_ASSERT(sdvm_compilerLocationKind_isRegisterPair(dest->kind));
            sdvm_compiler_riscv_mv(compiler, dest->firstRegister.value, arg0->firstRegister.value);
            sdvm_compiler_riscv_mv(compiler, dest->secondRegister.value, SDVM_RISCV_ZERO);
        }
        return true;

    default:
        abort();
    }
}

void sdvm_compiler_riscv_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, SdvmDebugLineInfoKindStatement, instruction->debugSourceLineInfo);

    if(instruction->decoding.isConstant)
    {
        // Emit the label, if this is a label.
        if(instruction->decoding.opcode == SdvmConstLabel)
        {
            sdvm_compiler_setLabelAtSectionEnd(state->compiler, instruction->location.immediateLabel, &state->compiler->textSection);
        }

        return;
    }

    sdvm_compilerInstruction_t *startInstruction = instruction;
    sdvm_compilerInstruction_t *endInstruction = instruction;
    if(instruction->pattern)
        endInstruction = instruction + instruction->pattern->size - 1;

    // Emit the argument moves.
    if(startInstruction->decoding.arg0IsInstruction)
    {
        sdvm_compilerInstruction_t *arg0 = state->instructions + startInstruction->decoding.instruction.arg0;
        sdvm_compiler_riscv_emitMoveFromLocationInto(state->compiler, &arg0->location, &instruction->arg0Location);
    }

    if(startInstruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + startInstruction->decoding.instruction.arg1;
        sdvm_compiler_riscv_emitMoveFromLocationInto(state->compiler, &arg1->location, &instruction->arg1Location);
    }

    // Emit the actual instruction operation
    if(instruction->pattern)
    {
        if(!instruction->pattern->generator(state, instruction->pattern->size, instruction))
            return;
    }
    else
    {
        if(!sdvm_compiler_riscv_emitFunctionInstructionOperation(state, instruction))
            return;
    }

    // Emit the result moves.
    sdvm_compiler_riscv_emitMoveFromLocationInto(state->compiler, &endInstruction->destinationLocation, &endInstruction->location);
}


void sdvm_compiler_riscv_emitFunctionInstructions(sdvm_functionCompilationState_t *state)
{
    uint32_t i = 0;
    while(i < state->instructionCount)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_riscv_emitFunctionInstruction(state, instruction);
        if(instruction->pattern)
            i += instruction->pattern->size;
        else
            ++i;
    }
}

void sdvm_compiler_riscv_emitFunctionEnding(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    sdvm_dwarf_cfi_endFDE(cfi, sdvm_compiler_getCurrentPC(compiler));
}

void sdvm_compiler_riscv_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    if(!state->requiresStackFrame)
        return;

    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    uint32_t pointerSize = state->compiler->pointerSize;
    sdvm_dwarf_cfi_beginEpilogue(cfi);


    int32_t stackSubtractionAmount = state->calloutStackSegment.endOffset;
    SDVM_ASSERT(stackSubtractionAmount >= (int32_t)pointerSize*2);

    sdvm_compiler_riscv_ld(compiler, SDVM_RISCV_FP, SDVM_RISCV_SP, stackSubtractionAmount - pointerSize*2);

    sdvm_compiler_riscv_ld(compiler, SDVM_RISCV_RA, SDVM_RISCV_SP, stackSubtractionAmount - pointerSize);

    sdvm_compiler_riscv_addi(compiler, SDVM_RISCV_SP, SDVM_RISCV_SP, stackSubtractionAmount);
    sdvm_dwarf_cfi_stackSizeRestore(cfi, sdvm_compiler_getCurrentPC(compiler), stackSubtractionAmount);

    sdvm_dwarf_cfi_endEpilogue(cfi);
}

bool sdvm_compiler_riscv_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_riscv_computeFunctionLocationConstraints(state);
    sdvm_compiler_riscv_allocateFunctionRegisters(state);
    sdvm_compiler_riscv_allocateFunctionSpillLocations(state);
    sdvm_compiler_riscv_computeFunctionStackLayout(state);

    if(state->compiler->verbose)
        sdvm_functionCompilationState_dump(state);

    // Align the function start symbol.
    sdvm_compiler_riscv_alignUnreacheableCode(state->compiler);

    // Set the function symbol
    size_t startOffset = state->compiler->textSection.contents.size;
    state->debugInfo->startPC = startOffset;
    sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&state->compiler->symbolTable, state->symbol, state->compiler->textSection.symbolIndex, startOffset);

    // Emit the prologue.
    sdvm_compiler_riscv_emitFunctionPrologue(state);

    // Emit the instructions.
    sdvm_compiler_riscv_emitFunctionInstructions(state);

    // End the function.
    sdvm_compiler_riscv_emitFunctionEnding(state);

    // Set the symbol size.
    size_t endOffset = state->compiler->textSection.contents.size;
    state->debugInfo->endPC = endOffset;
    sdvm_compilerSymbolTable_setSymbolSize(&state->compiler->symbolTable, state->symbol, endOffset - startOffset);
    sdvm_compiler_riscv_alignUnreacheableCode(state->compiler);

    return true;
}

uint32_t sdvm_compiler_riscv_mapElfRelocation(sdvm_compilerRelocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompRelocationAbsolute32: return SDVM_R_RISCV_32;
    case SdvmCompRelocationAbsolute64: return SDVM_R_RISCV_64;
    case SdvmCompRelocationRelative32: return SDVM_R_RISCV_32_PCREL;
    case SdvmCompRelocationSectionRelative32: return SDVM_R_RISCV_32;
    
    case SdvmCompRelocationRiscVJal: return SDVM_R_RISCV_JAL;
    case SdvmCompRelocationRiscVBranch: return SDVM_R_RISCV_BRANCH;
    case SdvmCompRelocationRiscVRelativeHi20: return SDVM_R_RISCV_PCREL_HI20;
    case SdvmCompRelocationRiscVRelativeLo12I: return SDVM_R_RISCV_PCREL_LO12_I;
    case SdvmCompRelocationRiscVRelativeLo12S: return SDVM_R_RISCV_PCREL_LO12_S;
    case SdvmCompRelocationRiscVAbsoluteHi20: return SDVM_R_RISCV_HI20;
    case SdvmCompRelocationRiscVAbsoluteLo12I: return SDVM_R_RISCV_LO12_I;
    case SdvmCompRelocationRiscVAbsoluteLo12S: return SDVM_R_RISCV_LO12_S;
    case SdvmCompRelocationRiscVRelax: return SDVM_R_RISCV_RELAX;
    case SdvmCompRelocationRiscVCallPLT: return SDVM_R_RISCV_CALL_PLT;
    default: abort();
    }
}

void sdvm_riscv_setupTargetAttributesWithArchString(sdvm_compiler_t *compiler, const char *archString)
{
    sdvm_compilerObjectSection_t *section = &compiler->targetSpecificAttributes;
    section->flags = SdvmCompSectionFlagTargetSpecificAttributes;
    section->entrySize = 1;
    section->name = ".riscv.attributes";
    section->machoSectionName = "__riscv_attributes"; // TODO: Find what is requried for Mach-O, if it gets supported.
    section->machoSegmentName = "__LD";
    section->relSectionName = ".riscv.attributes.rel";
    section->relaSectionName = ".riscv.attributes.rela";

    sdvm_dynarray_t *sectionContents = &section->contents;
    sdvm_dwarf_encodeByte(sectionContents, 'A');
    size_t attributesStart = sdvm_dwarf_encodeDWord(sectionContents, 0);

    sdvm_dwarf_encodeCString(sectionContents, "riscv");
    sdvm_dwarf_encodeULEB128(sectionContents, SDVM_Tag_RISCV_file);
    size_t subsectionStart = sdvm_dwarf_encodeDWord(sectionContents, 0);

    sdvm_dwarf_encodeULEB128(sectionContents, SDVM_Tag_RISCV_stack_align);
    sdvm_dwarf_encodeULEB128(sectionContents, compiler->target->defaultCC->stackAlignment);

    sdvm_dwarf_encodeULEB128(sectionContents, SDVM_Tag_RISCV_arch);
    sdvm_dwarf_encodeCString(sectionContents, archString);

    size_t subsectionEnd = sectionContents->size;
    uint32_t subsectionSize = subsectionEnd - subsectionStart;
    memcpy(sectionContents->data + subsectionStart, &subsectionSize, 4);

    size_t attributesEnd = sectionContents->size;
    uint32_t attributesSize = attributesEnd - attributesStart;
    memcpy(sectionContents->data + attributesStart, &attributesSize, 4);
}

void sdvm_riscv32_setupTargetAttributes(sdvm_compiler_t *compiler)
{
    sdvm_riscv_setupTargetAttributesWithArchString(compiler, "rv32i2p0_m2p0_a2p0_f2p0_d2p0_c2p0");
}

void sdvm_riscv64_setupTargetAttributes(sdvm_compiler_t *compiler)
{
    sdvm_riscv_setupTargetAttributesWithArchString(compiler, "rv64i2p0_m2p0_a2p0_f2p0_d2p0_c2p0");
}

static sdvm_compilerTarget_t sdvm_compilerTarget_riscv32_linux = {
    .pointerSize = 4,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_RISCV,
    .elfFlags = SDVM_EF_RISCV_RVC | SDVM_EF_RISCV_FLOAT_ABI_DOUBLE,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_RISCV32,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .closureCallNeedsScratch = true,
    .usesPIC = true,

    .defaultCC = &sdvm_riscv32_abi_callingConvention,
    .cdecl = &sdvm_riscv32_abi_callingConvention,
    .stdcall = &sdvm_riscv32_abi_callingConvention,
    .apicall = &sdvm_riscv32_abi_callingConvention,
    .thiscall = &sdvm_riscv32_abi_callingConvention,
    .vectorcall = &sdvm_riscv32_abi_callingConvention,

    .compileModuleFunction = sdvm_compiler_riscv_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_riscv_mapElfRelocation,
    .setupAttributesSection = sdvm_riscv32_setupTargetAttributes,

    .instructionPatterns = &sdvm_riscv_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_riscv32_linux(void)
{
    return &sdvm_compilerTarget_riscv32_linux;
}

static sdvm_compilerTarget_t sdvm_compilerTarget_riscv64_linux = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_RISCV,
    .elfFlags = SDVM_EF_RISCV_RVC | SDVM_EF_RISCV_FLOAT_ABI_DOUBLE,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_RISCV64,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .closureCallNeedsScratch = true,
    .usesPIC = true,

    .defaultCC = &sdvm_riscv64_abi_callingConvention,
    .cdecl = &sdvm_riscv64_abi_callingConvention,
    .stdcall = &sdvm_riscv64_abi_callingConvention,
    .apicall = &sdvm_riscv64_abi_callingConvention,
    .thiscall = &sdvm_riscv64_abi_callingConvention,
    .vectorcall = &sdvm_riscv64_abi_callingConvention,

    .compileModuleFunction = sdvm_compiler_riscv_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_riscv_mapElfRelocation,
    .setupAttributesSection = sdvm_riscv64_setupTargetAttributes,

    .instructionPatterns = &sdvm_riscv_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_riscv64_linux(void)
{
    return &sdvm_compilerTarget_riscv64_linux;
}
