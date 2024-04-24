#include "compilerAArch64.h"
#include "assert.h"
#include "module.h"
#include "elf.h"
#include "coff.h"
#include "macho.h"
#include "dwarf.h"
#include "utils.h"
#include <string.h>

void sdvm_compiler_aarch64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state);


#define SDVM_AARCH64_REG_DEF(regKind, regSize, name, regValue) const sdvm_compilerRegister_t sdvm_aarch64_ ## name = {\
    .kind = SdvmCompRegisterKind ## regKind, \
    .size = regSize, \
    .value = regValue, \
};
#include "aarch64Regs.inc"
#undef SDVM_ARCH64_REG_DEF

static const sdvm_compilerRegister_t *sdvm_aarch64_eabi_integerPassingRegisters[] = {
    &sdvm_aarch64_X0, &sdvm_aarch64_X1, &sdvm_aarch64_X2, &sdvm_aarch64_X3,
    &sdvm_aarch64_X4, &sdvm_aarch64_X5, &sdvm_aarch64_X6, &sdvm_aarch64_X7,
};
static const uint32_t sdvm_aarch64_eabi_integerPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_integerPassingRegisters);

static const sdvm_compilerRegister_t *sdvm_aarch64_eabi_integerPassingDwordRegisters[] = {
    &sdvm_aarch64_W0, &sdvm_aarch64_W1, &sdvm_aarch64_W2, &sdvm_aarch64_W3,
    &sdvm_aarch64_W4, &sdvm_aarch64_W5, &sdvm_aarch64_W6, &sdvm_aarch64_W7,
};
static const uint32_t sdvm_aarch64_eabi_integerPassingDwordRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_integerPassingDwordRegisters);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_eabi_allocatableIntegerRegisters[] = {
    // Temporary registers
    SDVM_AARCH64_X11, SDVM_AARCH64_X12, SDVM_AARCH64_X13, SDVM_AARCH64_X14, SDVM_AARCH64_X15,

    // Intra procedure temporary registers.
    SDVM_AARCH64_X16, SDVM_AARCH64_X17,

    // Argument registers
    SDVM_AARCH64_X0, SDVM_AARCH64_X1, SDVM_AARCH64_X2, SDVM_AARCH64_X3,
    SDVM_AARCH64_X4, SDVM_AARCH64_X5, SDVM_AARCH64_X6, SDVM_AARCH64_X7,

    SDVM_AARCH64_X9, // Temporary / Closure pointer
    SDVM_AARCH64_X10, // Closure GC pointer

    // Call preserved registers.
    SDVM_AARCH64_X19, SDVM_AARCH64_X20, SDVM_AARCH64_X21, SDVM_AARCH64_X22,
    SDVM_AARCH64_X23, SDVM_AARCH64_X24, SDVM_AARCH64_X25, SDVM_AARCH64_X26,
    SDVM_AARCH64_X27, SDVM_AARCH64_X28,
    
};
static const uint32_t sdvm_aarch64_eabi_allocatableIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_allocatableIntegerRegisters);

static const sdvm_compilerRegister_t *sdvm_aarch64_eabi_vectorFloatPassingRegister[] = {
    &sdvm_aarch64_V0,  &sdvm_aarch64_V1,  &sdvm_aarch64_V2,  &sdvm_aarch64_V3,
    &sdvm_aarch64_V4,  &sdvm_aarch64_V5,  &sdvm_aarch64_V6,  &sdvm_aarch64_V7,
};
static const uint32_t sdvm_aarch64_eabi_vectorFloatPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_vectorFloatPassingRegister);

static const sdvm_compilerRegister_t *sdvm_aarch64_eabi_vectorIntegerPassingRegister[] = {
    &sdvm_aarch64_VI0,  &sdvm_aarch64_VI1,  &sdvm_aarch64_VI2,  &sdvm_aarch64_VI3,
    &sdvm_aarch64_VI4,  &sdvm_aarch64_VI5,  &sdvm_aarch64_VI6,  &sdvm_aarch64_VI7,
};
static const uint32_t sdvm_aarch64_eabi_vectorIntegerPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_vectorIntegerPassingRegister);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_eabi_callPreservedIntegerRegisters[] = {
    SDVM_AARCH64_X19, SDVM_AARCH64_X20, SDVM_AARCH64_X21, SDVM_AARCH64_X22,
    SDVM_AARCH64_X23, SDVM_AARCH64_X24, SDVM_AARCH64_X25, SDVM_AARCH64_X26,
    SDVM_AARCH64_X27, SDVM_AARCH64_X28,

    SDVM_AARCH64_FP, SDVM_AARCH64_LR, SDVM_AARCH64_SP,
};
static const uint32_t sdvm_aarch64_eabi_callPreservedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_callPreservedIntegerRegisters);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_eabi_callTouchedIntegerRegisters[] = {
    SDVM_AARCH64_X0, SDVM_AARCH64_X1, SDVM_AARCH64_X2, SDVM_AARCH64_X3,
    SDVM_AARCH64_X4, SDVM_AARCH64_X5, SDVM_AARCH64_X6, SDVM_AARCH64_X7,
    SDVM_AARCH64_X8, SDVM_AARCH64_X9, SDVM_AARCH64_X10, SDVM_AARCH64_X11,
    SDVM_AARCH64_X12, SDVM_AARCH64_X13, SDVM_AARCH64_X14, SDVM_AARCH64_X15,
    SDVM_AARCH64_X16, SDVM_AARCH64_X17,
};
static const uint32_t sdvm_aarch64_eabi_callTouchedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_callTouchedIntegerRegisters);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_eabi_callTouchedVectorRegisters[] = {
    SDVM_AARCH64_V0,  SDVM_AARCH64_V1,  SDVM_AARCH64_V2,  SDVM_AARCH64_V3,
    SDVM_AARCH64_V4,  SDVM_AARCH64_V5,  SDVM_AARCH64_V6,  SDVM_AARCH64_V7,
    SDVM_AARCH64_V16, SDVM_AARCH64_V17,  SDVM_AARCH64_V18, SDVM_AARCH64_V19,
    SDVM_AARCH64_V20, SDVM_AARCH64_V21, SDVM_AARCH64_V22, SDVM_AARCH64_V23,
    SDVM_AARCH64_V24, SDVM_AARCH64_V25, SDVM_AARCH64_V26, SDVM_AARCH64_V27,
    SDVM_AARCH64_V28, SDVM_AARCH64_V29, SDVM_AARCH64_V30, SDVM_AARCH64_V31,
};
static const uint32_t sdvm_aarch64_eabi_callTouchedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_callTouchedVectorRegisters);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_eabi_callPreservedVectorRegisters[] = {
    SDVM_AARCH64_V8,  SDVM_AARCH64_V9,  SDVM_AARCH64_V10, SDVM_AARCH64_V11,
    SDVM_AARCH64_V12, SDVM_AARCH64_V13, SDVM_AARCH64_V14, SDVM_AARCH64_V15,
};
static const uint32_t sdvm_aarch64_eabi_callPreservedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_callPreservedVectorRegisters);

static const sdvm_compilerRegisterValue_t sdvm_aarch64_allocatableVectorRegisters[] = {
    SDVM_AARCH64_V0,  SDVM_AARCH64_V1,  SDVM_AARCH64_V2,  SDVM_AARCH64_V3,
    SDVM_AARCH64_V4,  SDVM_AARCH64_V5,  SDVM_AARCH64_V6,  SDVM_AARCH64_V7,
    SDVM_AARCH64_V8,  SDVM_AARCH64_V9,  SDVM_AARCH64_V10, SDVM_AARCH64_V11,
    SDVM_AARCH64_V12, SDVM_AARCH64_V13, SDVM_AARCH64_V14, SDVM_AARCH64_V15,
    SDVM_AARCH64_V16, SDVM_AARCH64_V17,  SDVM_AARCH64_V18, SDVM_AARCH64_V19,
    SDVM_AARCH64_V20, SDVM_AARCH64_V21, SDVM_AARCH64_V22, SDVM_AARCH64_V23,
    SDVM_AARCH64_V24, SDVM_AARCH64_V25, SDVM_AARCH64_V26, SDVM_AARCH64_V27,
    SDVM_AARCH64_V28, SDVM_AARCH64_V29, SDVM_AARCH64_V30, SDVM_AARCH64_V31,
};
static const uint32_t sdvm_aarch64_allocatableVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_allocatableVectorRegisters);

