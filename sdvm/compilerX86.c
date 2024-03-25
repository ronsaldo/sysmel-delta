#include "compilerX86.h"
#include "module.h"
#include "elf.h"
#include <string.h>

#define SDVM_X86_REG_DEF(regKind, regSize, name, regValue) const sdvm_compilerRegister_t sdvm_x86_ ## name = {\
    .kind = SdvmCompRegisterKind ## regKind, \
    .size = regSize, \
    .value = regValue, \
};
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

static const sdvm_compilerRegister_t *sdvm_x64_sysv_integerPassingRegisters[] = {
    &sdvm_x86_RDI,
    &sdvm_x86_RSI,
    &sdvm_x86_RDX,
    &sdvm_x86_RCX,
    &sdvm_x86_R8,
    &sdvm_x86_R9,
};
static const uint32_t sdvm_x64_sysv_integerPassingRegisterCount = sizeof(sdvm_x64_sysv_integerPassingRegisters) / sizeof(sdvm_x64_sysv_integerPassingRegisters[0]);

static const sdvm_compilerRegister_t *sdvm_x64_sysv_integerPassingDwordRegisters[] = {
    &sdvm_x86_EDI,
    &sdvm_x86_ESI,
    &sdvm_x86_EDX,
    &sdvm_x86_ECX,
    &sdvm_x86_R8D,
    &sdvm_x86_R9D,
};
static const uint32_t sdvm_x64_sysv_integerPassingDwordRegisterCount = sizeof(sdvm_x64_sysv_integerPassingDwordRegisters) / sizeof(sdvm_x64_sysv_integerPassingDwordRegisters[0]);

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_allocatableIntegerRegisters[] = {
    SDVM_X86_RAX,

    SDVM_X86_RDI, // Arg 1
    SDVM_X86_RSI, // Arg 2
    SDVM_X86_RDX, // Arg 3
    SDVM_X86_RCX, // Arg 4
    SDVM_X86_R8,  // Arg 5
    SDVM_X86_R9,  // Arg 6
    SDVM_X86_R10, // Static function chain/Closure pointer
    SDVM_X86_R11, // Closure GC pointer

    SDVM_X86_RBX,

    SDVM_X86_R12,
    SDVM_X86_R13,
    SDVM_X86_R14,
    SDVM_X86_R15, // Optional GOT pointer
};
static const uint32_t sdvm_x64_sysv_allocatableIntegerRegisterCount = sizeof(sdvm_x64_sysv_allocatableIntegerRegisters) / sizeof(sdvm_x64_sysv_allocatableIntegerRegisters[0]);

static const sdvm_compilerRegister_t *sdvm_x64_sysv_vectorFloatPassingRegister[] = {
    &sdvm_x86_XMM0,  &sdvm_x86_XMM1,  &sdvm_x86_XMM2,  &sdvm_x86_XMM3,
    &sdvm_x86_XMM4,  &sdvm_x86_XMM5,  &sdvm_x86_XMM6,  &sdvm_x86_XMM7,
};
static const uint32_t sdvm_x64_sysv_vectorFloatPassingRegisterCount = sizeof(sdvm_x64_sysv_vectorFloatPassingRegister) / sizeof(sdvm_x64_sysv_vectorFloatPassingRegister[0]);

static const sdvm_compilerRegister_t *sdvm_x64_sysv_vectorIntegerPassingRegister[] = {
    &sdvm_x86_XMM0I,  &sdvm_x86_XMM1I,  &sdvm_x86_XMM2I,  &sdvm_x86_XMM3I,
    &sdvm_x86_XMM4I,  &sdvm_x86_XMM5I,  &sdvm_x86_XMM6I,  &sdvm_x86_XMM7I,
};
static const uint32_t sdvm_x64_sysv_vectorIntegerPassingRegisterCount = sizeof(sdvm_x64_sysv_vectorIntegerPassingRegister) / sizeof(sdvm_x64_sysv_vectorIntegerPassingRegister[0]);

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callPreservedIntegerRegisters[] = {
    SDVM_X86_RBX, SDVM_X86_R12, SDVM_X86_R13, SDVM_X86_R14, SDVM_X86_R15, SDVM_X86_RSP, SDVM_X86_RBP
};
static const uint32_t sdvm_x64_sysv_callPreservedIntegerRegisterCount = sizeof(sdvm_x64_sysv_callPreservedIntegerRegisters) / sizeof(sdvm_x64_sysv_callPreservedIntegerRegisters[0]);

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callTouchedIntegerRegisters[] = {
    SDVM_X86_RAX, SDVM_X86_RCX, SDVM_X86_RDX, SDVM_X86_RSI, SDVM_X86_RDI, SDVM_X86_R8, SDVM_X86_R9, SDVM_X86_R10, SDVM_X86_R11
};
static const uint32_t sdvm_x64_sysv_callTouchedIntegerRegisterCount = sizeof(sdvm_x64_sysv_callTouchedIntegerRegisters) / sizeof(sdvm_x64_sysv_callTouchedIntegerRegisters[0]);

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callTouchedVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,  SDVM_X86_XMM6,  SDVM_X86_XMM7,
    SDVM_X86_XMM8,  SDVM_X86_XMM9,  SDVM_X86_XMM10, SDVM_X86_XMM11,
    SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15,
};
static const uint32_t sdvm_x64_sysv_callTouchedVectorRegisterCount = sizeof(sdvm_x64_sysv_callTouchedVectorRegisters) / sizeof(sdvm_x64_sysv_callTouchedVectorRegisters[0]);

static const sdvm_compilerRegisterValue_t sdvm_x64_allocatableVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,  SDVM_X86_XMM6,  SDVM_X86_XMM7,
    SDVM_X86_XMM8,  SDVM_X86_XMM9,  SDVM_X86_XMM10, SDVM_X86_XMM11,
    SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15,
};
static const uint32_t sdvm_x64_allocatableVectorRegisterCount = sizeof(sdvm_x64_allocatableVectorRegisters) / sizeof(sdvm_x64_allocatableVectorRegisters[0]);

const sdvm_compilerCallingConvention_t sdvm_x64_sysv_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 8,
    .integerRegisterCount = sdvm_x64_sysv_integerPassingRegisterCount,

    .integer32Registers = sdvm_x64_sysv_integerPassingDwordRegisters,
    .integer64Registers = sdvm_x64_sysv_integerPassingRegisters,
    .integerRegisters = sdvm_x64_sysv_integerPassingRegisters,

    .closureRegister = &sdvm_x86_R10,
    .closureGCRegister = &sdvm_x86_R11,

    .firstInteger32ResultRegister = &sdvm_x86_EAX,
    .firstInteger64ResultRegister = &sdvm_x86_RAX,
    .firstIntegerResultRegister = &sdvm_x86_RAX,
    .secondInteger32ResultRegister = &sdvm_x86_EDX,
    .secondInteger64ResultRegister = &sdvm_x86_RDX,
    .secondIntegerResultRegister = &sdvm_x86_RDX,

    .vectorRegisterSize = 16,
    .vectorRegisterCount = sdvm_x64_sysv_vectorFloatPassingRegisterCount,
    .vectorFloatRegisters = sdvm_x64_sysv_vectorFloatPassingRegister,
    .vectorIntegerRegisters = sdvm_x64_sysv_vectorIntegerPassingRegister,

    .firstVectorFloatResultRegister = &sdvm_x86_XMM0,
    .firstVectorIntegerResultRegister = &sdvm_x86_XMM0I,
    .secondVectorFloatResultRegister = &sdvm_x86_XMM1,
    .secondVectorIntegerResultRegister = &sdvm_x86_XMM1I,

    .allocatableIntegerRegisterCount = sdvm_x64_sysv_allocatableIntegerRegisterCount,
    .allocatableIntegerRegisters = sdvm_x64_sysv_allocatableIntegerRegisters,
    
    .allocatableVectorRegisterCount = sdvm_x64_allocatableVectorRegisterCount,
    .allocatableVectorRegisters = sdvm_x64_allocatableVectorRegisters,

    .callPreservedIntegerRegisterCount = sdvm_x64_sysv_callPreservedIntegerRegisterCount,
    .callPreservedIntegerRegisters = sdvm_x64_sysv_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = sdvm_x64_sysv_callTouchedIntegerRegisterCount,
    .callTouchedIntegerRegisters = sdvm_x64_sysv_callTouchedIntegerRegisters,

    .callTouchedVectorRegisterCount = sdvm_x64_sysv_callTouchedVectorRegisterCount,
    .callTouchedVectorRegisters = sdvm_x64_sysv_callTouchedVectorRegisters
};

uint8_t sdvm_compiler_x86_modRmByte(int8_t rm, uint8_t regOpcode, uint8_t mod)
{
    return (rm & SDVM_X86_REG_HALF_MASK) | ((regOpcode & SDVM_X86_REG_HALF_MASK) << 3) | (mod << 6);
}

uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg)
{
    return (reg & SDVM_X86_REG_HALF_MASK) | (4 << 3) ;
}

void sdvm_compiler_x86_modRmReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(rm, reg, 3));
}

void sdvm_compiler_x86_modRmOp(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t rm, uint8_t opcode)
{
    sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(rm, opcode, 3));
}

void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B)
{
    if(W || R || X || B)
    {
        sdvm_compiler_addInstructionByte(compiler, 0x40 | ((W ? 1 : 0) << 3) | ((R ? 1 : 0) << 2) | ((X ? 1 : 0) << 1) | (B ? 1 : 0));
    }
}

void sdvm_compiler_x86_rexPlusReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, false, false, reg > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexRmReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, reg > SDVM_X86_REG_HALF_MASK, false, rm > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, reg > SDVM_X86_REG_HALF_MASK, false, false);
}

void sdvm_compiler_x86_rexRm(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm)
{
    sdvm_compiler_x86_rex(compiler, W, false, false, rm > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_prefix(sdvm_compiler_t *compiler, uint8_t prefix)
{
    sdvm_compiler_addInstructionByte(compiler, prefix);
}

void sdvm_compiler_x86_opcode(sdvm_compiler_t *compiler, uint8_t opcode)
{
    sdvm_compiler_addInstructionByte(compiler, opcode);
}

void sdvm_compiler_x86_opcode2(sdvm_compiler_t *compiler, uint16_t opcode)
{
    sdvm_compiler_addInstructionBytes(compiler, 2, &opcode);
}

void sdvm_compiler_x86_opcodePlusReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_addInstructionByte(compiler, opcode + (reg & SDVM_X86_REG_HALF_MASK));
}

void sdvm_compiler_x86_imm8(sdvm_compiler_t *compiler, uint8_t value)
{
    sdvm_compiler_addInstructionBytes(compiler, 1, &value);
}

void sdvm_compiler_x86_imm16(sdvm_compiler_t *compiler, uint16_t value)
{
    sdvm_compiler_addInstructionBytes(compiler, 2, &value);
}

void sdvm_compiler_x86_imm32(sdvm_compiler_t *compiler, uint32_t value)
{
    sdvm_compiler_addInstructionBytes(compiler, 4, &value);
}

void sdvm_compiler_x86_imm64(sdvm_compiler_t *compiler, uint64_t value)
{
    sdvm_compiler_addInstructionBytes(compiler, 8, &value);
}

void sdvm_compiler_x86_lock(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0xF0);
}

void sdvm_compiler_x86_repne(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0xF2);
}

void sdvm_compiler_x86_rep(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0xF3);
}

void sdvm_compiler_x86_fsPrefix(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0x64);
}

void sdvm_compiler_x86_gsPrefix(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0x65);
}