const sdvm_compilerCallingConvention_t sdvm_aarch64_eabi_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 8,
    .integerRegisterCount = sdvm_aarch64_eabi_integerPassingRegisterCount,

    .integer32Registers = sdvm_aarch64_eabi_integerPassingDwordRegisters,
    .integer64Registers = sdvm_aarch64_eabi_integerPassingRegisters,
    .integerRegisters = sdvm_aarch64_eabi_integerPassingRegisters,

    .closureRegister = &sdvm_aarch64_X9,
    .closureGCRegister = &sdvm_aarch64_X10,

    .firstInteger32ResultRegister = &sdvm_aarch64_W0,
    .firstInteger64ResultRegister = &sdvm_aarch64_X0,
    .firstIntegerResultRegister = &sdvm_aarch64_X0,
    .secondInteger32ResultRegister = &sdvm_aarch64_W1,
    .secondInteger64ResultRegister = &sdvm_aarch64_X1,
    .secondIntegerResultRegister = &sdvm_aarch64_X1,

    .vectorRegisterSize = 16,
    .vectorRegisterCount = sdvm_aarch64_eabi_vectorFloatPassingRegisterCount,
    .vectorFloatRegisters = sdvm_aarch64_eabi_vectorFloatPassingRegister,
    .vectorIntegerRegisters = sdvm_aarch64_eabi_vectorIntegerPassingRegister,

    .firstVectorFloatResultRegister = &sdvm_aarch64_V0,
    .firstVectorIntegerResultRegister = &sdvm_aarch64_VI0,
    .secondVectorFloatResultRegister = &sdvm_aarch64_V1,
    .secondVectorIntegerResultRegister = &sdvm_aarch64_VI1,

    .allocatableIntegerRegisterCount = sdvm_aarch64_eabi_allocatableIntegerRegisterCount,
    .allocatableIntegerRegisters = sdvm_aarch64_eabi_allocatableIntegerRegisters,
    
    .allocatableVectorRegisterCount = sdvm_aarch64_allocatableVectorRegisterCount,
    .allocatableVectorRegisters = sdvm_aarch64_allocatableVectorRegisters,

    .callPreservedIntegerRegisterCount = sdvm_aarch64_eabi_callPreservedIntegerRegisterCount,
    .callPreservedIntegerRegisters = sdvm_aarch64_eabi_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = sdvm_aarch64_eabi_callTouchedIntegerRegisterCount,
    .callTouchedIntegerRegisters = sdvm_aarch64_eabi_callTouchedIntegerRegisters,

    .callTouchedVectorRegisterCount = sdvm_aarch64_eabi_callTouchedVectorRegisterCount,
    .callTouchedVectorRegisters = sdvm_aarch64_eabi_callTouchedVectorRegisters,

    .callPreservedVectorRegisterCount = sdvm_aarch64_eabi_callPreservedVectorRegisterCount,
    .callPreservedVectorRegisters = sdvm_aarch64_eabi_callPreservedVectorRegisters
};

const sdvm_compilerCallingConvention_t sdvm_aarch64_apple_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,
    .nonFixedVariadicArgumentsArePassedViaStack = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 8,
    .integerRegisterCount = sdvm_aarch64_eabi_integerPassingRegisterCount,

    .integer32Registers = sdvm_aarch64_eabi_integerPassingDwordRegisters,
    .integer64Registers = sdvm_aarch64_eabi_integerPassingRegisters,
    .integerRegisters = sdvm_aarch64_eabi_integerPassingRegisters,

    .closureRegister = &sdvm_aarch64_X9,
    .closureGCRegister = &sdvm_aarch64_X10,

    .firstInteger32ResultRegister = &sdvm_aarch64_W0,
    .firstInteger64ResultRegister = &sdvm_aarch64_X0,
    .firstIntegerResultRegister = &sdvm_aarch64_X0,
    .secondInteger32ResultRegister = &sdvm_aarch64_W1,
    .secondInteger64ResultRegister = &sdvm_aarch64_X1,
    .secondIntegerResultRegister = &sdvm_aarch64_X1,

    .vectorRegisterSize = 16,
    .vectorRegisterCount = sdvm_aarch64_eabi_vectorFloatPassingRegisterCount,
    .vectorFloatRegisters = sdvm_aarch64_eabi_vectorFloatPassingRegister,
    .vectorIntegerRegisters = sdvm_aarch64_eabi_vectorIntegerPassingRegister,

    .firstVectorFloatResultRegister = &sdvm_aarch64_V0,
    .firstVectorIntegerResultRegister = &sdvm_aarch64_VI0,
    .secondVectorFloatResultRegister = &sdvm_aarch64_V1,
    .secondVectorIntegerResultRegister = &sdvm_aarch64_VI1,

    .allocatableIntegerRegisterCount = sdvm_aarch64_eabi_allocatableIntegerRegisterCount,
    .allocatableIntegerRegisters = sdvm_aarch64_eabi_allocatableIntegerRegisters,
    
    .allocatableVectorRegisterCount = sdvm_aarch64_allocatableVectorRegisterCount,
    .allocatableVectorRegisters = sdvm_aarch64_allocatableVectorRegisters,

    .callPreservedIntegerRegisterCount = sdvm_aarch64_eabi_callPreservedIntegerRegisterCount,
    .callPreservedIntegerRegisters = sdvm_aarch64_eabi_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = sdvm_aarch64_eabi_callTouchedIntegerRegisterCount,
    .callTouchedIntegerRegisters = sdvm_aarch64_eabi_callTouchedIntegerRegisters,

    .callTouchedVectorRegisterCount = sdvm_aarch64_eabi_callTouchedVectorRegisterCount,
    .callTouchedVectorRegisters = sdvm_aarch64_eabi_callTouchedVectorRegisters,

    .callPreservedVectorRegisterCount = sdvm_aarch64_eabi_callPreservedVectorRegisterCount,
    .callPreservedVectorRegisters = sdvm_aarch64_eabi_callPreservedVectorRegisters
};

bool sdvm_compiler_aarch64_isValidWideImmediate32(uint32_t value)
{
    return
        value == (value & 0x0000FFFF) ||
        value == (value & 0xFFFF0000);
}

uint8_t sdvm_compiler_aarch64_computeWideImmediate32HW(uint32_t value)
{
    if(value == (value & 0x0000FFFF)) return 0;
    return 1;
}

bool sdvm_compiler_aarch64_isValidInvertedWideImmediate32(uint32_t value)
{
    return sdvm_compiler_aarch64_isValidWideImmediate32(~value);
}

bool sdvm_compiler_aarch64_isValidWideImmediate64(uint64_t value)
{
    return
        value == (value & 0x000000000000FFFF) ||
        value == (value & 0x00000000FFFF0000) ||
        value == (value & 0x0000FFFF00000000) ||
        value == (value & 0xFFFF000000000000);
}

uint8_t sdvm_compiler_aarch64_computeWideImmediate64HW(uint32_t value)
{
    if(value == (value & 0x000000000000FFFF)) return 0;
    if(value == (value & 0x00000000FFFF0000)) return 0;
    if(value == (value & 0x0000FFFF00000000)) return 0;
    return 3;
}

bool sdvm_compiler_aarch64_isValidInvertedWideImmediate64(uint32_t value)
{
    return sdvm_compiler_aarch64_isValidWideImmediate64(~value);
}

void sdvm_compiler_aarch64_alignUnreacheableCode(sdvm_compiler_t *compiler)
{
    if(compiler->textSection.alignment < 4)
        compiler->textSection.alignment = 4;
}

sdvm_aarch64_condition_t sdvm_compiler_aarch64_mapConditionCode(bool isSigned, sdvm_baseOpcode_t condition)
{
    switch(condition)
    {
    case SdvmOpEquals: return SDVM_AARCH64_EQ;
    case SdvmOpNotEquals: return SDVM_AARCH64_NE;
    case SdvmOpLessThan:
        if(isSigned)
            return SDVM_AARCH64_LT;
        else
            return SDVM_AARCH64_MI;
    case SdvmOpLessOrEquals:
        if(isSigned)
            return SDVM_AARCH64_LE;
        else
            return SDVM_AARCH64_LS;
    case SdvmOpGreaterThan:
        if(isSigned)
            return SDVM_AARCH64_GT;
        else
            return SDVM_AARCH64_HI;
    case SdvmOpGreaterOrEquals:
        if(isSigned)
            return SDVM_AARCH64_GE;
        else
            return SDVM_AARCH64_PL;
    default: abort();
    }
}

size_t sdvm_compiler_aarch64_addInstruction(sdvm_compiler_t *compiler, uint32_t instruction)
{
    size_t offset = compiler->textSection.contents.size;
    sdvm_compiler_addInstructionBytes(compiler, 4, &instruction);
    return offset;
}

#pragma region GeneralPurposeInstructions
void sdvm_compiler_aarch64_b_cond(sdvm_compiler_t *compiler, sdvm_aarch64_condition_t cond, uint32_t imm19)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x54000000 | (imm19 << 5) | cond);
}

void sdvm_compiler_aarch64_b_cond_label(sdvm_compiler_t *compiler, sdvm_aarch64_condition_t cond, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, 0x54000000 | cond, SdvmCompRelocationAArch64Jump19, label, 0);
}

void sdvm_compiler_aarch64_b(sdvm_compiler_t *compiler, uint32_t imm26)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x14000000 | imm26);
}

void sdvm_compiler_aarch64_b_label(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_addInstruction32WithLabelValue(compiler, 0x14000000, SdvmCompRelocationAArch64Jump26, label, 0);
}

void sdvm_compiler_aarch64_b_sv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationAArch64Jump26, symbolHandle, addend);
    sdvm_compiler_aarch64_b(compiler, 0);
}

void sdvm_compiler_aarch64_bl(sdvm_compiler_t *compiler, uint32_t imm26)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x94000000 | imm26);
}

void sdvm_compiler_aarch64_bl_sv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationAArch64Call26, symbolHandle, addend);
    sdvm_compiler_aarch64_bl(compiler, 0);
}

void sdvm_compiler_aarch64_blr(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rn)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xD63F0000 | (Rn << 5));
}

void sdvm_compiler_aarch64_ret(sdvm_compiler_t *compiler)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xD65F0000 | (SDVM_AARCH64_X30 << 5));
}

void sdvm_compiler_aarch64_brk(sdvm_compiler_t *compiler, uint16_t imm16)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xD4200000 | (imm16 << 5));
}

void sdvm_compiler_aarch64_adrp(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, uint32_t imm)
{
    uint32_t immlo = imm & 3;
    uint32_t immhi = imm >> 2;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x90000000 | (immhi << 5) | (immlo << 29) | Rd);
}

void sdvm_compiler_aarch64_add_extended(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_extendOption_t extend, uint8_t shift)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB200000 | Rd | (Rn << 5) | (shift << 10) | (extend << 13) | (Rm << 16) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_add_shifted(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_shiftType_t shift, uint8_t amount)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB000000 | Rd | (Rn << 5) | (amount << 10) | (Rm << 16) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_sub_immediate(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, uint16_t imm12, sdvm_aarch64_immediateShiftType_t shift)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x51000000 | Rd | (Rn << 5) | (imm12 << 10) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_sub_extended(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_extendOption_t extend, uint8_t shift)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x4B200000 | Rd | (Rn << 5) | (shift << 10) | (extend << 13) | (Rm << 16) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_sub_shifted(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_shiftType_t shift, uint8_t amount)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x4B000000 | Rd | (Rn << 5) | (amount << 10) | (Rm << 16) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_add_immediate(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, uint16_t imm12, sdvm_aarch64_immediateShiftType_t shift)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x11000000 | Rd | (Rn << 5) | (imm12 << 10) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_cmp_shifted(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_shiftType_t shift, uint8_t amount)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x6B00001F | (Rn << 5) | (amount << 10) | (Rm << 16) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_cset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_aarch64_condition_t condition)
{
    uint8_t invertedCondition = condition ^ 1;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x1A9F07E0 | Rd | (invertedCondition << 12) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_tst_shifted(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm, sdvm_aarch64_shiftType_t shift, uint8_t amount)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x6A00001F | (Rn << 5) | (amount << 10) | (Rm << 16) | (shift << 22) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_adrl_sv(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rd, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend)
{
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationAArch64AdrRelativePageHi21, symbolHandle, addend);
    sdvm_compiler_aarch64_adrp(compiler, Rd, 0);
    sdvm_compiler_addInstructionRelocation(compiler, SdvmCompRelocationAArch64AddAbsoluteLo12NoCheck, symbolHandle, addend);
    sdvm_compiler_aarch64_add_immediate(compiler, true, Rd, Rd, 0, 0);
}

void sdvm_compiler_aarch64_mov_sp(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t destination, sdvm_compilerRegisterValue_t source)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x11000000 | destination | (source << 5) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_mov_noopt(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t destination, sdvm_compilerRegisterValue_t source)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x2A0003E0 | destination | (source << 16) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_mov(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t destination, sdvm_compilerRegisterValue_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_aarch64_mov_noopt(compiler, sf, destination, source);
}

void sdvm_compiler_aarch64_mov_wideImmediate(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t destination, uint8_t hw, uint16_t imm16)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x52800000 | destination | (hw << 21) | (imm16 << 5) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_mov_invertedWideImmediate(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t destination, uint8_t hw, uint16_t imm16)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x12800000 | destination | (hw << 21) | (imm16 << 5) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_mov_imm32(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t destination, uint32_t value)
{
    if(value == 0)
        return sdvm_compiler_aarch64_mov(compiler, false, destination, SDVM_AARCH64_WZR);

    if(sdvm_compiler_aarch64_isValidWideImmediate32(value))
    {
        uint8_t hw = sdvm_compiler_aarch64_computeWideImmediate32HW(value);
        sdvm_compiler_aarch64_mov_wideImmediate(compiler, false, destination, hw, (uint16_t) (value >> (hw*16)));
        return;
    }

    if(sdvm_compiler_aarch64_isValidWideImmediate32(~value))
    {
        uint32_t invertedValue = ~value;
        uint8_t hw = sdvm_compiler_aarch64_computeWideImmediate32HW(invertedValue);
        sdvm_compiler_aarch64_mov_invertedWideImmediate(compiler, false, destination, hw, (uint16_t) (invertedValue >> (hw*16)));
        return;
    }

    abort();
}

void sdvm_compiler_aarch64_movImm64(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t destination, uint32_t value)
{
    if(value == 0)
        return sdvm_compiler_aarch64_mov(compiler, false, destination, SDVM_AARCH64_XZR);

    if(sdvm_compiler_aarch64_isValidWideImmediate64(value))
    {
        uint8_t hw = sdvm_compiler_aarch64_computeWideImmediate64HW(value);
        sdvm_compiler_aarch64_mov_wideImmediate(compiler, true, destination, hw, (uint16_t) (value >> (hw*16)));
        return;
    }

    if(sdvm_compiler_aarch64_isValidWideImmediate64(~value))
    {
        uint32_t invertedValue = ~value;
        uint8_t hw = sdvm_compiler_aarch64_computeWideImmediate64HW(invertedValue);
        sdvm_compiler_aarch64_mov_wideImmediate(compiler, true, destination, hw, (uint16_t) (invertedValue >> (hw*16)));
        return;
    }

    abort();
}

void sdvm_compiler_aarch64_mul(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x1B007C00 | Rd | (Rn << 5) | (Rm << 16) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_ldp_postIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x28C00000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_ldp_preIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x29C00000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_ldp_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x29400000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_ldr_postIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint16_t imm9 = offset & 511;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB8400400 | Rt | (Rn << 5) | (imm9 << 12) | (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_ldr_preIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint16_t imm9 = offset & 511;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB8400C00 | Rt | (Rn << 5) | (imm9 << 12) | (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_ldr_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = (sf ? (offset / 8) : (offset /4)) & 4095;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB9400000 | Rt | (Rn << 5) | (imm12 << 10)| (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_ldrh_offset(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset / 2;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x79400000 | Rt | (Rn << 5) | (imm12 << 10));
}

void sdvm_compiler_aarch64_ldrb_offset(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x39400000 | Rt | (Rn << 5) | (imm12 << 10));
}

void sdvm_compiler_aarch64_ldrsh_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset / 2;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x79800000 | Rt | (Rn << 5) | (imm12 << 10)| (sf ? (1<<22) : 0));
}