void sdvm_compiler_x86_operandPrefix(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0x66);
}

void sdvm_compiler_x86_addressPrefix(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_prefix(compiler, 0x67);
}

void sdvm_compiler_x86_modGsvReg(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, sdvm_x86_registerIndex_t reg, int32_t addend, int32_t relativeOffset)
{
    uint32_t addressPlaceHolder = 0;
    sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(5, reg, 0));
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRelative32AtGot, symbolHandle, addend + relativeOffset - 4);
    sdvm_compiler_addInstructionBytes(compiler, 4, &addressPlaceHolder);
}

void sdvm_compiler_x86_modLsvReg(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, sdvm_x86_registerIndex_t reg, int32_t addend, int32_t relativeOffset)
{
    uint32_t addressPlaceHolder = 0;
    sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(5, reg, 0));
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRelative32, symbolHandle, addend + relativeOffset - 4);
    sdvm_compiler_addInstructionBytes(compiler, 4, &addressPlaceHolder);
}

void sdvm_compiler_x86_modRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t reg)
{
    base &= SDVM_X86_REG_HALF_MASK;
    reg &= SDVM_X86_REG_HALF_MASK;

    if(offset == 0 && base != SDVM_X86_RBP)
    {
        if(base == SDVM_X86_RSP)
        {
            sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(SDVM_X86_RSP, reg, 0));
            sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_sibOnlyBase(base));
        }
        else
        {
            sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(base, reg, 0));
        }
        return;
    }

    bool hasByteOffset = (int8_t)offset == offset;
    sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_modRmByte(base, reg, hasByteOffset ? 1 : 2));

    if(base == SDVM_X86_RSP)
        sdvm_compiler_addInstructionByte(compiler, sdvm_compiler_x86_sibOnlyBase(base));
    
    if(hasByteOffset)
        sdvm_compiler_x86_imm8(compiler, offset);
    else
        sdvm_compiler_x86_imm32(compiler, offset);
}

void sdvm_compiler_x86_modRmoOp(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, uint8_t opcode)
{
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, opcode);
}

void sdvm_compiler_x86_int3(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode(compiler, 0xCC);
}

void sdvm_compiler_x86_ud2(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F0B);
}

void sdvm_compiler_x86_callGsv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    uint32_t addressPlaceHolder = 0;
    sdvm_compiler_addInstructionByte(compiler, 0xE8);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRelative32AtPlt, symbolHandle, addend - 4);
    sdvm_compiler_addInstructionBytes(compiler, 4, &addressPlaceHolder);
}

void sdvm_compiler_x86_callLsv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    uint32_t addressPlaceHolder = 0;
    sdvm_compiler_addInstructionByte(compiler, 0xE8);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationRelative32, symbolHandle, addend - 4);
    sdvm_compiler_addInstructionBytes(compiler, 4, &addressPlaceHolder);
}

void sdvm_compiler_x86_callReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexRm(compiler, false, reg);
    sdvm_compiler_x86_opcode(compiler, 0xFF);
    sdvm_compiler_x86_modRmOp(compiler, reg, 2);
}

void sdvm_compiler_x86_callRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRm(compiler, false, base);
    sdvm_compiler_x86_opcode(compiler, 0xFF);
    sdvm_compiler_x86_modRmoOp(compiler, base, offset, 2);
}

void sdvm_compiler_x86_jmpReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexRm(compiler, false, reg);
    sdvm_compiler_x86_opcode(compiler, 0xFF);
    sdvm_compiler_x86_modRmOp(compiler, reg, 2);
}

void sdvm_compiler_x86_jmpRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRm(compiler, false, base);
    sdvm_compiler_x86_opcode(compiler, 0xFF);
    sdvm_compiler_x86_modRmoOp(compiler, base, offset, 4);
}

void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode(compiler, 0xC3);
}

void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexPlusReg(compiler, false, reg);
    sdvm_compiler_x86_opcodePlusReg(compiler, 0x50, reg);
}

void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexPlusReg(compiler, false, reg);
    sdvm_compiler_x86_opcodePlusReg(compiler, 0x58, reg);
}

void sdvm_compiler_x86_endbr32(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0xF3, 0x0F, 0x1E, 0xFB,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_endbr64(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0xF3, 0x0F, 0x1E, 0xFA,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

#pragma region X86_Instructions_64

void sdvm_compiler_x86_xchg64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode(compiler, 0x87);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mov64RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_mov64RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, source);
    sdvm_compiler_x86_opcode(compiler, 0x89);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_mov64RegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int64_t offset)
{
    sdvm_compiler_x86_rexReg(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
    sdvm_compiler_x86_add64RegImmS32(compiler, destination, offset);
}

void sdvm_compiler_x86_lea64RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset)
{
    sdvm_compiler_x86_rexReg(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8D);
    sdvm_compiler_x86_modLsvReg(compiler, sourceSymbol, destination, offset, 0);
}

void sdvm_compiler_x86_lea64RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8D);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);
    
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0xC7);
    sdvm_compiler_x86_modRmOp(compiler, destination, 0);
    sdvm_compiler_x86_imm32(compiler, value);
}

void sdvm_compiler_x86_mov64RegImmS64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int64_t value)
{
    if(value == (int64_t)(int32_t)value)
        sdvm_compiler_x86_mov64RegImmS32(compiler, destination, value);
    else
        sdvm_compiler_x86_movabs64(compiler, destination, value);
}

void sdvm_compiler_x86_mov64RegImmU64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value)
{
    
    if(value == (uint64_t)(uint32_t)value)
        sdvm_compiler_x86_mov32RegImm32(compiler, destination, value);
    else
        sdvm_compiler_x86_movabs64(compiler, destination, value);
}

void sdvm_compiler_x86_movabs64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcodePlusReg(compiler, 0xB8, destination);
    sdvm_compiler_x86_imm64(compiler, value);
}