void sdvm_compiler_aarch64_ldrsb_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x39800000 | Rt | (Rn << 5) | (imm12 << 10)| (sf ? (1<<22) : 0));
}

void sdvm_compiler_aarch64_stp_postIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x28800000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_stp_preIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x29800000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_stp_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt1, sdvm_compilerRegisterValue_t Rt2, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint8_t imm7 = (sf ? (offset / 8) : offset / 4) & 127;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x29000000 | Rt1 | (Rn << 5) | (Rt2 << 10) | (imm7 << 15) | (sf ? (1<<31) : 0));
}

void sdvm_compiler_aarch64_str_postIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint16_t imm9 = offset & 511;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB8000400 | Rt | (Rn << 5) | (imm9 << 12) | (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_str_preIndex(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, int16_t offset)
{
    uint16_t imm9 = offset & 511;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB8000C00 | Rt | (Rn << 5) | (imm9 << 12) | (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_str_offset(sdvm_compiler_t *compiler, bool sf, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = (sf ? (offset / 8) : (offset /4)) & 4095;
    sdvm_compiler_aarch64_addInstruction(compiler, 0xB9000000 | Rt | (Rn << 5) | (imm12 << 10)| (sf ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_strb_offset(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset & 4095;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x39000000 | Rt | (Rn << 5) | (imm12 << 10));
}

void sdvm_compiler_aarch64_strh_offset(sdvm_compiler_t *compiler, sdvm_compilerRegisterValue_t Rt, sdvm_compilerRegisterValue_t Rn, uint16_t offset)
{
    uint16_t imm12 = offset & 4095;
    sdvm_compiler_aarch64_addInstruction(compiler, 0x79000000 | Rt | (Rn << 5) | (imm12 << 10));
}

#pragma endregion GeneralPurposeInstructions

#pragma region SIMDInstructions

void sdvm_compiler_aarch64_simd_fadd_scalar(sdvm_compiler_t *compiler, sdvm_aarch64_simd_float_type_t type, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0x1E202800 | Rd | (Rn << 5) | (Rm << 16) | (type << 22));
}

void sdvm_compiler_aarch64_simd_orr_vector_register(sdvm_compiler_t *compiler, bool Q, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn, sdvm_compilerRegisterValue_t Rm)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xEA01C00 | Rd | (Rn << 5) | (Rm << 16) | (Q ? (1<<30) : 0));
}

void sdvm_compiler_aarch64_simd_mov_vector(sdvm_compiler_t *compiler, bool Q, sdvm_compilerRegisterValue_t Rd, sdvm_compilerRegisterValue_t Rn)
{
    if(Rd == Rn)
        return;

    sdvm_compiler_aarch64_simd_orr_vector_register(compiler, Q, Rd, Rn, Rn);
}

#pragma endregion SIMDInstructions

static sdvm_compilerInstructionPatternTable_t sdvm_aarch64_instructionPatternTable = {
};

sdvm_compilerLocation_t sdvm_compilerLocation_aarch64_immediateS32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_aarch64_isValidWideImmediate32(value) || sdvm_compiler_aarch64_isValidWideImmediate32(~value))
        return sdvm_compilerLocation_immediateS32(value);
    else
        return sdvm_compilerLocation_constSectionS32(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_aarch64_immediateU32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_aarch64_isValidWideImmediate32(value) || sdvm_compiler_aarch64_isValidWideImmediate32(~value))
        return sdvm_compilerLocation_immediateU32(value);
    else
        return sdvm_compilerLocation_constSectionU32(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_aarch64_immediateS64(sdvm_compiler_t *compiler, int64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_aarch64_isValidWideImmediate64(value))
        return sdvm_compilerLocation_immediateS64(value);
    else
        return sdvm_compilerLocation_constSectionS64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_aarch64_immediateU64(sdvm_compiler_t *compiler, uint64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else if(sdvm_compiler_aarch64_isValidWideImmediate64(value))
        return sdvm_compilerLocation_immediateU64(value);
    else
        return sdvm_compilerLocation_constSectionU64(compiler, value);
}

void sdvm_compiler_aarch64_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_aarch64_immediateS32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstUInt32:
            instruction->location = sdvm_compilerLocation_aarch64_immediateU32(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64SExt:
        case SdvmConstUInt64SExt:
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_aarch64_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
        case SdvmConstUInt64ZExt:
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_aarch64_immediateU64(state->compiler, instruction->decoding.constant.unsignedPayload);
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
    case SdvmInstUInt32Min:
    case SdvmInstUInt32Max:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstInt64Add:
    case SdvmInstInt64Sub:
    case SdvmInstInt64Mul:
    case SdvmInstInt64Div:
    case SdvmInstInt64UDiv:
    case SdvmInstInt64And:
    case SdvmInstInt64Or:
    case SdvmInstInt64Xor:
    case SdvmInstInt64Min:
    case SdvmInstInt64Max:
    case SdvmInstUInt64Add:
    case SdvmInstUInt64Sub:
    case SdvmInstUInt64Mul:
    case SdvmInstUInt64Div:
    case SdvmInstUInt64UDiv:
    case SdvmInstUInt64And:
    case SdvmInstUInt64Or:
    case SdvmInstUInt64Xor:
    case SdvmInstUInt64Min:
    case SdvmInstUInt64Max:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstFloat32Add:
    case SdvmInstFloat32Sub:
    case SdvmInstFloat32Mul:
    case SdvmInstFloat32Div:
    case SdvmInstFloat32Min:
    case SdvmInstFloat32Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstFloat32Sqrt:
    case SdvmInstFloat32Floor:
    case SdvmInstFloat32Ceil:
    case SdvmInstFloat32Round:
    case SdvmInstFloat32Truncate:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstFloat64Add:
    case SdvmInstFloat64Sub:
    case SdvmInstFloat64Mul:
    case SdvmInstFloat64Div:
    case SdvmInstFloat64Min:
    case SdvmInstFloat64Max:
    case SdvmInstFloat32x2Add:
    case SdvmInstFloat32x2Sub:
    case SdvmInstFloat32x2Mul:
    case SdvmInstFloat32x2Div:
    case SdvmInstFloat32x2Min:
    case SdvmInstFloat32x2Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->allowArg0DestinationShare = true;
        instruction->allowArg1DestinationShare = true;
        return;

    case SdvmInstFloat64Sqrt:
    case SdvmInstFloat64Floor:
    case SdvmInstFloat64Ceil:
    case SdvmInstFloat64Round:
    case SdvmInstFloat64Truncate:
    case SdvmInstFloat32x2Sqrt:
    case SdvmInstFloat32x2Floor:
    case SdvmInstFloat32x2Ceil:
    case SdvmInstFloat32x2Round:
    case SdvmInstFloat32x2Truncate:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    default:
        return sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
    }
}

void sdvm_compiler_aarch64_computeFunctionLocationConstraints(sdvm_functionCompilationState_t *state)
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
            sdvm_compiler_aarch64_computeInstructionLocationConstraints(state, instruction);
            ++i;
        }
    }
}

void sdvm_compiler_aarch64_allocateFunctionRegisters(sdvm_functionCompilationState_t *state)
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

void sdvm_compiler_aarch64_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_allocateFunctionSpillLocations(state);
}

void sdvm_compiler_aarch64_computeFunctionStackLayout(sdvm_functionCompilationState_t *state)
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
        // Frame pointer.
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

    sdvm_compiler_computeStackSegmentLayouts(state);

    SDVM_ASSERT(!state->requiresStackFramePointer);
    state->stackFrameRegister = SDVM_AARCH64_SP;
    state->stackFramePointerAnchorOffset = state->calloutStackSegment.endOffset;

    sdvm_compiler_computeStackFrameOffsets(state);
}

void sdvm_compiler_aarch64_ensureCIE(sdvm_moduleCompilationState_t *state)
{
    if(state->hasEmittedCIE)
        return;

    sdvm_dwarf_cfi_builder_t *cfi = &state->cfi;

    sdvm_dwarf_cie_t ehCie = {0};
    ehCie.codeAlignmentFactor = 4;
    ehCie.dataAlignmentFactor = -8;
    ehCie.pointerSize = 8;
    ehCie.returnAddressRegister = DW_AARCH64_REG_LR;
    cfi->section = &state->compiler->ehFrameSection;
    cfi->pointerSize = 8;
    cfi->initialStackFrameSize = 0;
    cfi->stackPointerRegister = DW_AARCH64_REG_SP;

    sdvm_dwarf_cfi_beginCIE(cfi, &ehCie);
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, DW_AARCH64_REG_SP, 0);
    sdvm_dwarf_cfi_endCIE(cfi);

    state->hasEmittedCIE = true;
}

void sdvm_compiler_aarch64_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;

    sdvm_compiler_aarch64_ensureCIE(state->moduleState);
    sdvm_dwarf_cfi_beginFDE(cfi, &compiler->textSection, sdvm_compiler_getCurrentPC(compiler));

    if(compiler->target->usesCET)
        sdvm_compiler_x86_endbr64(compiler);

    if(!state->requiresStackFrame)
    {
        sdvm_dwarf_cfi_endPrologue(cfi);
        return;
    }

    // Construct the stack frame.
    sdvm_compiler_aarch64_stp_preIndex(compiler, true, SDVM_AARCH64_FP, SDVM_AARCH64_LR, SDVM_AARCH64_SP, -16);
    sdvm_compiler_aarch64_mov_sp(compiler, true, SDVM_AARCH64_FP, SDVM_AARCH64_SP);

    sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
    sdvm_dwarf_cfi_pushRegister(cfi, DW_AARCH64_REG_LR);
    sdvm_dwarf_cfi_pushRegister(cfi, DW_AARCH64_REG_FP);

    int32_t stackSubtractionAmount = state->calloutStackSegment.endOffset - 16;
    SDVM_ASSERT((stackSubtractionAmount % 16) == 0);
    if(stackSubtractionAmount != 0)
    {
        sdvm_compiler_aarch64_sub_immediate(compiler, true, SDVM_AARCH64_SP, SDVM_AARCH64_SP, stackSubtractionAmount, SDVM_AARCH64_LSL_0);
        sdvm_dwarf_cfi_stackSizeAdvance(cfi, sdvm_compiler_getCurrentPC(compiler), stackSubtractionAmount);
    }
    
    sdvm_dwarf_cfi_endPrologue(cfi);
}

void sdvm_compiler_aarch64_emitMemoryToMemoryFixedSizedAlignedMove(sdvm_compiler_t *compiler, sdvm_aarch64_registerIndex_t sourcePointer, int32_t sourcePointerOffset, sdvm_aarch64_registerIndex_t destinationPointer, int32_t destinationPointerOffset, size_t copySize, const sdvm_compilerScratchMoveRegisters_t *scratchMoveRegister)
{
    SDVM_ASSERT(scratchMoveRegister->isValid);
    SDVM_ASSERT(scratchMoveRegister->kind == SdvmCompRegisterKindInteger);
    sdvm_compilerRegisterValue_t scratchRegister = scratchMoveRegister->value;

    SDVM_ASSERT(0 <= sourcePointerOffset);
    SDVM_ASSERT(0 <= destinationPointerOffset);

    size_t offset = 0;
    while(offset < copySize)
    {
        size_t remainingSize = copySize - offset;
        if(remainingSize >= 8)
        {
            SDVM_ASSERT(sourcePointerOffset % 8 == 0);
            SDVM_ASSERT(destinationPointerOffset % 8 == 0);
            sdvm_compiler_aarch64_ldr_offset(compiler, true, scratchRegister, sourcePointer, sourcePointerOffset + offset);
            sdvm_compiler_aarch64_str_offset(compiler, true, scratchRegister, destinationPointer, destinationPointerOffset + offset);
            offset += 8;
        }
        else if(remainingSize >= 4)
        {
            SDVM_ASSERT(sourcePointerOffset % 4 == 0);
            SDVM_ASSERT(destinationPointerOffset % 4 == 0);
            SDVM_ASSERT((sourcePointerOffset + copySize) / 4 < 4096);
            SDVM_ASSERT((destinationPointerOffset + copySize) / 4 < 4096);
            sdvm_compiler_aarch64_ldr_offset(compiler, false, scratchRegister, sourcePointer, sourcePointerOffset + offset);
            sdvm_compiler_aarch64_str_offset(compiler, false, scratchRegister, destinationPointer, destinationPointerOffset + offset);
            offset += 4;
        }
        else if(remainingSize >= 2)
        {
            SDVM_ASSERT(sourcePointerOffset % 2 == 0);
            SDVM_ASSERT(destinationPointerOffset % 2 == 0);
            SDVM_ASSERT((sourcePointerOffset + copySize) / 2 < 4096);
            SDVM_ASSERT((destinationPointerOffset + copySize) / 2 < 4096);
            sdvm_compiler_aarch64_ldrh_offset(compiler, scratchRegister, sourcePointer, sourcePointerOffset + offset);
            sdvm_compiler_aarch64_strh_offset(compiler, scratchRegister, destinationPointer, destinationPointerOffset + offset);
            offset += 2;
        }
        else
        {
            SDVM_ASSERT((sourcePointerOffset + copySize) < 4096);
            SDVM_ASSERT((destinationPointerOffset + copySize) < 4096);
            sdvm_compiler_aarch64_ldrb_offset(compiler, scratchRegister, sourcePointer, sourcePointerOffset + offset);
            sdvm_compiler_aarch64_strb_offset(compiler, scratchRegister, destinationPointer, destinationPointerOffset + offset);
            offset += 1;
        }
    }
}

void sdvm_compiler_aarch64_emitMoveFromLocationIntoIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        if(sourceLocation->firstRegister.size <= 4)
            return sdvm_compiler_aarch64_mov(compiler, false, reg->value, SDVM_AARCH64_WZR);
        return sdvm_compiler_aarch64_mov(compiler, true, reg->value, SDVM_AARCH64_XZR);
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
        return sdvm_compiler_aarch64_mov_imm32(compiler, reg->value, sourceLocation->immediateS32);
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
        return sdvm_compiler_aarch64_movImm64(compiler, reg->value, sourceLocation->immediateS64);
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        if(sourceLocation->firstRegister.size <= 4)
            return sdvm_compiler_aarch64_mov(compiler, false, reg->value, sourceLocation->firstRegister.value);
        return sdvm_compiler_aarch64_mov(compiler, true, reg->value, sourceLocation->firstRegister.value);
    case SdvmCompLocationStack:
    case SdvmCompLocationStackPair:
        switch(reg->size)
        {
        case 1:
            if(sourceLocation->isSigned)
                return sdvm_compiler_aarch64_ldrsb_offset(compiler, false, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_aarch64_ldrb_offset(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 2:
            if(sourceLocation->isSigned)
                return sdvm_compiler_aarch64_ldrsh_offset(compiler, false, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                return sdvm_compiler_aarch64_ldrh_offset(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 4: return sdvm_compiler_aarch64_ldr_offset(compiler, false, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        case 8: return sdvm_compiler_aarch64_ldr_offset(compiler, true, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
        default: return abort();
        }
    case SdvmCompLocationLocalSymbolValue:
        return sdvm_compiler_aarch64_adrl_sv(compiler, reg->value, sourceLocation->symbolHandle, sourceLocation->symbolOffset);
    default: return abort();
    }
}

void sdvm_compiler_aarch64_emitMoveFromLocationIntoVectorRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        return sdvm_compiler_aarch64_simd_mov_vector(compiler, true, reg->value, sourceLocation->firstRegister.value);
    default: return abort();
    }
}

void sdvm_compiler_aarch64_emitMoveFromLocationIntoRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(reg->kind)
    {
    case SdvmCompRegisterKindInteger:
        return sdvm_compiler_aarch64_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindFloat:
    case SdvmCompRegisterKindVectorFloat:
    case SdvmCompRegisterKindVectorInteger:
        return sdvm_compiler_aarch64_emitMoveFromLocationIntoVectorRegister(compiler, sourceLocation, reg);
    default: abort();
    }
}

void sdvm_compiler_aarch64_emitMoveFromRegisterIntoStackLocation(sdvm_compiler_t *compiler, const sdvm_compilerRegister_t *sourceRegister, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        switch(sourceRegister->size)
        {
        case 1: return sdvm_compiler_aarch64_strb_offset(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 2: return sdvm_compiler_aarch64_strh_offset(compiler, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 4: return sdvm_compiler_aarch64_str_offset(compiler, false, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        case 8: return sdvm_compiler_aarch64_str_offset(compiler, true, sourceRegister->value, stackLocation->framePointerRegister, stackLocation->framePointerOffset);
        default:
            return abort();
        }
    default:
        return abort();
    }
}

void sdvm_compiler_aarch64_emitMoveFromLocationIntoStack(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
        return sdvm_compiler_aarch64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);
    case SdvmCompLocationRegisterPair:
        {
            sdvm_compiler_aarch64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);

            sdvm_compilerStackLocation_t nextLocation = *stackLocation;
            nextLocation.segmentOffset += sourceLocation->firstRegister.size;
            nextLocation.framePointerOffset += sourceLocation->firstRegister.size;

            return sdvm_compiler_aarch64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->secondRegister, &nextLocation);
        }
    case SdvmCompLocationStack:
        SDVM_ASSERT(destinationLocation->scratchMoveRegister.isValid);
        return sdvm_compiler_aarch64_emitMemoryToMemoryFixedSizedAlignedMove(compiler,
            sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset,
            destinationLocation->firstStackLocation.framePointerRegister, destinationLocation->firstStackLocation.framePointerOffset,
            sourceLocation->firstStackLocation.size <= destinationLocation->firstStackLocation.size ? sourceLocation->firstStackLocation.size : destinationLocation->firstStackLocation.size,
            &destinationLocation->scratchMoveRegister);
    default: return abort();
    }
}