void sdvm_compiler_x86_alu64RmReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, destination, source);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmReg(compiler, destination, source);
}

void sdvm_compiler_x86_alu64RmImm32(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint32_t value)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm32(compiler, value);
}

void sdvm_compiler_x86_alu64RmImm8(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint8_t value)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm8(compiler, value);
}

void sdvm_compiler_x86_alu64RmImm32_S8(sdvm_compiler_t *compiler, uint8_t opcodeImm32, uint8_t opcodeImm8, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, int32_t value)
{
    if(value == (int32_t)(int8_t)value)
        sdvm_compiler_x86_alu64RmImm8(compiler, opcodeImm8, destination, regOpcode, value);
    else
        sdvm_compiler_x86_alu64RmImm32(compiler, opcodeImm32, destination, regOpcode, value);
}

void sdvm_compiler_x86_add64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x01, destination, source);
}

void sdvm_compiler_x86_sub64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x29, destination, source);
}

void sdvm_compiler_x86_and64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x21, destination, source);
}

void sdvm_compiler_x86_or64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x09, destination, source);
}

void sdvm_compiler_x86_xor64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x31, destination, source);
}

void sdvm_compiler_x86_add64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 0, value);
}

void sdvm_compiler_x86_sub64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 5, value);
}

void sdvm_compiler_x86_and64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == -1)
        return;

    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 4, value);
}

void sdvm_compiler_x86_or64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 1, value);
}

void sdvm_compiler_x86_xor64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 6, value);
}

#pragma endregion X86_Instructions_64

#pragma region X86_Instructions_32

void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);

    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xC7);
    sdvm_compiler_x86_modRmOp(compiler, destination, 0);
    sdvm_compiler_x86_imm32(compiler, value);
}

void sdvm_compiler_x86_mov32RegReg_noOpt(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination != source)
        sdvm_compiler_x86_mov32RegReg_noOpt(compiler, destination, source);
}

void sdvm_compiler_x86_mov32RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_mov32RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode(compiler, 0x89);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_mov32RegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset)
{
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8B);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
    sdvm_compiler_x86_add32RegImm32(compiler, destination, offset);
}

void sdvm_compiler_x86_lea32RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset)
{
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8D);
    sdvm_compiler_x86_modLsvReg(compiler, sourceSymbol, destination, offset, 0);
}

void sdvm_compiler_x86_alu32RmReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, destination, source);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmReg(compiler, destination, source);
}

void sdvm_compiler_x86_alu32RmImm32(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint32_t value)
{
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm32(compiler, value);
}

void sdvm_compiler_x86_alu32RmImm8(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint8_t value)
{
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm8(compiler, value);
}

void sdvm_compiler_x86_alu32RmImm32_S8(sdvm_compiler_t *compiler, uint8_t opcodeImm32, uint8_t opcodeImm8, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint32_t value)
{
    if((int32_t)value == (int32_t)(int8_t)value)
        sdvm_compiler_x86_alu32RmImm8(compiler, opcodeImm8, destination, regOpcode, value);
    else
        sdvm_compiler_x86_alu32RmImm32(compiler, opcodeImm32, destination, regOpcode, value);
}

void sdvm_compiler_x86_add32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x01, destination, source);
}

void sdvm_compiler_x86_sub32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x29, destination, source);
}

void sdvm_compiler_x86_and32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x21, destination, source);
}

void sdvm_compiler_x86_or32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x09, destination, source);
}

void sdvm_compiler_x86_xor32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x31, destination, source);
}

void sdvm_compiler_x86_add32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 0, value);
}

void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 5, value);
}

void sdvm_compiler_x86_and32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == -1)
        return;

    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 4, value);
}

void sdvm_compiler_x86_or32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 1, value);
}

void sdvm_compiler_x86_xor32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 6, value);
}

#pragma endregion X86_Instructions_32

#pragma region X86_Instructions_16

void sdvm_compiler_x86_mov16RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode(compiler, 0x89);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movzxReg32Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB7);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movzxReg32Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB7);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movzxReg64Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB7);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movzxReg64Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB7);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movsxReg32Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsxReg32Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBF);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movsxReg64Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsxReg64Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBF);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_alu16RmReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRmReg(compiler, false, destination, source);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmReg(compiler, destination, source);
}

void sdvm_compiler_x86_alu16RmImm16(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint16_t value)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm16(compiler, value);
}

void sdvm_compiler_x86_alu16RmImm8(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint8_t value)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm8(compiler, value);
}

void sdvm_compiler_x86_alu16RmImm16_S8(sdvm_compiler_t *compiler, uint8_t opcodeImm32, uint8_t opcodeImm8, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint32_t value)
{
    if((int16_t)value == (int16_t)(int8_t)value)
        sdvm_compiler_x86_alu16RmImm8(compiler, opcodeImm8, destination, regOpcode, value);
    else
        sdvm_compiler_x86_alu16RmImm16(compiler, opcodeImm32, destination, regOpcode, value);
}

void sdvm_compiler_x86_add16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x01, destination, source);
}

void sdvm_compiler_x86_sub16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x29, destination, source);
}

void sdvm_compiler_x86_and16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x21, destination, source);
}

void sdvm_compiler_x86_or16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x09, destination, source);
}

void sdvm_compiler_x86_xor16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x31, destination, source);
}

void sdvm_compiler_x86_add16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 0, value);
}

void sdvm_compiler_x86_sub16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 5, value);
}

void sdvm_compiler_x86_and16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    if(value == -1)
        return;

    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 4, value);
}

void sdvm_compiler_x86_or16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 1, value);
}

void sdvm_compiler_x86_xor16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 6, value);
}

#pragma endregion X86_Instructions_16