void sdvm_compiler_aarch64_emitMoveFromLocationInto(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation)
{
    switch(destinationLocation->kind)
    {
    case SdvmCompLocationNull:
        // Ignored.
        return;
    case SdvmCompLocationRegister:
        return sdvm_compiler_aarch64_emitMoveFromLocationIntoRegister(compiler, sourceLocation, &destinationLocation->firstRegister);
    case SdvmCompLocationRegisterPair:
        // TODO:
        return abort();
    case SdvmCompLocationStack:
        return sdvm_compiler_aarch64_emitMoveFromLocationIntoStack(compiler, sourceLocation, destinationLocation, &destinationLocation->firstStackLocation);
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

bool sdvm_compiler_aarch64_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_compiler_t *compiler = state->compiler;

    sdvm_compilerLocation_t *dest = &instruction->destinationLocation;
    sdvm_compilerLocation_t *arg0 = &instruction->arg0Location;
    sdvm_compilerLocation_t *arg1 = &instruction->arg1Location;
    sdvm_compilerLocation_t *scratch0 = &instruction->scratchLocation0;

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
        sdvm_compiler_aarch64_emitFunctionEpilogue(state);
        sdvm_compiler_aarch64_ret(compiler);
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
    case SdvmInstCallFloat32x2:
    case SdvmInstCallFloat32x4:
    case SdvmInstCallFloat64x2:
    case SdvmInstCallFloat64x4:
    case SdvmInstCallInt32x2:
    case SdvmInstCallInt32x4:
    case SdvmInstCallUInt32x2:
    case SdvmInstCallUInt32x4:
        if(arg0->kind == SdvmCompLocationGlobalSymbolValue || arg0->kind == SdvmCompLocationLocalSymbolValue)
            sdvm_compiler_aarch64_bl_sv(compiler, arg0->symbolHandle, 0);
        else
            sdvm_compiler_aarch64_blr(compiler, arg0->firstRegister.value);
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
    case SdvmInstCallClosureFloat32x2:
    case SdvmInstCallClosureFloat32x4:
    case SdvmInstCallClosureFloat64x2:
    case SdvmInstCallClosureFloat64x4:
    case SdvmInstCallClosureInt32x2:
    case SdvmInstCallClosureInt32x4:
    case SdvmInstCallClosureUInt32x2:
    case SdvmInstCallClosureUInt32x4:
        sdvm_compiler_aarch64_ldr_offset(compiler, true, scratch0->firstRegister.value, arg0->firstRegister.value, 0);
        sdvm_compiler_aarch64_blr(compiler, scratch0->firstRegister.value);
        return true;

    case SdvmInstLoadInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldrsb_offset(compiler, false, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldrsb_offset(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldrb_offset(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldrb_offset(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldrsh_offset(compiler, false, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldrsh_offset(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldrh_offset(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldrh_offset(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt32:
    case SdvmInstLoadUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldr_offset(compiler, false, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldr_offset(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt64:
    case SdvmInstLoadUInt64:
    case SdvmInstLoadPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadGCPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + 8);
        }
        else
        {
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, 0);
            sdvm_compiler_aarch64_ldr_offset(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, 8);
        }
        return true;

    case SdvmInstStoreInt8:
    case SdvmInstStoreUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_strb_offset(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_strb_offset(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt16:
    case SdvmInstStoreUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_strh_offset(compiler, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_strh_offset(compiler, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt32:
    case SdvmInstStoreUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_str_offset(compiler, false, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_str_offset(compiler, false, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreInt64:
    case SdvmInstStoreUInt64:
    case SdvmInstStorePointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_aarch64_str_offset(compiler, true, arg1->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_aarch64_str_offset(compiler, true, arg1->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstStoreGCPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_aarch64_str_offset(compiler, true, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
            sdvm_compiler_aarch64_str_offset(compiler, true, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + 8, arg1->secondRegister.value);
        }
        else
        {
            sdvm_compiler_aarch64_str_offset(compiler, true, arg0->firstRegister.value, 0, arg1->firstRegister.value);
            sdvm_compiler_aarch64_str_offset(compiler, true, arg0->firstRegister.value, 8, arg1->secondRegister.value);
        }
        return true;

    case SdvmInstJump:
        sdvm_compiler_aarch64_b_label(compiler, arg0->immediateLabel);
        return true;
    case SdvmInstJumpIfTrue:
        sdvm_compiler_aarch64_tst_shifted(compiler, false, arg0->firstRegister.value, arg0->firstRegister.value, SDVM_AARCH64_LSL, 0);
        sdvm_compiler_aarch64_b_cond_label(compiler, SDVM_AARCH64_NE, arg1->immediateLabel);
        return true;
    case SdvmInstJumpIfFalse:
        sdvm_compiler_aarch64_tst_shifted(compiler, false, arg0->firstRegister.value, arg0->firstRegister.value, SDVM_AARCH64_LSL, 0);
        sdvm_compiler_aarch64_b_cond_label(compiler, SDVM_AARCH64_EQ, arg1->immediateLabel);
        return true;

    case SdvmInstInt32Add:
    case SdvmInstUInt32Add:
        sdvm_compiler_aarch64_add_shifted(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        return true;
    case SdvmInstInt32Sub:
    case SdvmInstUInt32Sub:
        sdvm_compiler_aarch64_sub_shifted(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        return true;
    case SdvmInstInt32Mul:
    case SdvmInstUInt32Mul:
        sdvm_compiler_aarch64_mul(compiler, false, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt8Equals:
    case SdvmInstInt8NotEquals:
    case SdvmInstInt8LessThan:
    case SdvmInstInt8LessOrEquals:
    case SdvmInstInt8GreaterThan:
    case SdvmInstInt8GreaterOrEquals:
    case SdvmInstInt16Equals:
    case SdvmInstInt16NotEquals:
    case SdvmInstInt16LessThan:
    case SdvmInstInt16LessOrEquals:
    case SdvmInstInt16GreaterThan:
    case SdvmInstInt16GreaterOrEquals:
    case SdvmInstInt32Equals:
    case SdvmInstInt32NotEquals:
    case SdvmInstInt32LessThan:
    case SdvmInstInt32LessOrEquals:
    case SdvmInstInt32GreaterThan:
    case SdvmInstInt32GreaterOrEquals:
    case SdvmInstUInt8Equals:
    case SdvmInstUInt8NotEquals:
    case SdvmInstUInt8LessThan:
    case SdvmInstUInt8LessOrEquals:
    case SdvmInstUInt8GreaterThan:
    case SdvmInstUInt8GreaterOrEquals:
    case SdvmInstUInt16Equals:
    case SdvmInstUInt16NotEquals:
    case SdvmInstUInt16LessThan:
    case SdvmInstUInt16LessOrEquals:
    case SdvmInstUInt16GreaterThan:
    case SdvmInstUInt16GreaterOrEquals:
    case SdvmInstUInt32Equals:
    case SdvmInstUInt32NotEquals:
    case SdvmInstUInt32LessThan:
    case SdvmInstUInt32LessOrEquals:
    case SdvmInstUInt32GreaterThan:
    case SdvmInstUInt32GreaterOrEquals:
        sdvm_compiler_aarch64_cmp_shifted(compiler, false, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        sdvm_compiler_aarch64_cset(compiler, false, dest->firstRegister.value, sdvm_compiler_aarch64_mapConditionCode(sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode));
        return true;

    case SdvmInstInt64Add:
    case SdvmInstUInt64Add:
    case SdvmInstPointerAddOffsetInt64:
    case SdvmInstPointerAddOffsetUInt64:
        sdvm_compiler_aarch64_add_shifted(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        return true;
    case SdvmInstInt64Sub:
    case SdvmInstUInt64Sub:
        sdvm_compiler_aarch64_sub_shifted(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        return true;
    case SdvmInstInt64Mul:
    case SdvmInstUInt64Mul:
        sdvm_compiler_aarch64_mul(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt64Equals:
    case SdvmInstInt64NotEquals:
    case SdvmInstInt64LessThan:
    case SdvmInstInt64LessOrEquals:
    case SdvmInstInt64GreaterThan:
    case SdvmInstInt64GreaterOrEquals:
    case SdvmInstUInt64Equals:
    case SdvmInstUInt64NotEquals:
    case SdvmInstUInt64LessThan:
    case SdvmInstUInt64LessOrEquals:
    case SdvmInstUInt64GreaterThan:
    case SdvmInstUInt64GreaterOrEquals:
        sdvm_compiler_aarch64_cmp_shifted(compiler, true, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_LSL, 0);
        sdvm_compiler_aarch64_cset(compiler, true, dest->firstRegister.value, sdvm_compiler_aarch64_mapConditionCode(sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode));
        return true;

    case SdvmInstPointerAddOffsetUInt32:
        sdvm_compiler_aarch64_add_extended(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_UXTW, 0);
        return true;
    case SdvmInstPointerAddOffsetInt32:
        sdvm_compiler_aarch64_add_extended(compiler, true, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value, SDVM_AARCH64_SXTW, 0);
        return true;

    case SdvmInstFloat32Add:
        sdvm_compiler_aarch64_simd_fadd_scalar(compiler, SDVM_AARCH_FLOAT_SINGLE_TYPE, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstFloat64Add:
        sdvm_compiler_aarch64_simd_fadd_scalar(compiler, SDVM_AARCH_FLOAT_DOUBLE_TYPE, dest->firstRegister.value, arg0->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt8_Bitcast_UInt8:
    case SdvmInstInt16_Bitcast_UInt16:
    case SdvmInstInt32_Bitcast_UInt32:
    case SdvmInstInt64_Bitcast_UInt64:
    case SdvmInstUInt8_Bitcast_Int8:
    case SdvmInstUInt16_Bitcast_Int16:
    case SdvmInstUInt32_Bitcast_Int32:
    case SdvmInstUInt64_Bitcast_Int64:

    case SdvmInstInt64_Truncate_Int32:
    case SdvmInstInt64_Truncate_Int16:
    case SdvmInstInt64_Truncate_Int8:
    case SdvmInstInt64_Truncate_UInt32:
    case SdvmInstInt64_Truncate_UInt16:
    case SdvmInstInt64_Truncate_UInt8:
    case SdvmInstUInt64_Truncate_Int32:
    case SdvmInstUInt64_Truncate_Int16:
    case SdvmInstUInt64_Truncate_Int8:
    case SdvmInstUInt64_Truncate_UInt32:
    case SdvmInstUInt64_Truncate_UInt16:
    case SdvmInstUInt64_Truncate_UInt8:

    case SdvmInstInt32_Truncate_Int16:
    case SdvmInstInt32_Truncate_Int8:
    case SdvmInstInt32_Truncate_UInt16:
    case SdvmInstInt32_Truncate_UInt8:
    case SdvmInstUInt32_Truncate_Int16:
    case SdvmInstUInt32_Truncate_Int8:
    case SdvmInstUInt32_Truncate_UInt16:
    case SdvmInstUInt32_Truncate_UInt8:

    case SdvmInstInt16_Truncate_Int8:
    case SdvmInstInt16_Truncate_UInt8:
    case SdvmInstUInt16_Truncate_Int8:
    case SdvmInstUInt16_Truncate_UInt8:
        sdvm_compiler_aarch64_emitMoveFromLocationInto(compiler, arg0, dest);
        return true;

    case SdvmInstInt32_ZeroExtend_UInt64:
    case SdvmInstUInt32_ZeroExtend_Int64:
    case SdvmInstUInt32_ZeroExtend_UInt64:
        sdvm_compiler_aarch64_mov_noopt(compiler, false, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    default:
        abort();
    }
}

void sdvm_compiler_aarch64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, instruction->debugSourceLineInfo);

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
        sdvm_compiler_aarch64_emitMoveFromLocationInto(state->compiler, &arg0->location, &instruction->arg0Location);
    }

    if(startInstruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + startInstruction->decoding.instruction.arg1;
        sdvm_compiler_aarch64_emitMoveFromLocationInto(state->compiler, &arg1->location, &instruction->arg1Location);
    }

    // Emit the actual instruction operation
    if(instruction->pattern)
    {
        if(!instruction->pattern->generator(state, instruction->pattern->size, instruction))
            return;
    }
    else
    {
        if(!sdvm_compiler_aarch64_emitFunctionInstructionOperation(state, instruction))
            return;
    }

    // Emit the result moves.
    sdvm_compiler_aarch64_emitMoveFromLocationInto(state->compiler, &endInstruction->destinationLocation, &endInstruction->location);
}


void sdvm_compiler_aarch64_emitFunctionInstructions(sdvm_functionCompilationState_t *state)
{
    uint32_t i = 0;
    while(i < state->instructionCount)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_aarch64_emitFunctionInstruction(state, instruction);
        if(instruction->pattern)
            i += instruction->pattern->size;
        else
            ++i;
    }
}

void sdvm_compiler_aarch64_emitFunctionEnding(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    sdvm_dwarf_cfi_endFDE(cfi, sdvm_compiler_getCurrentPC(compiler));
}

void sdvm_compiler_aarch64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    if(!state->requiresStackFrame)
        return;

    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    sdvm_dwarf_cfi_beginEpilogue(cfi);

    int32_t stackSubtractionAmount = state->calloutStackSegment.endOffset - 16;
    SDVM_ASSERT((stackSubtractionAmount % 16) == 0);
    if(stackSubtractionAmount != 0)
    {
        sdvm_compiler_aarch64_add_immediate(compiler, true, SDVM_AARCH64_SP, SDVM_AARCH64_SP, stackSubtractionAmount, SDVM_AARCH64_LSL_0);
        sdvm_dwarf_cfi_stackSizeRestore(cfi, sdvm_compiler_getCurrentPC(compiler), stackSubtractionAmount);
    }

    sdvm_compiler_aarch64_ldp_postIndex(compiler, true, SDVM_AARCH64_FP, SDVM_AARCH64_LR, SDVM_AARCH64_SP, 16);
    sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
    sdvm_dwarf_cfi_popRegister(cfi, DW_AARCH64_REG_FP);
    sdvm_dwarf_cfi_popRegister(cfi, DW_AARCH64_REG_LR);

    sdvm_dwarf_cfi_endEpilogue(cfi);
}

bool sdvm_compiler_aarch64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_aarch64_computeFunctionLocationConstraints(state);
    sdvm_compiler_aarch64_allocateFunctionRegisters(state);
    sdvm_compiler_aarch64_allocateFunctionSpillLocations(state);
    sdvm_compiler_aarch64_computeFunctionStackLayout(state);

    if(state->compiler->verbose)
        sdvm_functionCompilationState_dump(state);

    // Align the function start symbol.
    sdvm_compiler_aarch64_alignUnreacheableCode(state->compiler);

    // Set the function symbol
    size_t startOffset = state->compiler->textSection.contents.size;
    state->debugInfo->startPC = startOffset;
    sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&state->compiler->symbolTable, state->symbol, state->compiler->textSection.symbolIndex, startOffset);

    // Emit the prologue.
    sdvm_compiler_aarch64_emitFunctionPrologue(state);

    // Emit the instructions.
    sdvm_compiler_aarch64_emitFunctionInstructions(state);

    // End the function.
    sdvm_compiler_aarch64_emitFunctionEnding(state);

    // Set the symbol size.
    size_t endOffset = state->compiler->textSection.contents.size;
    state->debugInfo->endPC = endOffset;
    sdvm_compilerSymbolTable_setSymbolSize(&state->compiler->symbolTable, state->symbol, endOffset - startOffset);
    sdvm_compiler_aarch64_alignUnreacheableCode(state->compiler);

    return true;
}

uint32_t sdvm_compiler_aarch64_mapElfRelocation(sdvm_compilerRelocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompRelocationAbsolute16: return SDVM_R_AARCH64_ABS16;
    case SdvmCompRelocationAbsolute32: return SDVM_R_AARCH64_ABS32;
    case SdvmCompRelocationAbsolute64: return SDVM_R_AARCH64_ABS64;
    case SdvmCompRelocationRelative32: return SDVM_R_AARCH64_PREL32;
    case SdvmCompRelocationRelative64: return SDVM_R_AARCH64_PREL64;
    case SdvmCompRelocationSectionRelative32: return SDVM_R_AARCH64_ABS32;
    case SdvmCompRelocationAArch64AdrRelativePageHi21: return SDVM_R_AARCH64_ADR_PREL_PG_HI21;
    case SdvmCompRelocationAArch64AddAbsoluteLo12NoCheck: return SDVM_R_AARCH64_ADD_ABS_LO12_NC;
    case SdvmCompRelocationAArch64Call26: return SDVM_R_AARCH64_CALL26;
    case SdvmCompRelocationAArch64Jump26: return SDVM_R_AARCH64_JUMP26;
    default: abort();
    }
}

uint16_t sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend(sdvm_compilerRelocation_t *relocation, uint8_t *target)
{
    abort();
}

size_t sdvm_compiler_aarch64_countMachORelocations(sdvm_compilerRelocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompRelocationAArch64AdrRelativePageHi21:
    case SdvmCompRelocationAArch64AddAbsoluteLo12NoCheck:
        return 2;
    case SdvmCompRelocationAArch64Call26:
    case SdvmCompRelocationAArch64Jump26:
    case SdvmCompRelocationRelative32:
    case SdvmCompRelocationSectionRelative32:
    case SdvmCompRelocationAbsolute64:
        return 1;
    default: abort();
    }
}

sdvm_macho_relocation_info_t sdvm_compiler_aarch64_addendRelocation(uint32_t offset, int64_t addend)
{
    sdvm_macho_relocation_info_t reloc = {
        .r_address = offset,
        .r_symbolnum = addend,
        .r_length = 2,
        .r_pcrel = false,
        .r_type = SDVM_MACHO_ARM64_RELOC_ADDEND,
    };

    return reloc;
}

size_t sdvm_compiler_aarch64_mapMachORelocation(sdvm_compilerRelocation_t *relocation, int64_t symbolAddend, uint64_t symbolSectionAddend, uint64_t relocatedSectionOffset, uint8_t *target, sdvm_macho_relocation_info_t *machRelocations)
{
    uint32_t *instruction = (uint32_t*)target;
    switch(relocation->kind)
    {
    case SdvmCompRelocationAArch64AdrRelativePageHi21:
        machRelocations->r_pcrel = true;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_PAGE21;
        machRelocations[1] = machRelocations[0];
        machRelocations[0] = sdvm_compiler_aarch64_addendRelocation(relocation->offset, relocation->addend + symbolAddend);
        return 2;
    case SdvmCompRelocationAArch64AddAbsoluteLo12NoCheck:
        machRelocations->r_pcrel = false;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_PAGEOFF12;
        machRelocations[1] = machRelocations[0];
        machRelocations[0] = sdvm_compiler_aarch64_addendRelocation(relocation->offset, relocation->addend + symbolAddend);
        return 2;
    case SdvmCompRelocationAArch64Call26:
    case SdvmCompRelocationAArch64Jump26:
        SDVM_ASSERT(relocation->addend + symbolAddend == 0);
        machRelocations->r_pcrel = true;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_BRANCH26;
        return 1;
    case SdvmCompRelocationRelative32:
        *instruction = relocation->addend + symbolAddend - (relocatedSectionOffset + relocation->offset);
        machRelocations->r_pcrel = true;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_UNSIGNED;
        return 1;
    case SdvmCompRelocationSectionRelative32:
        *instruction = relocation->addend + symbolAddend;
        machRelocations->r_pcrel = false;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_UNSIGNED;
        return 1;
    case SdvmCompRelocationAbsolute32:
        *instruction = relocation->addend + symbolAddend + symbolSectionAddend;
        machRelocations->r_pcrel = false;
        machRelocations->r_length = 2;
        machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_UNSIGNED;
        return 1;
    case SdvmCompRelocationAbsolute64:
        {
            int64_t *target64 = (int64_t*)target;
            *target64 = relocation->addend + symbolAddend + symbolSectionAddend;
            machRelocations->r_pcrel = false;
            machRelocations->r_length = 3;
            machRelocations->r_type = SDVM_MACHO_ARM64_RELOC_UNSIGNED;
            return 1;
        }
    default: abort();
    }
}

static sdvm_compilerTarget_t sdvm_compilerTarget_aarch64_linux = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_AARCH64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_ARM64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_ARM64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_ARM_ALL,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .closureCallNeedsScratch = true,

    .defaultCC = &sdvm_aarch64_eabi_callingConvention,
    .cdecl = &sdvm_aarch64_eabi_callingConvention,
    .stdcall = &sdvm_aarch64_eabi_callingConvention,
    .apicall = &sdvm_aarch64_eabi_callingConvention,
    .thiscall = &sdvm_aarch64_eabi_callingConvention,
    .vectorcall = &sdvm_aarch64_eabi_callingConvention,

    .compileModuleFunction = sdvm_compiler_aarch64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_aarch64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend,
    .countMachORelocations = sdvm_compiler_aarch64_countMachORelocations,
    .mapMachORelocation = sdvm_compiler_aarch64_mapMachORelocation,

    .instructionPatterns = &sdvm_aarch64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_aarch64_linux(void)
{
    return &sdvm_compilerTarget_aarch64_linux;
}

static sdvm_compilerTarget_t sdvm_compilerTarget_aarch64_macosx = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeMachO,
    .elfMachine = SDVM_EM_AARCH64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_ARM64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_ARM64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_ARM_ALL,
    .usesUnderscorePrefix = true,
    .usesCET = false,
    .closureCallNeedsScratch = true,

    .defaultCC = &sdvm_aarch64_apple_callingConvention,
    .cdecl = &sdvm_aarch64_apple_callingConvention,
    .stdcall = &sdvm_aarch64_apple_callingConvention,
    .apicall = &sdvm_aarch64_apple_callingConvention,
    .thiscall = &sdvm_aarch64_apple_callingConvention,
    .vectorcall = &sdvm_aarch64_apple_callingConvention,

    .compileModuleFunction = sdvm_compiler_aarch64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_aarch64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend,
    .countMachORelocations = sdvm_compiler_aarch64_countMachORelocations,
    .mapMachORelocation = sdvm_compiler_aarch64_mapMachORelocation,

    .instructionPatterns = &sdvm_aarch64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_aarch64_macosx(void)
{
    return &sdvm_compilerTarget_aarch64_macosx;
}

static sdvm_compilerTarget_t sdvm_compilerTarget_aarch64_windows = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeCoff,
    .elfMachine = SDVM_EM_AARCH64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_ARM64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_ARM64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_ARM_ALL,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .closureCallNeedsScratch = true,

    .defaultCC = &sdvm_aarch64_eabi_callingConvention,
    .cdecl = &sdvm_aarch64_eabi_callingConvention,
    .stdcall = &sdvm_aarch64_eabi_callingConvention,
    .apicall = &sdvm_aarch64_eabi_callingConvention,
    .thiscall = &sdvm_aarch64_eabi_callingConvention,
    .vectorcall = &sdvm_aarch64_eabi_callingConvention,

    .compileModuleFunction = sdvm_compiler_aarch64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_aarch64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend,
    .countMachORelocations = sdvm_compiler_aarch64_countMachORelocations,
    .mapMachORelocation = sdvm_compiler_aarch64_mapMachORelocation,

    .instructionPatterns = &sdvm_aarch64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_aarch64_windows(void)
{
    return &sdvm_compilerTarget_aarch64_windows;
}