#pragma region X86_RegisterConstraints
sdvm_compilerLocation_t sdvm_compilerLocation_x64_immediateS64(sdvm_compiler_t *compiler, int64_t value)
{
    if(value == (int64_t)(int32_t)value)
        return sdvm_compilerLocation_immediateS32(value);
    else
        return sdvm_compilerLocation_constSectionS64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_x64_immediateU64(sdvm_compiler_t *compiler, uint64_t value)
{
    if(value == (uint64_t)(uint32_t)value)
        return sdvm_compilerLocation_immediateS32(value);
    else
        return sdvm_compilerLocation_constSectionU64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_x86_intRegOrImm32(uint8_t size, sdvm_compilerInstruction_t *operand)
{
    switch(operand->location.kind)
    {
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateF32:
        return operand->location;
    default:
        return sdvm_compilerLocation_integerRegister(size);
    }
}

sdvm_compilerLocation_t sdvm_compilerLocation_x86_specificRegOrImm32(sdvm_compilerRegister_t reg, sdvm_compilerInstruction_t *operand)
{
    switch(operand->location.kind)
    {
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateF32:
        return operand->location;
    default:
        return sdvm_compilerLocation_specificRegister(reg);
    }
}

sdvm_compilerLocation_t sdvm_compilerLocation_x64_intRegOrImmS32(uint8_t size, sdvm_compilerInstruction_t *operand)
{
    switch(operand->location.kind)
    {
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateF32:
        if((operand->location.immediateU32 & 1<<31) == 0)
            return sdvm_compilerLocation_immediateS32(operand->location.immediateU32);
        return sdvm_compilerLocation_integerRegister(size);
    case SdvmCompLocationImmediateS32:
        return operand->location;
    default:
        return sdvm_compilerLocation_integerRegister(size);
    }
}

void sdvm_compiler_x64_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_immediateU32(instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64SExt:
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_x64_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_x64_immediateU64(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64ConstSection:
        case SdvmConstPointerConstSection:
            {
                int64_t value;
                memcpy(&value, state->module->constSectionData + instruction->decoding.constant.unsignedPayload, 8);
                instruction->location = sdvm_compilerLocation_x64_immediateS64(state->compiler, value);
            }
            break;
        default:
            sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
        }

        return;
    }

    sdvm_compilerInstruction_t *arg0 = instruction->decoding.arg0IsInstruction ? state->instructions + instruction->decoding.instruction.arg0 : NULL;
    sdvm_compilerInstruction_t *arg1 = instruction->decoding.arg1IsInstruction ? state->instructions + instruction->decoding.instruction.arg1 : NULL;

    switch (instruction->decoding.opcode)
    {
    case SdvmInstInt16Add:
    case SdvmInstInt16Sub:
    case SdvmInstInt16And:
    case SdvmInstInt16Or:
    case SdvmInstUInt16Add:
    case SdvmInstUInt16Sub:
    case SdvmInstUInt16And:
    case SdvmInstUInt16Xor:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(2);
        return;
    case SdvmInstInt16Mul:
    case SdvmInstUInt16Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(2);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(2);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(2);
        return;
    case SdvmInstInt16Div:
    case SdvmInstInt16UDiv:
    case SdvmInstInt16Rem:
    case SdvmInstInt16URem:
    case SdvmInstUInt16Div:
    case SdvmInstUInt16UDiv:
    case SdvmInstUInt16Rem:
    case SdvmInstUInt16URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(2);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_DX);
        return;
    case SdvmInstInt16Lsl:
    case SdvmInstInt16Lsr:
    case SdvmInstInt16Asr:
    case SdvmInstUInt16Lsl:
    case SdvmInstUInt16Lsr:
    case SdvmInstUInt16Asr:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_specificRegOrImm32(sdvm_x86_CX, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(2);
        return;

    case SdvmInstInt32Add:
    case SdvmInstInt32Sub:
    case SdvmInstInt32And:
    case SdvmInstInt32Or:
    case SdvmInstUInt32Add:
    case SdvmInstUInt32Sub:
    case SdvmInstUInt32And:
    case SdvmInstUInt32Xor:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        return;
    case SdvmInstInt32Mul:
    case SdvmInstUInt32Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        return;
    case SdvmInstInt32Div:
    case SdvmInstInt32UDiv:
    case SdvmInstInt32Rem:
    case SdvmInstInt32URem:
    case SdvmInstUInt32Div:
    case SdvmInstUInt32UDiv:
    case SdvmInstUInt32Rem:
    case SdvmInstUInt32URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_EDX);
        return;
    case SdvmInstInt32Lsl:
    case SdvmInstInt32Lsr:
    case SdvmInstInt32Asr:
    case SdvmInstUInt32Lsl:
    case SdvmInstUInt32Lsr:
    case SdvmInstUInt32Asr:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_specificRegOrImm32(sdvm_x86_ECX, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        return;

    case SdvmInstInt64Add:
    case SdvmInstInt64Sub:
    case SdvmInstInt64And:
    case SdvmInstInt64Or:
    case SdvmInstUInt64Add:
    case SdvmInstUInt64Sub:
    case SdvmInstUInt64And:
    case SdvmInstUInt64Xor:
        instruction->arg0Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        return;
    case SdvmInstInt64Mul:
    case SdvmInstUInt64Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        return;
    case SdvmInstInt64Div:
    case SdvmInstInt64UDiv:
    case SdvmInstInt64Rem:
    case SdvmInstInt64URem:
    case SdvmInstUInt64Div:
    case SdvmInstUInt64UDiv:
    case SdvmInstUInt64Rem:
    case SdvmInstUInt64URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_RDX);
        return;
    case SdvmInstInt64Lsl:
    case SdvmInstInt64Lsr:
    case SdvmInstInt64Asr:
    case SdvmInstUInt64Lsl:
    case SdvmInstUInt64Lsr:
    case SdvmInstUInt64Asr:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(8, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_specificRegOrImm32(sdvm_x86_RCX, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        return;
    default:
        sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
    }
}

void sdvm_compiler_x64_computeFunctionLocationConstraints(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerTarget_t *target = state->compiler->target;
    state->callingConvention = target->defaultCC;
    state->currentCallCallingConvention = target->defaultCC;

    for(uint32_t i = 0; i < state->instructionCount; ++i)
        sdvm_compiler_x64_computeInstructionLocationConstraints(state, state->instructions + i);
}

#pragma endregion X86_RegisterConstraints

#pragma region X86_CodeGeneration

void sdvm_compiler_x64_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compiler_x86_endbr64(compiler);

    if(!state->requiresStackFrame)
        return;

    sdvm_compiler_x86_push(compiler, SDVM_X86_RBP);
    sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RBP, SDVM_X86_RSP);

    // Preserved integer registers.
    for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedIntegerRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, reg))
            sdvm_compiler_x86_push(compiler, reg);
    }

    sdvm_compiler_x86_sub64RegImmS32(compiler, SDVM_X86_RSP, state->calloutStackSegment.endOffset - state->prologueStackSegment.endOffset);

    // Preserved vector registers.
    int32_t vectorOffset = state->stackFramePointerAnchorOffset - state->vectorCallPreservedRegisterStackSegment.endOffset;
    for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedVectorRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedVectorRegisterSet, reg))
        {
            // TODO: Emit movapd
            abort();
            vectorOffset += 16;
        }
    }
}

void sdvm_compiler_x64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;

    if(!state->requiresStackFrame)
        return;

    // Preserved vector registers.
    int32_t vectorOffset = state->stackFramePointerAnchorOffset - state->vectorCallPreservedRegisterStackSegment.endOffset;
    for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedVectorRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedVectorRegisterSet, reg))
        {
            // TODO: Emit movapd
            abort();
            vectorOffset += 16;
        }
    }

    uint32_t pointerSize = compiler->pointerSize;
    if(state->prologueStackSegment.size > pointerSize * 2)
    {
        sdvm_compiler_x86_lea64RegRmo(compiler, SDVM_X86_RSP, SDVM_X86_RBP, state->stackFramePointerAnchorOffset - state->prologueStackSegment.endOffset);
        for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
        {
            sdvm_compilerRegisterValue_t reg = convention->callPreservedIntegerRegisters[convention->callPreservedIntegerRegisterCount - i - 1];
            if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, reg))
                sdvm_compiler_x86_pop(compiler, reg);
        }
    }
    else
    {
        sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RSP, SDVM_X86_RBP);
    }

    sdvm_compiler_x86_pop(compiler, SDVM_X86_RBP);
}

void sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        return sdvm_compiler_x86_xor32RegReg(compiler, reg->value, reg->value);
    case SdvmCompLocationImmediateS32:
        return sdvm_compiler_x86_mov64RegImmS32(compiler, reg->value, sourceLocation->immediateS32);
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateU32:
        return sdvm_compiler_x86_mov32RegImm32(compiler, reg->value, sourceLocation->immediateU32);
    case SdvmCompLocationImmediateS64:
        return sdvm_compiler_x86_mov64RegImmS64(compiler, reg->value, sourceLocation->immediateS64);
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateU64:
        return sdvm_compiler_x86_mov64RegImmU64(compiler, reg->value, sourceLocation->immediateU64);
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        if(sourceLocation->firstRegister.size <= 4)
            return sdvm_compiler_x86_mov32RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        return sdvm_compiler_x86_mov64RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
    case SdvmCompLocationStack:
    case SdvmCompLocationStackPair:
        switch(reg->size)
        {
        case 2:
            if(sourceLocation->isSigned)
                return sdvm_compiler_x86_movsxReg32Rmo16(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_x86_movzxReg32Rmo16(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 4: return sdvm_compiler_x86_mov32RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 8: return sdvm_compiler_x86_mov64RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        default: return abort();
        }
    case SdvmCompLocationLocalSymbolValue:
        {
            switch(reg->size)
            {
            case 4:
                return sdvm_compiler_x86_lea32RegLsv(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
            case 8:
                return sdvm_compiler_x86_lea64RegLsv(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
            default:
                return abort();
            }
        }
    case SdvmCompLocationGlobalSymbolValue:
        {
            switch(reg->size)
            {
            case 4:
                return sdvm_compiler_x86_mov32RegGsv(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
            case 8:
                return sdvm_compiler_x86_mov64RegGsv(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
            default:
                return abort();
            }
        }
    default: return abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloat(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    abort();
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorInteger(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    abort();
}

void sdvm_compiler_x64_emitMoveFromLocationIntoRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(reg->kind)
    {
    case SdvmCompRegisterKindInteger:
        return sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindFloat:
    case SdvmCompRegisterKindVectorFloat:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloat(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindVectorInteger:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorInteger(compiler, sourceLocation, reg);
    default: abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationRegister:
        sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, firstRegister);
        return sdvm_compiler_x86_xor32RegReg(compiler, secondRegister->value, secondRegister->value);

    case SdvmCompLocationRegisterPair:
        {
            sdvm_compilerRegisterValue_t sourceFirstRegisterValue = sourceLocation->firstRegister.value;
            sdvm_compilerRegisterValue_t sourceSecondRegisterValue = sourceLocation->secondRegister.value;
            sdvm_compilerRegisterValue_t destFirstRegisterValue = firstRegister->value;
            sdvm_compilerRegisterValue_t destSecondRegisterValue = secondRegister->value;

            bool isFirstInSecond = destSecondRegisterValue == sourceFirstRegisterValue;
            bool isSecondInFirst = destFirstRegisterValue == sourceSecondRegisterValue;

            if(isFirstInSecond && isSecondInFirst)
            {
                return sdvm_compiler_x86_xchg64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }
            else if(isSecondInFirst)
            {
                sdvm_compiler_x86_mov64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
                return sdvm_compiler_x86_mov64RegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
            }
            else
            {
                sdvm_compiler_x86_mov64RegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
                return sdvm_compiler_x86_mov64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }
        }

    default: abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    abort();
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    abort();
}

void sdvm_compiler_x64_emitMoveFromLocationIntoRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    switch(firstRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        return sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegisterPair(compiler, sourceLocation, firstRegister, secondRegister);
    case SdvmCompRegisterKindVectorFloat:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatPair(compiler, sourceLocation, firstRegister, secondRegister);
    case SdvmCompRegisterKindVectorInteger:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerPair(compiler, sourceLocation, firstRegister, secondRegister);
    default:
        return abort();
    }
}

void sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(sdvm_compiler_t *compiler, const sdvm_compilerRegister_t *sourceRegister, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        switch(sourceRegister->size)
        {
        case 2: return sdvm_compiler_x86_mov16RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
        case 4: return sdvm_compiler_x86_mov32RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
        case 8: return sdvm_compiler_x86_mov64RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
        default:
            return abort();
        }
    default:
        return abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoStack(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
        return sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);
    case SdvmCompLocationRegisterPair:
        {
            sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);

            sdvm_compilerStackLocation_t nextLocation = *stackLocation;
            nextLocation.segmentOffset += sourceLocation->firstRegister.size;
            nextLocation.framePointerOffset += sourceLocation->firstRegister.size;

            return sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->secondRegister, &nextLocation);
        }
    default: return abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationInto(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerLocation_t *destinationLocation)
{
    switch(destinationLocation->kind)
    {
    case SdvmCompLocationNull:
        // Ignored.
        return;
    case SdvmCompLocationRegister:
        return sdvm_compiler_x64_emitMoveFromLocationIntoRegister(compiler, sourceLocation, &destinationLocation->firstRegister);
    case SdvmCompLocationRegisterPair:
        return sdvm_compiler_x64_emitMoveFromLocationIntoRegisterPair(compiler, sourceLocation, &destinationLocation->firstRegister, &destinationLocation->secondRegister);
    case SdvmCompLocationStack:
        return sdvm_compiler_x64_emitMoveFromLocationIntoStack(compiler, sourceLocation, &destinationLocation->firstStackLocation);
    case SdvmCompLocationStackPair:
        return abort();
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateLabel:
    case SdvmCompLocationLocalSymbolValue:
    case SdvmCompLocationGlobalSymbolValue:
        return;
    default:
        return abort();
    }
}

bool sdvm_compiler_x64_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_compiler_t *compiler = state->compiler;

    sdvm_compilerLocation_t *dest = &instruction->destinationLocation;
    sdvm_compilerLocation_t *arg0 = &instruction->arg0Location;
    sdvm_compilerLocation_t *arg1 = &instruction->arg1Location;

    switch(instruction->decoding.opcode)
    {
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
    case SdvmInstArgFloat64:

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
    case SdvmInstCallArgFloat64:
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
    case SdvmInstReturnFloatVector128:
    case SdvmInstReturnIntegerVector128:
    case SdvmInstReturnFloatVector256:
    case SdvmInstReturnIntegerVector256:
        sdvm_compiler_x64_emitFunctionEpilogue(state);
        sdvm_compiler_x86_ret(compiler);
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
    case SdvmInstCallFloatVector128:
    case SdvmInstCallIntegerVector128:
    case SdvmInstCallFloatVector256:
    case SdvmInstCallIntegerVector256:
        if(arg0->kind == SdvmCompLocationGlobalSymbolValue)
            sdvm_compiler_x86_callGsv(compiler, arg0->symbolHandle, 0);
        else if(arg0->kind == SdvmCompLocationLocalSymbolValue)
            sdvm_compiler_x86_callLsv(compiler, arg0->symbolHandle, arg0->symbolOffset);
        else
            sdvm_compiler_x86_callReg(compiler, arg0->firstRegister.value);
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
    case SdvmInstCallClosureFloatVector128:
    case SdvmInstCallClosureIntegerVector128:
    case SdvmInstCallClosureFloatVector256:
    case SdvmInstCallClosureIntegerVector256:
        sdvm_compiler_x86_callRmo(compiler, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadInt16:
        sdvm_compiler_x86_movsxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt16:
        sdvm_compiler_x86_movzxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadInt32:
    case SdvmInstLoadUInt32:
        sdvm_compiler_x86_mov32RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadInt64:
    case SdvmInstLoadUInt64:
    case SdvmInstLoadPointer:
        sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadGCPointer:
        sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        sdvm_compiler_x86_mov64RegRmo(compiler, dest->secondRegister.value, arg0->firstRegister.value, 8);
        return true;

    case SdvmInstStoreInt16:
    case SdvmInstStoreUInt16:
        sdvm_compiler_x86_mov16RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;

    case SdvmInstStoreInt32:
    case SdvmInstStoreUInt32:
        sdvm_compiler_x86_mov32RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;

    case SdvmInstStoreInt64:
    case SdvmInstStoreUInt64:
        sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;

    case SdvmInstInt16Add:
    case SdvmInstUInt16Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add16RegImm16(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_add16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Sub:
    case SdvmInstUInt16Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sub16RegImm16(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_sub16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16And:
    case SdvmInstUInt16And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_and16RegImm16(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_and16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Or:
    case SdvmInstUInt16Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_or16RegImm16(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_or16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Xor:
    case SdvmInstUInt16Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_xor16RegImm16(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_xor16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt32Add:
    case SdvmInstUInt32Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add32RegImm32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_add32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Sub:
    case SdvmInstUInt32Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sub32RegImm32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_sub32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32And:
    case SdvmInstUInt32And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_and32RegImm32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_and32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Or:
    case SdvmInstUInt32Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_or32RegImm32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_or32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Xor:
    case SdvmInstUInt32Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_xor32RegImm32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_xor32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt64Add:
    case SdvmInstUInt64Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_add64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64Sub:
    case SdvmInstUInt64Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sub64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_sub64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64And:
    case SdvmInstUInt64And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_and64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_and64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64Or:
    case SdvmInstUInt64Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_or64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_or64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64Xor:
    case SdvmInstUInt64Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_xor64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_xor64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    default:
        abort();
    }
    return true;
}

void sdvm_compiler_x64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        // Emit the label, if this is a label.
        if(instruction->decoding.opcode == SdvmConstLabel)
        {
            sdvm_compiler_setLabelAtSectionEnd(state->compiler, instruction->location.immediateLabel, &state->compiler->textSection);
        }

        return;
    }

    // Emit the argument moves.
    if(instruction->decoding.arg0IsInstruction)
    {
        sdvm_compilerInstruction_t *arg0 = state->instructions + instruction->decoding.instruction.arg0;
        sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &arg0->location, &instruction->arg0Location);
    }

    if(instruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + instruction->decoding.instruction.arg1;
        sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &arg1->location, &instruction->arg1Location);
    }

    // Emit the actual instruction operation
    if(!sdvm_compiler_x64_emitFunctionInstructionOperation(state, instruction))
        return;

    // Emit the result moves.
    sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &instruction->destinationLocation, &instruction->location);
}

void sdvm_compiler_x64_emitFunctionInstructions(sdvm_functionCompilationState_t *state)
{
    for(uint32_t i = 0; i < state->instructionCount; ++i)
        sdvm_compiler_x64_emitFunctionInstruction(state, state->instructions + i);
}

#pragma endregion X86_CodeGeneration

void sdvm_compiler_x64_allocateFunctionRegisters(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    
    sdvm_linearScanRegisterAllocatorFile_t integerRegisterFile = {
        .allocatableRegisterCount = convention->allocatableIntegerRegisterCount,
        .allocatableRegisters = convention->allocatableIntegerRegisters
    };

    sdvm_linearScanRegisterAllocatorFile_t vectorRegisterFile = {
        .allocatableRegisterCount = convention->allocatableFloatRegisterCount,
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

void sdvm_compiler_x64_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_allocateFunctionSpillLocations(state);
}

void sdvm_compiler_x64_computeFunctionStackLayout(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;

    state->requiresStackFrame = state->hasCallout
        || !sdvm_registerSet_isEmpty(&state->usedCallPreservedIntegerRegisterSet)
        || !sdvm_registerSet_isEmpty(&state->usedCallPreservedVectorRegisterSet)
        || state->gcSpillingStackSegment.size > 0
        || state->spillingStackSegment.size > 0
        || state->calloutStackSegment.size > 0;

    uint32_t pointerSize = state->compiler->pointerSize;
    state->prologueStackSegment.size = pointerSize;
    state->prologueStackSegment.alignment = 16;

    if(state->requiresStackFrame)
    {
        // Frame pointer.
        state->prologueStackSegment.size += pointerSize;
    }

    sdvm_compiler_computeStackSegmentLayouts(state);

    if(state->requiresStackFrame)
    {
        state->stackFrameRegister = SDVM_X86_RBP;
        state->stackFramePointerAnchorOffset = pointerSize * 2;

        // Preserved integer registers.
        for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
        {
            if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, convention->callPreservedIntegerRegisters[i]))
                state->prologueStackSegment.size += pointerSize;
        }

        // Preserved vector registers.
        for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
        {
            if(sdvm_registerSet_includes(&state->usedCallPreservedVectorRegisterSet, convention->callPreservedVectorRegisters[i]))
            {
                state->vectorCallPreservedRegisterStackSegment.alignment = 16;
                state->vectorCallPreservedRegisterStackSegment.size += 16;
            }
        }
    }
    else
    {
        state->stackFrameRegister = SDVM_X86_RSP;
        state->stackFramePointerAnchorOffset = state->calloutStackSegment.endOffset;
    }

    sdvm_compiler_computeStackFrameOffsets(state);
}

bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_x64_computeFunctionLocationConstraints(state);
    sdvm_compiler_x64_allocateFunctionRegisters(state);
    sdvm_compiler_x64_allocateFunctionSpillLocations(state);
    sdvm_compiler_x64_computeFunctionStackLayout(state);

    sdvm_functionCompilationState_dump(state);
    sdvm_compiler_x64_emitFunctionPrologue(state);
    sdvm_compiler_x64_emitFunctionInstructions(state);
    return true;
}

uint32_t sdvm_compiler_x64_mapElfRelocation(sdvm_compilerRelocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompRelocationAbsolute8: return SDVM_R_X86_64_8;
    case SdvmCompRelocationAbsolute16: return SDVM_R_X86_64_16;
    case SdvmCompRelocationAbsolute32: return SDVM_R_X86_64_32;
    case SdvmCompRelocationAbsolute64: return SDVM_R_X86_64_64;
    case SdvmCompRelocationRelative32: return SDVM_R_X86_64_PC32;
    case SdvmCompRelocationRelative32AtGot: return SDVM_R_X86_64_GOTPCREL;
    case SdvmCompRelocationRelative32AtPlt: return SDVM_R_X86_64_PLT32;
    case SdvmCompRelocationRelative64: return SDVM_R_X86_64_PC64;
    default: abort();
    }
}

static sdvm_compilerTarget_t sdvm_compilerTarget_x64_linux_pie = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_X86_64,
    .usesUnderscorePrefix = false,

    .defaultCC = &sdvm_x64_sysv_callingConvention,
    .cdecl = &sdvm_x64_sysv_callingConvention,
    .stdcall = &sdvm_x64_sysv_callingConvention,
    .apicall = &sdvm_x64_sysv_callingConvention,
    .thiscall = &sdvm_x64_sysv_callingConvention,
    .vectorcall = &sdvm_x64_sysv_callingConvention,

    .compileModuleFunction = sdvm_compiler_x64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_x64_mapElfRelocation,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_x64_linux()
{
    return &sdvm_compilerTarget_x64_linux_pie;
}
