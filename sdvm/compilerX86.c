#include "compilerX86.h"
#include "module.h"
#include "elf.h"
#include "coff.h"
#include "macho.h"
#include "dwarf.h"
#include "utils.h"
#include "assert.h"
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

static const sdvm_compilerRegister_t *sdvm_x64_sysv_integerPassingDwordRegisters[] = {
    &sdvm_x86_EDI,
    &sdvm_x86_ESI,
    &sdvm_x86_EDX,
    &sdvm_x86_ECX,
    &sdvm_x86_R8D,
    &sdvm_x86_R9D,
};

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

static const sdvm_compilerRegister_t *sdvm_x64_sysv_vectorFloatPassingRegister[] = {
    &sdvm_x86_XMM0,  &sdvm_x86_XMM1,  &sdvm_x86_XMM2,  &sdvm_x86_XMM3,
    &sdvm_x86_XMM4,  &sdvm_x86_XMM5,  &sdvm_x86_XMM6,  &sdvm_x86_XMM7,
};

static const sdvm_compilerRegister_t *sdvm_x64_sysv_vectorIntegerPassingRegister[] = {
    &sdvm_x86_XMM0I,  &sdvm_x86_XMM1I,  &sdvm_x86_XMM2I,  &sdvm_x86_XMM3I,
    &sdvm_x86_XMM4I,  &sdvm_x86_XMM5I,  &sdvm_x86_XMM6I,  &sdvm_x86_XMM7I,
};

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callPreservedIntegerRegisters[] = {
    SDVM_X86_RBX, SDVM_X86_R12, SDVM_X86_R13, SDVM_X86_R14, SDVM_X86_R15, SDVM_X86_RSP, SDVM_X86_RBP
};

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callTouchedIntegerRegisters[] = {
    SDVM_X86_RAX, SDVM_X86_RCX, SDVM_X86_RDX, SDVM_X86_RSI, SDVM_X86_RDI, SDVM_X86_R8, SDVM_X86_R9, SDVM_X86_R10, SDVM_X86_R11
};

static const sdvm_compilerRegisterValue_t sdvm_x64_sysv_callTouchedVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,  SDVM_X86_XMM6,  SDVM_X86_XMM7,
    SDVM_X86_XMM8,  SDVM_X86_XMM9,  SDVM_X86_XMM10, SDVM_X86_XMM11,
    SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15,
};

static const sdvm_compilerRegisterValue_t sdvm_x64_allocatableVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,  SDVM_X86_XMM6,  SDVM_X86_XMM7,
    SDVM_X86_XMM8,  SDVM_X86_XMM9,  SDVM_X86_XMM10, SDVM_X86_XMM11,
    SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15,
};

const sdvm_compilerCallingConvention_t sdvm_x64_sysv_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,
    .usesVariadicVectorCountRegister = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 0,

    .integerRegisterSize = 8,
    .integerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_integerPassingRegisters),

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
    .vectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_vectorFloatPassingRegister),
    .vectorFloatRegisters = sdvm_x64_sysv_vectorFloatPassingRegister,
    .vectorIntegerRegisters = sdvm_x64_sysv_vectorIntegerPassingRegister,

    .firstVectorFloatResultRegister = &sdvm_x86_XMM0,
    .firstVectorIntegerResultRegister = &sdvm_x86_XMM0I,
    .secondVectorFloatResultRegister = &sdvm_x86_XMM1,
    .secondVectorIntegerResultRegister = &sdvm_x86_XMM1I,

    .allocatableIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_allocatableIntegerRegisters),
    .allocatableIntegerRegisters = sdvm_x64_sysv_allocatableIntegerRegisters,
    
    .allocatableVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_allocatableVectorRegisters),
    .allocatableVectorRegisters = sdvm_x64_allocatableVectorRegisters,

    .callPreservedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_callPreservedIntegerRegisters),
    .callPreservedIntegerRegisters = sdvm_x64_sysv_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_callTouchedIntegerRegisters),
    .callTouchedIntegerRegisters = sdvm_x64_sysv_callTouchedIntegerRegisters,

    .callTouchedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_sysv_callTouchedVectorRegisters),
    .callTouchedVectorRegisters = sdvm_x64_sysv_callTouchedVectorRegisters,

    .variadicVectorCountRegister = &sdvm_x86_RAX,
};

static const sdvm_compilerRegister_t *sdvm_x64_win64_integerPassingRegisters[] = {
    &sdvm_x86_RCX,
    &sdvm_x86_RDX,
    &sdvm_x86_R8,
    &sdvm_x86_R9,
};
static const uint32_t sdvm_x64_win64_integerPassingRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_integerPassingRegisters);

static const sdvm_compilerRegister_t *sdvm_x64_win64_integerPassingDwordRegisters[] = {
    &sdvm_x86_ECX,
    &sdvm_x86_EDX,
    &sdvm_x86_R8D,
    &sdvm_x86_R9D,
};
static const uint32_t sdvm_x64_win64_integerPassingDwordRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_integerPassingDwordRegisters);

static const sdvm_compilerRegisterValue_t sdvm_x64_win64_allocatableIntegerRegisters[] = {
    SDVM_X86_RAX,

    SDVM_X86_RCX, // Arg 1
    SDVM_X86_RDX, // Arg 2
    SDVM_X86_R8,  // Arg 3
    SDVM_X86_R9,  // Arg 4

    SDVM_X86_R10, // Closure pointer
    SDVM_X86_R11, // Closure GC pointer

    SDVM_X86_RDI,
    SDVM_X86_RSI,

    SDVM_X86_RBX,

    SDVM_X86_R12,
    SDVM_X86_R13,
    SDVM_X86_R14,
    SDVM_X86_R15,
};
static const uint32_t sdvm_x64_win64_allocatableIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_allocatableIntegerRegisters);

static const sdvm_compilerRegister_t *sdvm_x64_win64_vectorFloatPassingRegister[] = {
    &sdvm_x86_XMM0,  &sdvm_x86_XMM1,  &sdvm_x86_XMM2,  &sdvm_x86_XMM3,
};

static const sdvm_compilerRegister_t *sdvm_x64_win64_vectorIntegerPassingRegister[] = {
    &sdvm_x86_XMM0I,  &sdvm_x86_XMM1I,  &sdvm_x86_XMM2I,  &sdvm_x86_XMM3I,
};

static const sdvm_compilerRegisterValue_t sdvm_x64_win64_callPreservedIntegerRegisters[] = {
    SDVM_X86_RBX, SDVM_X86_RBP, SDVM_X86_RDI, SDVM_X86_RSI, SDVM_X86_RSP, SDVM_X86_R12, SDVM_X86_R13, SDVM_X86_R14, SDVM_X86_R15
};

static const sdvm_compilerRegisterValue_t sdvm_x64_win64_callTouchedIntegerRegisters[] = {
    SDVM_X86_RAX, SDVM_X86_RCX, SDVM_X86_RDX, SDVM_X86_R8, SDVM_X86_R9, SDVM_X86_R10, SDVM_X86_R11
};

static const sdvm_compilerRegisterValue_t sdvm_x64_win64_callTouchedVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,
};

static const sdvm_compilerRegisterValue_t sdvm_x64_win64_callPreservedVectorRegisters[] = {
    SDVM_X86_XMM6, SDVM_X86_XMM7, SDVM_X86_XMM8, SDVM_X86_XMM9, SDVM_X86_XMM10,
    SDVM_X86_XMM11, SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15
};

const sdvm_compilerCallingConvention_t sdvm_x64_win64_callingConvention = {
    .supportsLocalSymbolValueCall = true,
    .supportsGlobalSymbolValueCall = true,
    .anchorsFramePointerAtBottom = true,
    .usesSingleRegisterCount = true,
    .vectorsArePassedByPointers = true,

    .stackAlignment = 16,
    .stackParameterAlignment = 8,
    .calloutShadowSpace = 32,

    .integerRegisterSize = 8,
    .integerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_integerPassingRegisters),

    .integer32Registers = sdvm_x64_win64_integerPassingDwordRegisters,
    .integer64Registers = sdvm_x64_win64_integerPassingRegisters,
    .integerRegisters = sdvm_x64_win64_integerPassingRegisters,

    .closureRegister = &sdvm_x86_R10,
    .closureGCRegister = &sdvm_x86_R11,

    .firstInteger32ResultRegister = &sdvm_x86_EAX,
    .firstInteger64ResultRegister = &sdvm_x86_RAX,
    .firstIntegerResultRegister = &sdvm_x86_RAX,
    .secondInteger32ResultRegister = &sdvm_x86_EDX,
    .secondInteger64ResultRegister = &sdvm_x86_RDX,
    .secondIntegerResultRegister = &sdvm_x86_RDX,

    .vectorRegisterSize = 16,
    .vectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_vectorFloatPassingRegister),
    .vectorFloatRegisters = sdvm_x64_win64_vectorFloatPassingRegister,
    .vectorIntegerRegisters = sdvm_x64_win64_vectorIntegerPassingRegister,

    .firstVectorFloatResultRegister = &sdvm_x86_XMM0,
    .firstVectorIntegerResultRegister = &sdvm_x86_XMM0I,
    .secondVectorFloatResultRegister = &sdvm_x86_XMM1,
    .secondVectorIntegerResultRegister = &sdvm_x86_XMM1I,

    .allocatableIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_allocatableIntegerRegisters),
    .allocatableIntegerRegisters = sdvm_x64_win64_allocatableIntegerRegisters,
    
    .allocatableVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_allocatableVectorRegisters),
    .allocatableVectorRegisters = sdvm_x64_allocatableVectorRegisters,

    .callPreservedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_callPreservedIntegerRegisters),
    .callPreservedIntegerRegisters = sdvm_x64_win64_callPreservedIntegerRegisters,
    
    .callTouchedIntegerRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_callTouchedIntegerRegisters),
    .callTouchedIntegerRegisters = sdvm_x64_win64_callTouchedIntegerRegisters,

    .callPreservedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_callPreservedVectorRegisters),
    .callPreservedVectorRegisters = sdvm_x64_win64_callPreservedVectorRegisters,

    .callTouchedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_x64_win64_callTouchedVectorRegisters),
    .callTouchedVectorRegisters = sdvm_x64_win64_callTouchedVectorRegisters
};

static uint8_t sdvm_compiler_x86_nopPatterns[15][16] = {
    {0x90},
    {0x66, 0x90},                                                                               //  2 - xchg ax ax (o16 nop)
    {0x0f, 0x1f, 0x00},                                                                         //  3 - nop(3)
    {0x0f, 0x1f, 0x40, 0x00},                                                                   //  4 - nop(4)
    {0x0f, 0x1f, 0x44, 0x00, 0x00},                                                             //  5 - nop(5)
    {0x66, 0x0f, 0x1f, 0x44, 0x00, 0x00},                                                       //  6 - nop(6)
    {0x0f, 0x1f, 0x80, 0x00, 0x00, 0x00, 0x00},                                                 //  7 - nop(7)
    {0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},                                           //  8 - nop(8)
    {0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},                                     //  9 - nop(9)
    {0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},                               // 10 - o16 cs nop
    {0x66, 0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},                         // 11 - 2x o16 cs nop
    {0x66, 0x66, 0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},                   // 12 - 3x o16 cs nop
    {0x66, 0x66, 0x66, 0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},             // 13 - 4x o16 cs nop
    {0x66, 0x66, 0x66, 0x66, 0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00},       // 14 - 5x o16 cs nop
    {0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x2e, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00}, // 15 - 6x o16 cs nop
};

static int sdvm_compiler_x64_mapIntegerRegisterToDwarf(sdvm_compilerRegisterValue_t reg)
{
    switch(reg)
    {
    case SDVM_X86_RAX: return DW_X64_REG_RAX;
    case SDVM_X86_RCX: return DW_X64_REG_RCX;
    case SDVM_X86_RDX: return DW_X64_REG_RDX;
    case SDVM_X86_RBX: return DW_X64_REG_RBX;
    case SDVM_X86_RSP: return DW_X64_REG_RSP;
    case SDVM_X86_RBP: return DW_X64_REG_RBP;
    case SDVM_X86_RSI: return DW_X64_REG_RSI;
    case SDVM_X86_RDI: return DW_X64_REG_RDI;
    case SDVM_X86_R8:  return DW_X64_REG_R8;
    case SDVM_X86_R9:  return DW_X64_REG_R9;
    case SDVM_X86_R10: return DW_X64_REG_R10;
    case SDVM_X86_R11: return DW_X64_REG_R11;
    case SDVM_X86_R12: return DW_X64_REG_R12;
    case SDVM_X86_R13: return DW_X64_REG_R13;
    case SDVM_X86_R14: return DW_X64_REG_R14;
    case SDVM_X86_R15: return DW_X64_REG_R15;
    default: abort();
    }
}
void sdvm_compiler_x86_alignUnreacheableCode(sdvm_compiler_t *compiler)
{
    if(compiler->textSection.alignment < 16)
        compiler->textSection.alignment = 16;

    size_t alignedSize = sdvm_compiler_alignSizeTo(compiler->textSection.contents.size, 16);
    size_t paddingSize = alignedSize - compiler->textSection.contents.size;
    for(size_t i = 0; i < paddingSize; ++i)
        sdvm_compiler_addInstructionByte(compiler, 0xCC);
}

void sdvm_compiler_x86_alignReacheableCode(sdvm_compiler_t *compiler)
{
    if(compiler->textSection.alignment < 16)
        compiler->textSection.alignment = 16;

    size_t alignedSize = sdvm_compiler_alignSizeTo(compiler->textSection.contents.size, 16);
    size_t paddingSize = alignedSize - compiler->textSection.contents.size;
    while(paddingSize > 0)
    {
        size_t patternSize = paddingSize & 15;
        sdvm_compiler_addInstructionBytes(compiler, patternSize, sdvm_compiler_x86_nopPatterns[patternSize - 1]);
        paddingSize -= patternSize;
    }
}

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

void sdvm_compiler_x86_rexByte(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B)
{
    sdvm_compiler_addInstructionByte(compiler, 0x40 | ((W ? 1 : 0) << 3) | ((R ? 1 : 0) << 2) | ((X ? 1 : 0) << 1) | (B ? 1 : 0));
}

void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B)
{
    if(W || R || X || B)
        sdvm_compiler_x86_rexByte(compiler, W, R, X, B);
}

void sdvm_compiler_x86_rexByteBase(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    bool B = reg > SDVM_X86_REG_HALF_MASK;
    bool isHighPart = reg >= SDVM_X86_AH;
    if(B || isHighPart)
        sdvm_compiler_addInstructionByte(compiler, 0x40 | (B ? 1 : 0));
}

void sdvm_compiler_x86_rexPlusReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, false, false, reg > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexRmReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, reg > SDVM_X86_REG_HALF_MASK, false, rm > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexByteRmReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByte(compiler, W, reg > SDVM_X86_REG_HALF_MASK, false, rm > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexReg(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, W, reg > SDVM_X86_REG_HALF_MASK, false, false);
}

void sdvm_compiler_x86_rexRm(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm)
{
    sdvm_compiler_x86_rex(compiler, W, false, false, rm > SDVM_X86_REG_HALF_MASK);
}

void sdvm_compiler_x86_rexByteRm(sdvm_compiler_t *compiler, bool W, sdvm_x86_registerIndex_t rm)
{
    sdvm_compiler_x86_rexByte(compiler, W, false, false, rm > SDVM_X86_REG_HALF_MASK);
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
    sdvm_compiler_addInstructionByte(compiler, (uint8_t)(opcode >> 8));
    sdvm_compiler_addInstructionByte(compiler, (uint8_t)opcode);
}

void sdvm_compiler_x86_opcode3(sdvm_compiler_t *compiler, uint32_t opcode)
{
    sdvm_compiler_addInstructionByte(compiler, (uint8_t)(opcode >> 16));
    sdvm_compiler_addInstructionByte(compiler, (uint8_t)(opcode >> 8));
    sdvm_compiler_addInstructionByte(compiler, (uint8_t)opcode);
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
        sdvm_compiler_x86_imm8(compiler, (uint8_t)offset);
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

void sdvm_compiler_x86_movsb(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode(compiler, 0xA4);
}

void sdvm_compiler_x86_movsw(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_opcode(compiler, 0xA5);
}

void sdvm_compiler_x86_movsd(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode(compiler, 0xA5);
}

void sdvm_compiler_x86_movsq(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_rex(compiler, true, false, false, false);
    sdvm_compiler_x86_opcode(compiler, 0xA5);
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

void sdvm_compiler_x86_jmpLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode(compiler, 0xE9);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jnzLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F85);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jzLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F84);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jeLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F84);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jneLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F85);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jaLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F87);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jaeLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F83);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jbLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F82);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jbeLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F86);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jgLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F8F);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jgeLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F8D);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jlLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F8C);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jleLabel(sdvm_compiler_t *compiler, uint32_t label)
{
    sdvm_compiler_x86_opcode2(compiler, 0x0F8E);
    sdvm_compiler_addInstructionLabelValueRelative32(compiler, label, -4);
}

void sdvm_compiler_x86_jumpOnCondition(sdvm_compiler_t *compiler, uint32_t label, bool isSigned, sdvm_baseOpcode_t condition)
{
    switch(condition)
    {
    case SdvmOpEquals:
        sdvm_compiler_x86_jeLabel(compiler, label);
        return;
    case SdvmOpNotEquals: sdvm_compiler_x86_jneLabel(compiler, label);
        return;
    case SdvmOpLessThan:
        if(isSigned)
            sdvm_compiler_x86_jlLabel(compiler, label);
        else
            sdvm_compiler_x86_jbLabel(compiler, label);
        return;
    case SdvmOpLessOrEquals:
        if(isSigned)
            sdvm_compiler_x86_jleLabel(compiler, label);
        else
            sdvm_compiler_x86_jbeLabel(compiler, label);
        return;
    case SdvmOpGreaterThan:
        if(isSigned)
            sdvm_compiler_x86_jgLabel(compiler, label);
        else
            sdvm_compiler_x86_jaLabel(compiler, label);
        return;
    case SdvmOpGreaterOrEquals:
        if(isSigned)
            sdvm_compiler_x86_jgeLabel(compiler, label);
        else
            sdvm_compiler_x86_jaeLabel(compiler, label);
        return;
    default:
        abort();
    }
}

void sdvm_compiler_x86_jumpOnInverseCondition(sdvm_compiler_t *compiler, uint32_t label, bool isSigned, sdvm_baseOpcode_t condition)
{
    switch(condition)
    {
    case SdvmOpEquals: 
        sdvm_compiler_x86_jneLabel(compiler, label);
        return;
    case SdvmOpNotEquals: 
        sdvm_compiler_x86_jeLabel(compiler, label);
        return;
    case SdvmOpLessThan:
        if(isSigned)
            sdvm_compiler_x86_jgeLabel(compiler, label);
        else
            sdvm_compiler_x86_jaeLabel(compiler, label);
        return;
    case SdvmOpLessOrEquals:
        if(isSigned)
            sdvm_compiler_x86_jgLabel(compiler, label);
        else
            sdvm_compiler_x86_jaLabel(compiler, label);
        return;
    case SdvmOpGreaterThan:
        if(isSigned)
            sdvm_compiler_x86_jleLabel(compiler, label);
        else
            sdvm_compiler_x86_jbeLabel(compiler, label);
        return;
    case SdvmOpGreaterOrEquals:
        if(isSigned)
            sdvm_compiler_x86_jlLabel(compiler, label);
        else
            sdvm_compiler_x86_jbLabel(compiler, label);
        return;
    default:
        abort();
    }
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

void sdvm_compiler_x86_cwd(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_opcode(compiler, 0x99);
}

void sdvm_compiler_x86_cdq(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_opcode(compiler, 0x99);
}

void sdvm_compiler_x86_cqo(sdvm_compiler_t *compiler)
{
    sdvm_compiler_x86_rex(compiler, true, false, false, false);
    sdvm_compiler_x86_opcode(compiler, 0x99);
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

void sdvm_compiler_x86_sete(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F94);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setne(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F95);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setb(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F92);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setbe(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F96);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_seta(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F97);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setae(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F93);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setl(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F9C);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setle(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F9E);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F9F);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setge(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rexByteBase(compiler, reg);
    sdvm_compiler_x86_opcode2(compiler, 0x0F9D);
    sdvm_compiler_x86_modRmOp(compiler, reg, 0);
}

void sdvm_compiler_x86_setByteOnCondition(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, bool isSigned, sdvm_baseOpcode_t condition)
{
    switch(condition)
    {
    case SdvmOpEquals:
        sdvm_compiler_x86_sete(compiler, destination);
        return;
    case SdvmOpNotEquals:
        sdvm_compiler_x86_setne(compiler, destination);
        return;
    case SdvmOpLessThan:
        if(isSigned)
            sdvm_compiler_x86_setl(compiler, destination);
        else
            sdvm_compiler_x86_setb(compiler, destination);
        return;
    case SdvmOpLessOrEquals:
        if(isSigned)
            sdvm_compiler_x86_setle(compiler, destination);
        else
            sdvm_compiler_x86_setbe(compiler, destination);
        return;
    case SdvmOpGreaterThan:
        if(isSigned)
            sdvm_compiler_x86_setg(compiler, destination);
        else
            sdvm_compiler_x86_seta(compiler, destination);
        return;
    case SdvmOpGreaterOrEquals:
        if(isSigned)
            sdvm_compiler_x86_setge(compiler, destination);
        else
            sdvm_compiler_x86_setae(compiler, destination);
        return;
    default:
        abort();
    }
}

void sdvm_compiler_x86_setByteOnInverseCondition(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, bool isSigned, sdvm_baseOpcode_t condition)
{
    switch(condition)
    {
    case SdvmOpEquals:
        sdvm_compiler_x86_setne(compiler, destination);
        return;
    case SdvmOpNotEquals:
        sdvm_compiler_x86_sete(compiler, destination);
        return;
    case SdvmOpLessThan:
        if(isSigned)
            sdvm_compiler_x86_setge(compiler, destination);
        else
            sdvm_compiler_x86_setae(compiler, destination);
        return;
    case SdvmOpLessOrEquals:
        if(isSigned)
            sdvm_compiler_x86_setg(compiler, destination);
        else
            sdvm_compiler_x86_seta(compiler, destination);
        return;
    case SdvmOpGreaterThan:
        if(isSigned)
            sdvm_compiler_x86_setle(compiler, destination);
        else
            sdvm_compiler_x86_setbe(compiler, destination);
        return;
    case SdvmOpGreaterOrEquals:
        if(isSigned)
            sdvm_compiler_x86_setl(compiler, destination);
        else
            sdvm_compiler_x86_setb(compiler, destination);
        return;
    default:
        abort();
    }
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

void sdvm_compiler_x86_cmove64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F44);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovne64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F45);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmova64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F47);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovae64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F43);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovb64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F42);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovbe64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F46);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovg64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovge64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovl64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovle64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4E);
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
    sdvm_compiler_x86_add64RegImmS32(compiler, destination, (int32_t)offset);
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
    {
        sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);
        return;
    }
    
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0xC7);
    sdvm_compiler_x86_modRmOp(compiler, destination, 0);
    sdvm_compiler_x86_imm32(compiler, value);
}

void sdvm_compiler_x86_mov64RegImmS64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int64_t value)
{
    if(value == (int64_t)(int32_t)value)
        sdvm_compiler_x86_mov64RegImmS32(compiler, destination, (int32_t)value);
    else
        sdvm_compiler_x86_movabs64(compiler, destination, value);
}

void sdvm_compiler_x86_mov64RegImmU64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value)
{
    
    if(value == (uint64_t)(uint32_t)value)
        sdvm_compiler_x86_mov32RegImm32(compiler, destination, (int32_t)value);
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
        sdvm_compiler_x86_alu64RmImm8(compiler, opcodeImm8, destination, regOpcode, (uint8_t)value);
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

void sdvm_compiler_x86_cmp64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x39, destination, source);
}

void sdvm_compiler_x86_test64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu64RmReg(compiler, 0x85, destination, source);
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

void sdvm_compiler_x86_imul64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, destination, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0FAF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_div64Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 6);
}

void sdvm_compiler_x86_idiv64Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 7);
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

void sdvm_compiler_x86_cmp64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    sdvm_compiler_x86_alu64RmImm32_S8(compiler, 0x81, 0x83, destination, 7, value);
}

void sdvm_compiler_x86_test64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    sdvm_compiler_x86_alu64RmImm32(compiler, 0xF7, destination, 0, value);
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

SDVM_API void sdvm_compiler_x86_sar64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 7);
}

SDVM_API void sdvm_compiler_x86_sar64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, true, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shl64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 4);
}

SDVM_API void sdvm_compiler_x86_shl64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, true, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shr64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, true, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 5);
}

SDVM_API void sdvm_compiler_x86_shr64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, true, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

#pragma endregion X86_Instructions_64

#pragma region X86_Instructions_32

void sdvm_compiler_x86_cmove32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F44);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovne32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F45);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmova32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F47);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovae32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F43);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovb32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F42);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovbe32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F46);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovg32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovge32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovl32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_cmovle32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;
    
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F4E);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
    {
        sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);
        return;
    }

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

void sdvm_compiler_x86_movsxdReg64Reg32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode(compiler, 0x63);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsxdReg64Rmo32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode(compiler, 0x63);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_lea32RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset)
{
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8D);
    sdvm_compiler_x86_modLsvReg(compiler, sourceSymbol, destination, offset, 0);
}

void sdvm_compiler_x86_lea32RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode(compiler, 0x8D);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
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
        sdvm_compiler_x86_alu32RmImm8(compiler, opcodeImm8, destination, regOpcode, (uint8_t)value);
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

void sdvm_compiler_x86_cmp32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x39, destination, source);
}

void sdvm_compiler_x86_test32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu32RmReg(compiler, 0x85, destination, source);
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

void sdvm_compiler_x86_imul32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, destination, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0FAF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_div32Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 6);
}

void sdvm_compiler_x86_idiv32Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 7);
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

void sdvm_compiler_x86_cmp32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    sdvm_compiler_x86_alu32RmImm32_S8(compiler, 0x81, 0x83, destination, 7, value);
}

void sdvm_compiler_x86_test32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    sdvm_compiler_x86_alu32RmImm32(compiler, 0xF7, destination, 0, value);
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

SDVM_API void sdvm_compiler_x86_sar32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 7);
}

SDVM_API void sdvm_compiler_x86_sar32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shl32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 4);
}

SDVM_API void sdvm_compiler_x86_shl32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shr32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 5);
}

SDVM_API void sdvm_compiler_x86_shr32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
        sdvm_compiler_x86_imm8(compiler, value);
    }
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
        sdvm_compiler_x86_alu16RmImm8(compiler, opcodeImm8, destination, regOpcode, (uint8_t)value);
    else
        sdvm_compiler_x86_alu16RmImm16(compiler, opcodeImm32, destination, regOpcode, (uint16_t)value);
}

void sdvm_compiler_x86_add16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x01, destination, source);
}

void sdvm_compiler_x86_sub16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x29, destination, source);
}

void sdvm_compiler_x86_cmp16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x39, destination, source);
}

void sdvm_compiler_x86_test16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu16RmReg(compiler, 0x85, destination, source);
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

void sdvm_compiler_x86_imul16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRmReg(compiler, false, destination, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0FAF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_div16Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRmReg(compiler, false, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 6);
}

void sdvm_compiler_x86_idiv16Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRmReg(compiler, false, operand, 0);
    sdvm_compiler_x86_opcode(compiler, 0xF7);
    sdvm_compiler_x86_modRmReg(compiler, operand, 7);
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

void sdvm_compiler_x86_cmp16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    sdvm_compiler_x86_alu16RmImm16_S8(compiler, 0x81, 0x83, destination, 7, value);
}

void sdvm_compiler_x86_test16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value)
{
    sdvm_compiler_x86_alu16RmImm16(compiler, 0xF7, destination, 0, value);
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

SDVM_API void sdvm_compiler_x86_sar16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 7);
}

SDVM_API void sdvm_compiler_x86_sar16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shl16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 4);
}

SDVM_API void sdvm_compiler_x86_shl16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shr16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD3);
    sdvm_compiler_x86_modRmOp(compiler, destination, 5);
}

SDVM_API void sdvm_compiler_x86_shr16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_operandPrefix(compiler);
    sdvm_compiler_x86_rexRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC1);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

#pragma endregion X86_Instructions_16

#pragma region X86_Instructions_8

void sdvm_compiler_x86_mov8RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexByteRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode(compiler, 0x88);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movzxReg32Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexByteRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB6);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movzxReg32Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB6);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movzxReg64Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB6);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movzxReg64Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FB6);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movsxReg32Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexByteRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBE);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsxReg32Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBE);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movsxReg64Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexByteRmReg(compiler, true, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBE);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsxReg64Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, true, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FBE);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_alu8RmReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexByteRmReg(compiler, false, destination, source);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmReg(compiler, destination, source);
}

void sdvm_compiler_x86_alu8RmImm8(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint16_t value)
{
    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, opcode);
    sdvm_compiler_x86_modRmOp(compiler, destination, regOpcode);
    sdvm_compiler_x86_imm8(compiler, (uint8_t)value);
}

void sdvm_compiler_x86_add8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x00, destination, source);
}

void sdvm_compiler_x86_sub8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x28, destination, source);
}

void sdvm_compiler_x86_cmp8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x38, destination, source);
}

void sdvm_compiler_x86_test8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x84, destination, source);
}

void sdvm_compiler_x86_and8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x20, destination, source);
}

void sdvm_compiler_x86_or8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x08, destination, source);
}

void sdvm_compiler_x86_xor8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_alu8RmReg(compiler, 0x30, destination, source);
}

void sdvm_compiler_x86_add8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 0, value);
}

void sdvm_compiler_x86_sub8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 5, value);
}

void sdvm_compiler_x86_cmp8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 7, value);
}

void sdvm_compiler_x86_test8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    sdvm_compiler_x86_alu8RmImm8(compiler, 0xF6, destination, 0, value);
}

void sdvm_compiler_x86_and8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == -1)
        return;

    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 4, value);
}

void sdvm_compiler_x86_or8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 1, value);
}

void sdvm_compiler_x86_xor8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_alu8RmImm8(compiler, 0x80, destination, 6, value);
}

SDVM_API void sdvm_compiler_x86_sar8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD2);
    sdvm_compiler_x86_modRmOp(compiler, destination, 7);
}

SDVM_API void sdvm_compiler_x86_sar8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 7);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shl8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD2);
    sdvm_compiler_x86_modRmOp(compiler, destination, 4);
}

SDVM_API void sdvm_compiler_x86_shl8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 4);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

SDVM_API void sdvm_compiler_x86_shr8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination)
{
    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    sdvm_compiler_x86_opcode(compiler, 0xD2);
    sdvm_compiler_x86_modRmOp(compiler, destination, 5);
}

SDVM_API void sdvm_compiler_x86_shr8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rexByteRm(compiler, false, destination);
    if(value == 1)
    {
        sdvm_compiler_x86_opcode(compiler, 0xD0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
    }
    else
    {
        sdvm_compiler_x86_opcode(compiler, 0xC0);
        sdvm_compiler_x86_modRmOp(compiler, destination, 5);
        sdvm_compiler_x86_imm8(compiler, value);
    }
}

#pragma endregion X86_Instructions_8

#pragma region X86_Instructions_SSE

void sdvm_compiler_x86_addpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F58);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_subpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mulpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F59);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_divpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5E);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_sqrtpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F51);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_maxpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_minpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movapsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F28);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movapsRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F28);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movapsRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0F29);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movapsRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol)
{
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F28);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
}

void sdvm_compiler_x86_addpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F58);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_subpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mulpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F59);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_divpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5E);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_sqrtpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F51);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_maxpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_minpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_xorpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F57);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movsdRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movsdRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0F11);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movsdRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
}

void sdvm_compiler_x86_addsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F58);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_subsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mulsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F59);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_divsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5E);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_sqrtsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F51);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_maxsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_minsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF2);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movssRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movssRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0F11);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movssRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F10);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
}

void sdvm_compiler_x86_addssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F58);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_subssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5C);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_mulssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F59);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_divssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5E);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_sqrtssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F51);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_maxssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_minssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0xF3);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F5D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movdqaRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination == source)
        return;

    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F6F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_movdqaRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F6F);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, destination);
}

void sdvm_compiler_x86_movdqaRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, base, source);
    sdvm_compiler_x86_opcode2(compiler, 0x0F7F);
    sdvm_compiler_x86_modRmoReg(compiler, base, offset, source);
}

void sdvm_compiler_x86_movdqaRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexReg(compiler, false, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0F6F);
    sdvm_compiler_x86_modGsvReg(compiler, sourceSymbol, destination, 0, 0);
}

void sdvm_compiler_x86_padddRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FFE);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_psubdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FFA);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pmulldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode3(compiler, 0x0F3840);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pmaxsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode3(compiler, 0x0F383D);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pmaxudRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode3(compiler, 0x0F383F);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pminsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode3(compiler, 0x0F3839);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pminudRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode3(compiler, 0x0F383B);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pandRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FDB);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_porRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FEB);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pxorRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FEF);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_pslldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FF2);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_psradRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FE2);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

void sdvm_compiler_x86_psrldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_opcode(compiler, 0x66);
    sdvm_compiler_x86_rexRmReg(compiler, false, source, destination);
    sdvm_compiler_x86_opcode2(compiler, 0x0FD2);
    sdvm_compiler_x86_modRmReg(compiler, source, destination);
}

#pragma endregion X86

#pragma region X86_RegisterConstraints
sdvm_compilerLocation_t sdvm_compilerLocation_x64_immediateS64(sdvm_compiler_t *compiler, int64_t value)
{
    if(value == (int64_t)(int32_t)value)
        return sdvm_compilerLocation_immediateS32((int32_t)value);
    else
        return sdvm_compilerLocation_constSectionS64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_x64_immediateU64(sdvm_compiler_t *compiler, uint64_t value)
{
    if(value == (uint64_t)(uint32_t)value)
        return sdvm_compilerLocation_immediateS32((int32_t)value);
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

bool sdvm_compilerLocation_x64_isImmPowerOfTwo(sdvm_compilerLocation_t *location)
{
    switch(location->kind)
    {
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS32:
        return sdvm_uint32_isPowerOfTwo(location->immediateU32);
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateS64:
        return sdvm_uint64_isPowerOfTwo(location->immediateU64);
    default:
        return false;
    }
}

int8_t sdvm_compilerLocation_x64_log2(sdvm_compilerLocation_t *location)
{
    switch(location->kind)
    {
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS32:
        return (int8_t)sdvm_uint32_log2(location->immediateU32);
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateS64:
        return (int8_t)sdvm_uint64_log2(location->immediateU64);
    default:
        abort();
    }
}

sdvm_compilerLocation_t sdvm_compilerLocation_x64_intRegOrPowerOfTwo(uint8_t size, sdvm_compilerInstruction_t *operand)
{
    if(sdvm_compilerLocation_x64_isImmPowerOfTwo(&operand->location))
        return operand->location;
    return sdvm_compilerLocation_integerRegister(size);
}

void sdvm_compiler_x64_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_immediateS32((int32_t)instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstUInt32:
            instruction->location = sdvm_compilerLocation_immediateU32((uint32_t)instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64SExt:
        case SdvmConstUInt64SExt:
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_x64_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
        case SdvmConstUInt64ZExt:
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_x64_immediateU64(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64ConstSection:
        case SdvmConstUInt64ConstSection:
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
    uint32_t pointerSize = state->compiler->target->pointerSize;

    switch (instruction->decoding.opcode)
    {
    case SdvmInstInt8Add:
    case SdvmInstInt8Sub:
    case SdvmInstInt8And:
    case SdvmInstInt8Or:
    case SdvmInstInt8Xor:
    case SdvmInstUInt8Add:
    case SdvmInstUInt8Sub:
    case SdvmInstUInt8And:
    case SdvmInstUInt8Or:
    case SdvmInstUInt8Xor:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(1, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(1, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt8Mul:
    case SdvmInstUInt8Mul:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(1);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        return;
    case SdvmInstInt8Div:
    case SdvmInstInt8UDiv:
    case SdvmInstUInt8Div:
    case SdvmInstUInt8UDiv:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(1);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        return;
    case SdvmInstInt8Rem:
    case SdvmInstInt8URem:
    case SdvmInstUInt8Rem:
    case SdvmInstUInt8URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(1);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        return;
    case SdvmInstInt8Lsl:
    case SdvmInstInt8Lsr:
    case SdvmInstInt8Asr:
    case SdvmInstUInt8Lsl:
    case SdvmInstUInt8Lsr:
    case SdvmInstUInt8Asr:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(1, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_specificRegOrImm32(sdvm_x86_CX, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt8Equals:
    case SdvmInstInt8NotEquals:
    case SdvmInstInt8LessThan:
    case SdvmInstInt8LessOrEquals:
    case SdvmInstInt8GreaterThan:
    case SdvmInstInt8GreaterOrEquals:
    case SdvmInstUInt8Equals:
    case SdvmInstUInt8NotEquals:
    case SdvmInstUInt8LessThan:
    case SdvmInstUInt8LessOrEquals:
    case SdvmInstUInt8GreaterThan:
    case SdvmInstUInt8GreaterOrEquals:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(1);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(1, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

    case SdvmInstInt16Add:
    case SdvmInstInt16Sub:
    case SdvmInstInt16And:
    case SdvmInstInt16Or:
    case SdvmInstInt16Xor:
    case SdvmInstUInt16Add:
    case SdvmInstUInt16Sub:
    case SdvmInstUInt16And:
    case SdvmInstUInt16Or:
    case SdvmInstUInt16Xor:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(2);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt16Mul:
    case SdvmInstUInt16Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(2);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrPowerOfTwo(2, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(2);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt16Div:
    case SdvmInstInt16UDiv:
    case SdvmInstUInt16Div:
    case SdvmInstUInt16UDiv:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(2);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_DX);
        return;
    case SdvmInstInt16Rem:
    case SdvmInstInt16URem:
    case SdvmInstUInt16Rem:
    case SdvmInstUInt16URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(2);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_DX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_AX);
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
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt16Equals:
    case SdvmInstInt16NotEquals:
    case SdvmInstInt16LessThan:
    case SdvmInstInt16LessOrEquals:
    case SdvmInstInt16GreaterThan:
    case SdvmInstInt16GreaterOrEquals:
    case SdvmInstUInt16Equals:
    case SdvmInstUInt16NotEquals:
    case SdvmInstUInt16LessThan:
    case SdvmInstUInt16LessOrEquals:
    case SdvmInstUInt16GreaterThan:
    case SdvmInstUInt16GreaterOrEquals:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(2);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

    case SdvmInstInt32Add:
    case SdvmInstInt32Sub:
    case SdvmInstInt32And:
    case SdvmInstInt32Xor:
    case SdvmInstInt32Or:
    case SdvmInstUInt32Add:
    case SdvmInstUInt32Sub:
    case SdvmInstUInt32And:
    case SdvmInstUInt32Xor:
    case SdvmInstUInt32Or:
        instruction->arg0Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt32Mul:
    case SdvmInstUInt32Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrPowerOfTwo(4, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(4);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt32Div:
    case SdvmInstInt32UDiv:
    case SdvmInstUInt32Div:
    case SdvmInstUInt32UDiv:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_EDX);
        return;
    case SdvmInstInt32Rem:
    case SdvmInstInt32URem:
    case SdvmInstUInt32Rem:
    case SdvmInstUInt32URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_EDX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
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
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt32Equals:
    case SdvmInstInt32NotEquals:
    case SdvmInstInt32LessThan:
    case SdvmInstInt32LessOrEquals:
    case SdvmInstInt32GreaterThan:
    case SdvmInstInt32GreaterOrEquals:
    case SdvmInstUInt32Equals:
    case SdvmInstUInt32NotEquals:
    case SdvmInstUInt32LessThan:
    case SdvmInstUInt32LessOrEquals:
    case SdvmInstUInt32GreaterThan:
    case SdvmInstUInt32GreaterOrEquals:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

    case SdvmInstPointerAddOffsetUInt32:
    case SdvmInstPointerAddOffsetInt64:
    case SdvmInstPointerAddOffsetUInt64:
        instruction->arg0Location = sdvm_compilerLocation_x64_intRegOrImmS32((uint8_t)pointerSize, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrImmS32((uint8_t)pointerSize, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister((uint8_t)pointerSize);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstInt64Add:
    case SdvmInstInt64Sub:
    case SdvmInstInt64And:
    case SdvmInstInt64Or:
    case SdvmInstInt64Xor:
    case SdvmInstUInt64Add:
    case SdvmInstUInt64Sub:
    case SdvmInstUInt64And:
    case SdvmInstUInt64Or:
    case SdvmInstUInt64Xor:
        instruction->arg0Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg0);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt64Mul:
    case SdvmInstUInt64Mul:
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrPowerOfTwo(8, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstInt64Div:
    case SdvmInstInt64UDiv:
    case SdvmInstUInt64Div:
    case SdvmInstUInt64UDiv:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_RDX);
        return;
    case SdvmInstInt64Rem:
    case SdvmInstInt64URem:
    case SdvmInstUInt64Rem:
    case SdvmInstUInt64URem:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        instruction->arg1Location = sdvm_compilerLocation_integerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(sdvm_x86_RDX);
        instruction->scratchLocation0 = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
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
        instruction->allowArg0DestinationShare = true;
        return;
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
        instruction->arg0Location = sdvm_compilerLocation_integerRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg1);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

    case SdvmInstMemcopyFixed:
    case SdvmInstMemcopyGCFixed:
        {
            sdvm_moduleMemoryDescriptorTableEntry_t *memoryDescriptor = state->module->memoryDescriptorTable + instruction->decoding.instruction.arg2;
            instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RDI);
            instruction->arg1Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RSI);
            instruction->implicitArg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RCX);

            uint64_t movsCount = memoryDescriptor->size;
            if(memoryDescriptor->alignment >= 8 && memoryDescriptor->size % 8 == 0)
                movsCount /= 8;
            else if(memoryDescriptor->alignment >= 4 && memoryDescriptor->size % 4 == 0)
                movsCount /= 4;
            else if(memoryDescriptor->alignment >= 2 && memoryDescriptor->size % 2 == 0)
                movsCount /= 2;
            instruction->implicitArg0SourceLocation = sdvm_compilerLocation_immediateU64(movsCount);
        }
        return;

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

    case SdvmInstInt8_SignExtend_Int16:
    case SdvmInstInt8_SignExtend_Int32:
    case SdvmInstInt8_SignExtend_Int64:
    case SdvmInstInt16_SignExtend_Int32:
    case SdvmInstInt16_SignExtend_Int64:
    case SdvmInstInt32_SignExtend_Int64:

    case SdvmInstInt8_ZeroExtend_UInt16:
    case SdvmInstInt8_ZeroExtend_UInt32:
    case SdvmInstUInt8_ZeroExtend_Int16:
    case SdvmInstUInt8_ZeroExtend_Int32:
    case SdvmInstUInt8_ZeroExtend_UInt16:
    case SdvmInstUInt8_ZeroExtend_UInt32:
    case SdvmInstInt8_ZeroExtend_UInt64:
    case SdvmInstUInt8_ZeroExtend_Int64:
    case SdvmInstUInt8_ZeroExtend_UInt64:
    case SdvmInstInt16_ZeroExtend_UInt32:
    case SdvmInstUInt16_ZeroExtend_Int32:
    case SdvmInstUInt16_ZeroExtend_UInt32:
    case SdvmInstInt16_ZeroExtend_UInt64:
    case SdvmInstUInt16_ZeroExtend_Int64:
    case SdvmInstUInt16_ZeroExtend_UInt64:
    case SdvmInstInt32_ZeroExtend_UInt64:
    case SdvmInstUInt32_ZeroExtend_Int64:
    case SdvmInstUInt32_ZeroExtend_UInt64:
        sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
        instruction->allowArg0DestinationShare = true;
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
        return;
    case SdvmInstFloat32Sqrt:
    case SdvmInstFloat32Floor:
    case SdvmInstFloat32Ceil:
    case SdvmInstFloat32Truncate:
    case SdvmInstFloat32Round:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstFloat32Equals:
    case SdvmInstFloat32NotEquals:
    case SdvmInstFloat32LessThan:
    case SdvmInstFloat32LessOrEquals:
    case SdvmInstFloat32GreaterThan:
    case SdvmInstFloat32GreaterOrEquals:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(4);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

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
        return;
    case SdvmInstFloat32x2Sqrt:
    case SdvmInstFloat32x2Floor:
    case SdvmInstFloat32x2Ceil:
    case SdvmInstFloat32x2Truncate:
    case SdvmInstFloat32x2Round:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstFloat32x4Add:
    case SdvmInstFloat32x4Sub:
    case SdvmInstFloat32x4Mul:
    case SdvmInstFloat32x4Div:
    case SdvmInstFloat32x4Min:
    case SdvmInstFloat32x4Max:
    case SdvmInstFloat64x2Add:
    case SdvmInstFloat64x2Sub:
    case SdvmInstFloat64x2Mul:
    case SdvmInstFloat64x2Div:
    case SdvmInstFloat64x2Min:
    case SdvmInstFloat64x2Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(16);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(16);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(16);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstFloat32x4Sqrt:
    case SdvmInstFloat32x4Floor:
    case SdvmInstFloat32x4Ceil:
    case SdvmInstFloat32x4Truncate:
    case SdvmInstFloat32x4Round:
    case SdvmInstFloat64x2Sqrt:
    case SdvmInstFloat64x2Floor:
    case SdvmInstFloat64x2Ceil:
    case SdvmInstFloat64x2Truncate:
    case SdvmInstFloat64x2Round:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(16);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(16);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstFloat64Add:
    case SdvmInstFloat64Sub:
    case SdvmInstFloat64Mul:
    case SdvmInstFloat64Div:
    case SdvmInstFloat64Min:
    case SdvmInstFloat64Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstFloat64Sqrt:
    case SdvmInstFloat64Floor:
    case SdvmInstFloat64Ceil:
    case SdvmInstFloat64Truncate:
    case SdvmInstFloat64Round:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstFloat64Equals:
    case SdvmInstFloat64NotEquals:
    case SdvmInstFloat64LessThan:
    case SdvmInstFloat64LessOrEquals:
    case SdvmInstFloat64GreaterThan:
    case SdvmInstFloat64GreaterOrEquals:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_integerRegister(1);
        return;

    case SdvmInstFloat64x4Add:
    case SdvmInstFloat64x4Sub:
    case SdvmInstFloat64x4Mul:
    case SdvmInstFloat64x4Div:
    case SdvmInstFloat64x4Min:
    case SdvmInstFloat64x4Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegisterPair(16, 16);
        instruction->arg1Location = sdvm_compilerLocation_vectorFloatRegisterPair(16, 16);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegisterPair(16, 16);
        instruction->allowArg0DestinationShare = true;
        return;
    case SdvmInstFloat64x4Sqrt:
    case SdvmInstFloat64x4Floor:
    case SdvmInstFloat64x4Ceil:
    case SdvmInstFloat64x4Truncate:
    case SdvmInstFloat64x4Round:
        instruction->arg0Location = sdvm_compilerLocation_vectorFloatRegisterPair(16, 16);
        instruction->destinationLocation = sdvm_compilerLocation_vectorFloatRegisterPair(16, 16);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstInt32x2Add:
    case SdvmInstInt32x2Sub:
    case SdvmInstInt32x2Mul:
    case SdvmInstInt32x2And:
    case SdvmInstInt32x2Or:
    case SdvmInstInt32x2Xor:
    case SdvmInstInt32x2Asr:
    case SdvmInstInt32x2Lsl:
    case SdvmInstInt32x2Lsr:
    case SdvmInstInt32x2Min:
    case SdvmInstInt32x2Max:
    case SdvmInstUInt32x2Add:
    case SdvmInstUInt32x2Sub:
    case SdvmInstUInt32x2Mul:
    case SdvmInstUInt32x2And:
    case SdvmInstUInt32x2Or:
    case SdvmInstUInt32x2Xor:
    case SdvmInstUInt32x2Asr:
    case SdvmInstUInt32x2Lsl:
    case SdvmInstUInt32x2Lsr:
    case SdvmInstUInt32x2Min:
    case SdvmInstUInt32x2Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorIntegerRegister(8);
        instruction->arg1Location = sdvm_compilerLocation_vectorIntegerRegister(8);
        instruction->destinationLocation = sdvm_compilerLocation_vectorIntegerRegister(8);
        instruction->allowArg0DestinationShare = true;
        return;

    case SdvmInstInt32x4Add:
    case SdvmInstInt32x4Sub:
    case SdvmInstInt32x4Mul:
    case SdvmInstInt32x4And:
    case SdvmInstInt32x4Or:
    case SdvmInstInt32x4Xor:
    case SdvmInstInt32x4Asr:
    case SdvmInstInt32x4Lsl:
    case SdvmInstInt32x4Lsr:
    case SdvmInstInt32x4Min:
    case SdvmInstInt32x4Max:
    case SdvmInstUInt32x4Add:
    case SdvmInstUInt32x4Sub:
    case SdvmInstUInt32x4Mul:
    case SdvmInstUInt32x4And:
    case SdvmInstUInt32x4Or:
    case SdvmInstUInt32x4Xor:
    case SdvmInstUInt32x4Asr:
    case SdvmInstUInt32x4Lsl:
    case SdvmInstUInt32x4Lsr:
    case SdvmInstUInt32x4Min:
    case SdvmInstUInt32x4Max:
        instruction->arg0Location = sdvm_compilerLocation_vectorIntegerRegister(16);
        instruction->arg1Location = sdvm_compilerLocation_vectorIntegerRegister(16);
        instruction->destinationLocation = sdvm_compilerLocation_vectorIntegerRegister(16);
        instruction->allowArg0DestinationShare = true;
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
            sdvm_compiler_x64_computeInstructionLocationConstraints(state, instruction);
            ++i;
        }
    }
}

#pragma endregion X86_RegisterConstraints

#pragma region X86_InstructionPatterns

static bool sdvm_compiler_x86_comparisonAndBranchPredicate(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)state;
    (void)count;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;
    return (uint32_t)branch->decoding.instruction.arg0 == comparison->index;
}

static void sdvm_compiler_x86_int8ComparisonAndBranchConstraints(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;
    sdvm_compilerInstruction_t *arg1 = state->instructions + comparison->decoding.instruction.arg1;
    sdvm_compilerInstruction_t *branchDestination = state->instructions + branch->decoding.instruction.arg1;

    comparison->arg0Location = sdvm_compilerLocation_integerRegister(1);
    comparison->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(1, arg1);
    branch->arg1Location = branchDestination->location;
}

static bool sdvm_compiler_x86_int8ComparisonAndJumpIfTrueCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp8RegImm8(compiler, comparison->arg0Location.firstRegister.value, (int8_t)comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp8RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static bool sdvm_compiler_x86_int8ComparisonAndJumpIfFalseCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp8RegImm8(compiler, comparison->arg0Location.firstRegister.value, (int8_t)comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp8RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnInverseCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static void sdvm_compiler_x86_int16ComparisonAndBranchConstraints(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;
    sdvm_compilerInstruction_t *arg1 = state->instructions + comparison->decoding.instruction.arg1;
    sdvm_compilerInstruction_t *branchDestination = state->instructions + branch->decoding.instruction.arg1;

    comparison->arg0Location = sdvm_compilerLocation_integerRegister(2);
    comparison->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(2, arg1);
    branch->arg1Location = branchDestination->location;
}

static bool sdvm_compiler_x86_int16ComparisonAndJumpIfTrueCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp16RegImm16(compiler, comparison->arg0Location.firstRegister.value, (int16_t)comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp16RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static bool sdvm_compiler_x86_int16ComparisonAndJumpIfFalseCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp16RegImm16(compiler, comparison->arg0Location.firstRegister.value, (int16_t)comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp16RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnInverseCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static void sdvm_compiler_x86_int32ComparisonAndBranchConstraints(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;
    sdvm_compilerInstruction_t *arg1 = state->instructions + comparison->decoding.instruction.arg1;
    sdvm_compilerInstruction_t *branchDestination = state->instructions + branch->decoding.instruction.arg1;

    comparison->arg0Location = sdvm_compilerLocation_integerRegister(4);
    comparison->arg1Location = sdvm_compilerLocation_x86_intRegOrImm32(4, arg1);
    branch->arg1Location = branchDestination->location;
}

static bool sdvm_compiler_x86_int32ComparisonAndJumpIfTrueCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp32RegImm32(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp32RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static bool sdvm_compiler_x86_int32ComparisonAndJumpIfFalseCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp32RegImm32(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp32RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnInverseCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static void sdvm_compiler_x86_int64ComparisonAndBranchConstraints(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;
    sdvm_compilerInstruction_t *arg1 = state->instructions + comparison->decoding.instruction.arg1;
    sdvm_compilerInstruction_t *branchDestination = state->instructions + branch->decoding.instruction.arg1;

    comparison->arg0Location = sdvm_compilerLocation_integerRegister(8);
    comparison->arg1Location = sdvm_compilerLocation_x64_intRegOrImmS32(8, arg1);
    branch->arg1Location = branchDestination->location;
}

static bool sdvm_compiler_x86_int64ComparisonAndJumpIfTrueCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp64RegImmS32(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp64RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static bool sdvm_compiler_x86_int64ComparisonAndJumpIfFalseCodegen(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions)
{
    (void)count;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compilerInstruction_t *comparison = instructions;
    sdvm_compilerInstruction_t *branch = instructions + 1;

    if(sdvm_compilerLocationKind_isImmediate(comparison->arg1Location.kind))
        sdvm_compiler_x86_cmp64RegImmS32(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.immediateS32);
    else
        sdvm_compiler_x86_cmp64RegReg(compiler, comparison->arg0Location.firstRegister.value, comparison->arg1Location.firstRegister.value);

    sdvm_compiler_x86_jumpOnInverseCondition(compiler, branch->arg1Location.immediateLabel, sdvm_instruction_typeIsSigned(comparison->decoding.instruction.arg0Type), comparison->decoding.baseOpcode);
    return true;
}

static sdvm_compilerInstructionPattern_t sdvm_x64_instructionPatterns[] = {
#define COMPARISON_BRANCH_PATTERN(typePrefix, op) \
    {.size = 2, .opcodes = {op, SdvmInstJumpIfTrue}, .predicate = sdvm_compiler_x86_comparisonAndBranchPredicate, .constraints = sdvm_compiler_x86_ ## typePrefix ## ComparisonAndBranchConstraints, .generator = sdvm_compiler_x86_## typePrefix ##ComparisonAndJumpIfTrueCodegen },\
    {.size = 2, .opcodes = {op, SdvmInstJumpIfFalse}, .predicate = sdvm_compiler_x86_comparisonAndBranchPredicate, .constraints = sdvm_compiler_x86_ ## typePrefix ## ComparisonAndBranchConstraints, .generator = sdvm_compiler_x86_## typePrefix ##ComparisonAndJumpIfFalseCodegen }

    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8Equals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8NotEquals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8LessThan),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8GreaterThan),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstInt8GreaterOrEquals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8Equals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8NotEquals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8LessThan),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8GreaterThan),
    COMPARISON_BRANCH_PATTERN(int8, SdvmInstUInt8GreaterOrEquals),

    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16Equals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16NotEquals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16LessThan),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16GreaterThan),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstInt16GreaterOrEquals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16Equals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16NotEquals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16LessThan),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16GreaterThan),
    COMPARISON_BRANCH_PATTERN(int16, SdvmInstUInt16GreaterOrEquals),

    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32Equals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32NotEquals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32LessThan),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32GreaterThan),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstInt32GreaterOrEquals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32Equals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32NotEquals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32LessThan),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32GreaterThan),
    COMPARISON_BRANCH_PATTERN(int32, SdvmInstUInt32GreaterOrEquals),

    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64Equals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64NotEquals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64LessThan),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64GreaterThan),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstInt64GreaterOrEquals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64Equals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64NotEquals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64LessThan),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64LessOrEquals),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64GreaterThan),
    COMPARISON_BRANCH_PATTERN(int64, SdvmInstUInt64GreaterOrEquals),
};


static sdvm_compilerInstructionPatternTable_t sdvm_x64_instructionPatternTable = {
    .patternCount = SDVM_C_ARRAY_SIZE(sdvm_x64_instructionPatterns),
    .patterns = sdvm_x64_instructionPatterns
};

#pragma endregion

#pragma region X86_CodeGeneration

void sdvm_compiler_x64_ensureCIE(sdvm_moduleCompilationState_t *state)
{
    if(!state->compiler->target->usesEHFrame)
        return;

    if(state->hasEmittedCIE)
        return;

    sdvm_dwarf_cfi_builder_t *cfi = &state->cfi;

    sdvm_dwarf_cie_t ehCie = {0};
    ehCie.codeAlignmentFactor = 1;
    ehCie.dataAlignmentFactor = -8;
    ehCie.pointerSize = 8;
    ehCie.returnAddressRegister = DW_X64_REG_RA;
    cfi->section = &state->compiler->ehFrameSection;
    cfi->pointerSize = 8;
    cfi->initialStackFrameSize = 1; // Return address
    cfi->stackPointerRegister = DW_X64_REG_RSP;

    sdvm_dwarf_cfi_beginCIE(cfi, &ehCie);
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, DW_X64_REG_RSP, 1);
    sdvm_dwarf_cfi_registerValueAtFactoredOffset(cfi, DW_X64_REG_RA, 1);
    sdvm_dwarf_cfi_endCIE(cfi);

    state->hasEmittedCIE = true;
}

void sdvm_compiler_x64_seh_begin(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t functionSymbol)
{
    sdvm_seh_builder_t *seh = &compiler->seh;
    if(!seh->unwindCodes.data)
        sdvm_dynarray_initialize(&compiler->seh.unwindCodes, 2, 256);
    sdvm_dynarray_clear(&compiler->seh.unwindCodes);
    seh->functionSymbol = functionSymbol;
    seh->startPC = sdvm_compiler_getCurrentPC(compiler);
    seh->frameRegister = 0;
    seh->frameOffset = 0;
}

void sdvm_compiler_x64_seh_endPrologue(sdvm_compiler_t *compiler)
{
    compiler->seh.prologueEndPC = (uint32_t)sdvm_compiler_getCurrentPC(compiler);
}

void sdvm_compiler_x64_seh_op(sdvm_compiler_t *compiler, uint8_t opcode, uint8_t operationInfo)
{
    uint8_t prologueOffset = sdvm_compiler_getCurrentPC(compiler) - compiler->seh.startPC;
    uint8_t operation = (operationInfo << 4) | opcode;
    uint16_t code = prologueOffset | (operation << 8);
    sdvm_dynarray_addAll(&compiler->seh.unwindCodes, 2, &code);
}

void sdvm_compiler_x64_seh_op_pushNonVol(sdvm_compiler_t *compiler, uint8_t reg)
{
    sdvm_compiler_x64_seh_op(compiler, /*UWOP_PUSH_NONVOL */0 , reg);
}

void sdvm_compiler_x64_seh_op_setFPReg(sdvm_compiler_t *compiler, uint8_t reg, size_t offset)
{
    SDVM_ASSERT((offset % 16) == 0);
    compiler->seh.frameRegister = reg;
    compiler->seh.frameOffset = offset / 16;
    sdvm_compiler_x64_seh_op(compiler, /* UWOP_SET_FPREG */3, 0);
}

void sdvm_compiler_x64_seh_op_alloc(sdvm_compiler_t *compiler, size_t amount)
{
    if(amount == 0) return;

    SDVM_ASSERT((amount % 8) == 0);
    if(amount <= 128)
    {
        sdvm_compiler_x64_seh_op(compiler, /* UWOP_ALLOC_SMALL */2, (uint8_t)(amount/8 - 1));
    }
    else if(amount <= 512*1024 - 8)
    {
        size_t encodedAmount = amount / 8;
        SDVM_ASSERT(encodedAmount <= 0xFFFF);
        uint16_t encodedAmountU16 = (uint16_t)encodedAmount;
        sdvm_dynarray_addAll(&compiler->seh.unwindCodes, 2, &encodedAmountU16);
        sdvm_compiler_x64_seh_op(compiler, /* UWOP_ALLOC_LARGE */1, 0);
    }
    else
    {
        abort();
    }
}

void sdvm_compiler_x64_seh_op_saveXMM(sdvm_compiler_t *compiler, uint8_t reg, size_t offset)
{
    SDVM_ASSERT((offset % 16) == 0);
    uint32_t offset16 = offset / 16;

    if(offset16 <= 0xFFFF)
    {
        uint16_t encodedOffset = (uint16_t)offset16;
        sdvm_dynarray_addAll(&compiler->seh.unwindCodes, 2, &encodedOffset);
        sdvm_compiler_x64_seh_op(compiler, /* UWOP_SAVE_XMM128 */8, reg);
    }
    else
    {
        uint16_t encodedOffsetLow = (uint16_t)offset16;
        uint16_t encodedOffsetHigh = (uint16_t)(offset16 >> 16);
        sdvm_dynarray_addAll(&compiler->seh.unwindCodes, 2, &encodedOffsetHigh);
        sdvm_dynarray_addAll(&compiler->seh.unwindCodes, 2, &encodedOffsetLow);
        sdvm_compiler_x64_seh_op(compiler, /* UWOP_SAVE_XMM128_FAR */9, reg);
    }
}

void sdvm_compiler_x64_seh_end(sdvm_compiler_t *compiler)
{
    sdvm_seh_builder_t *seh = &compiler->seh;

    sdvm_x86_win64_runtime_info_t runtimeInfo = {0};
    uint32_t runtimeInfoOffset = (uint32_t)compiler->pdataSection.contents.size;
    uint32_t unwindInfoOffset = (uint32_t)compiler->xdataSection.contents.size;

    sdvm_x86_win64_unwind_info_t unwindInfo = {
        .versionAndFlags = /*Version*/1  | (/* Flags*/0 << 3),
        .prologueSize = seh->prologueEndPC - seh->startPC,
        .unwindCodeCount = seh->unwindCodes.size,
        .frameRegisterAndOffset = (uint8_t) ((seh->frameRegister) | (seh->frameOffset << 4))
    };

    sdvm_dynarray_addAll(&compiler->xdataSection.contents, sizeof(unwindInfo), &unwindInfo);
    
    // Unwind codes must be sorted in descending order.
    const uint16_t *unwindCodes = (const uint16_t *)seh->unwindCodes.data;
    for(size_t i = 0; i < seh->unwindCodes.size; ++i)
        sdvm_dynarray_addAll(&compiler->xdataSection.contents, 2, unwindCodes + seh->unwindCodes.size - i - 1);

    // Pad the unwind codes.
    if(seh->unwindCodes.size % 2 != 0)
    {
        uint16_t zero = 0;
        sdvm_dynarray_addAll(&compiler->xdataSection.contents, 2, &zero);
    }

    // Function start address
    {
        sdvm_compilerRelocation_t relocation = {
            .kind = SdvmCompRelocationAbsolute32,
            .symbol = seh->functionSymbol,
            .addend = 0,
            .offset = runtimeInfoOffset
        };
        sdvm_dynarray_add(&compiler->pdataSection.relocations, &relocation);
    }

    // Function end address
    {
        sdvm_compilerRelocation_t relocation = {
            .kind = SdvmCompRelocationAbsolute32,
            .symbol = seh->functionSymbol,
            .addend = sdvm_compiler_getCurrentPC(compiler) - seh->startPC,
            .offset = runtimeInfoOffset + 4
        };
        sdvm_dynarray_add(&compiler->pdataSection.relocations, &relocation);
    }

    // Unwind info address
    {
        sdvm_compilerRelocation_t relocation = {
            .kind = SdvmCompRelocationAbsolute32,
            .symbol = compiler->xdataSection.symbolIndex,
            .addend = unwindInfoOffset,
            .offset = runtimeInfoOffset + 8
        };
        sdvm_dynarray_add(&compiler->pdataSection.relocations, &relocation);
    }

    sdvm_dynarray_addAll(&compiler->pdataSection.contents, sizeof(runtimeInfo), &runtimeInfo);
}

void sdvm_compiler_x64_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;

    bool usesDwarfEH = compiler->target->usesEHFrame;
    bool usesSEH = compiler->target->usesSEH;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;

    if(usesDwarfEH)
    {
        sdvm_compiler_x64_ensureCIE(state->moduleState);
        sdvm_dwarf_cfi_beginFDE(cfi, state->symbol, sdvm_compiler_getCurrentPC(compiler));
    }
    if(usesSEH)
        sdvm_compiler_x64_seh_begin(compiler, state->symbol);

    if(state->debugFunctionTableEntry)
        sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, SdvmDebugLineInfoKindBeginPrologue, state->debugFunctionTableEntry->declarationLineInfo);

    if(compiler->target->usesCET)
        sdvm_compiler_x86_endbr64(compiler);

    if(!state->requiresStackFrame)
    {
        if(usesDwarfEH)
            sdvm_dwarf_cfi_endPrologue(cfi);
        if(usesSEH)
            sdvm_compiler_x64_seh_endPrologue(compiler);

        return;
    }

    sdvm_compiler_x86_push(compiler, SDVM_X86_RBP);
    if(usesDwarfEH)
    {
        sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
        sdvm_dwarf_cfi_pushRegister(cfi, DW_X64_REG_RBP);
    }
    if(usesSEH)
        sdvm_compiler_x64_seh_op_pushNonVol(compiler, SDVM_X86_RBP);

    sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RBP, SDVM_X86_RSP);
    if(usesDwarfEH)
    {
        sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
        sdvm_dwarf_cfi_saveFramePointerInRegister(cfi, DW_X64_REG_RBP, 0);
    }
    if(usesSEH)
        sdvm_compiler_x64_seh_op_setFPReg(compiler, SDVM_X86_RBP, 0);

    // Preserved integer registers.
    for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedIntegerRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, reg))
        {
            sdvm_compiler_x86_push(compiler, reg);
            if(usesDwarfEH)
                sdvm_dwarf_cfi_pushRegister(cfi, sdvm_compiler_x64_mapIntegerRegisterToDwarf(reg));
            if(usesSEH)
                sdvm_compiler_x64_seh_op_pushNonVol(compiler, reg);
        }
    }

    int32_t stackSubtractionAmount = state->calloutStackSegment.endOffset - state->prologueStackSegment.endOffset;
    sdvm_compiler_x86_sub64RegImmS32(compiler, SDVM_X86_RSP, stackSubtractionAmount);
    if(usesDwarfEH)
        sdvm_dwarf_cfi_stackSizeAdvance(cfi, sdvm_compiler_getCurrentPC(compiler), stackSubtractionAmount);
    if(usesSEH)
        sdvm_compiler_x64_seh_op_alloc(compiler, stackSubtractionAmount);

    // Preserved vector registers.
    int32_t vectorOffset = state->calloutStackSegment.endOffset - state->vectorCallPreservedRegisterStackSegment.endOffset;
    for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedVectorRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedVectorRegisterSet, reg))
        {
            sdvm_compiler_x86_movapsRmoReg(compiler, SDVM_X86_RSP, vectorOffset, reg);
            if(usesSEH)
                sdvm_compiler_x64_seh_op_saveXMM(compiler, reg, vectorOffset);
            vectorOffset += 16;
        }
    }
    
    if(usesDwarfEH)
        sdvm_dwarf_cfi_endPrologue(cfi);

    if(usesSEH)
        sdvm_compiler_x64_seh_endPrologue(compiler);
}

void sdvm_compiler_x64_emitFunctionEnding(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;
    if(compiler->target->usesEHFrame)
        sdvm_dwarf_cfi_endFDE(&state->moduleState->cfi, sdvm_compiler_getCurrentPC(compiler));
    if(compiler->target->usesSEH)
        sdvm_compiler_x64_seh_end(compiler);
}

void sdvm_compiler_x64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;

    bool usesDwarfEH = compiler->target->usesEHFrame;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;

    if(!state->requiresStackFrame)
        return;

    if(usesDwarfEH)
        sdvm_dwarf_cfi_beginEpilogue(cfi);

    // Preserved vector registers.
    int32_t vectorOffset = state->stackFramePointerAnchorOffset - state->vectorCallPreservedRegisterStackSegment.endOffset;
    for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
    {
        sdvm_compilerRegisterValue_t reg = convention->callPreservedVectorRegisters[i];
        if(sdvm_registerSet_includes(&state->usedCallPreservedVectorRegisterSet, reg))
        {
            sdvm_compiler_x86_movapsRegRmo(compiler, reg, state->stackFrameRegister, vectorOffset);
            vectorOffset += 16;
        }
    }

    uint32_t pointerSize = compiler->pointerSize;
    if(state->prologueStackSegment.size > pointerSize * 2)
    {
        int32_t restoreOffset = state->stackFramePointerAnchorOffset - state->prologueStackSegment.endOffset;
        sdvm_compiler_x86_lea64RegRmo(compiler, SDVM_X86_RSP, SDVM_X86_RBP, restoreOffset);
        if(usesDwarfEH)
        {
            sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
            sdvm_dwarf_cfi_restoreFramePointer(cfi, restoreOffset);
        }

        for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
        {
            sdvm_compilerRegisterValue_t reg = convention->callPreservedIntegerRegisters[convention->callPreservedIntegerRegisterCount - i - 1];
            if(sdvm_registerSet_includes(&state->usedCallPreservedIntegerRegisterSet, reg))
            {
                sdvm_compiler_x86_pop(compiler, reg);
                if(usesDwarfEH)
                {
                    sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
                    sdvm_dwarf_cfi_popRegister(cfi, sdvm_compiler_x64_mapIntegerRegisterToDwarf(reg));
                }
            }
        }
    }
    else
    {
        sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RSP, SDVM_X86_RBP);
        if(usesDwarfEH)
        {
            sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
            sdvm_dwarf_cfi_restoreFramePointer(cfi, 0);
        }
    }

    sdvm_compiler_x86_pop(compiler, SDVM_X86_RBP);

    if(usesDwarfEH)
    {
        sdvm_dwarf_cfi_setPC(cfi, sdvm_compiler_getCurrentPC(compiler));
        sdvm_dwarf_cfi_popRegister(cfi, DW_X64_REG_RBP);

        sdvm_dwarf_cfi_endEpilogue(cfi);
    }
}

void sdvm_compiler_x64_emitMemoryToMemoryFixedSizedMove(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t sourcePointer, int32_t sourcePointerOffset, sdvm_x86_registerIndex_t destinationPointer, int32_t destinationPointerOffset, size_t copySize, const sdvm_compilerScratchMoveRegisters_t *scratchMoveRegister)
{
    SDVM_ASSERT(scratchMoveRegister->isValid);
    SDVM_ASSERT(scratchMoveRegister->kind == SdvmCompRegisterKindInteger);
    sdvm_compilerRegisterValue_t scratchRegister = scratchMoveRegister->value;

    size_t offset = 0;
    while(offset < copySize)
    {
        size_t remainingSize = copySize - offset;
        if(remainingSize >= 8)
        {
            sdvm_compiler_x86_mov64RegRmo(compiler, scratchRegister, sourcePointer, (int32_t)(sourcePointerOffset + offset));
            sdvm_compiler_x86_mov64RmoReg(compiler, destinationPointer, (int32_t)(destinationPointerOffset + offset), scratchRegister);
            offset += 8;
        }
        else if(remainingSize >= 4)
        {
            sdvm_compiler_x86_mov32RegRmo(compiler, scratchRegister, sourcePointer, (int32_t)(sourcePointerOffset + offset));
            sdvm_compiler_x86_mov32RmoReg(compiler, destinationPointer, (int32_t)(destinationPointerOffset + offset), scratchRegister);
            offset += 4;
        }
        else if(remainingSize >= 2)
        {
            sdvm_compiler_x86_movzxReg32Rmo16(compiler, scratchRegister, sourcePointer, (int32_t)(sourcePointerOffset + offset));
            sdvm_compiler_x86_mov16RmoReg(compiler, destinationPointer, (int32_t)(destinationPointerOffset + offset), scratchRegister);
            offset += 2;
        }
        else
        {
            sdvm_compiler_x86_movzxReg32Rmo8(compiler, scratchRegister, sourcePointer, (int32_t)(sourcePointerOffset + offset));
            sdvm_compiler_x86_mov8RmoReg(compiler, destinationPointer, (int32_t)(destinationPointerOffset + offset), scratchRegister);
            offset += 1;
        }
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        sdvm_compiler_x86_xor32RegReg(compiler, reg->value, reg->value);
        return;
    case SdvmCompLocationImmediateS32:
        sdvm_compiler_x86_mov64RegImmS32(compiler, reg->value, sourceLocation->immediateS32);
        return;
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateU32:
        sdvm_compiler_x86_mov32RegImm32(compiler, reg->value, sourceLocation->immediateU32);
        return;
    case SdvmCompLocationImmediateS64:
        sdvm_compiler_x86_mov64RegImmS64(compiler, reg->value, sourceLocation->immediateS64);
        return;
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateU64:
        sdvm_compiler_x86_mov64RegImmU64(compiler, reg->value, sourceLocation->immediateU64);
        return;
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        if(sourceLocation->firstRegister.size <= 4)
            sdvm_compiler_x86_mov32RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        else
            sdvm_compiler_x86_mov64RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        return;
    case SdvmCompLocationStack:
    case SdvmCompLocationStackPair:
        switch(reg->size)
        {
        case 1:
            if(sourceLocation->isSigned)
                sdvm_compiler_x86_movsxReg32Rmo8(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                sdvm_compiler_x86_movzxReg32Rmo8(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        case 2:
            if(sourceLocation->isSigned)
                sdvm_compiler_x86_movsxReg32Rmo16(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            else
                sdvm_compiler_x86_movzxReg32Rmo16(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        case 4:
            sdvm_compiler_x86_mov32RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        case 8:
            sdvm_compiler_x86_mov64RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        default:
            abort();
        }
    case SdvmCompLocationStackAddress:
        switch(reg->size)
        {
        case 1:
        case 2:
        case 4:
            sdvm_compiler_x86_lea32RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        case 8:
            sdvm_compiler_x86_lea64RegRmo(compiler, reg->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            return;
        default:
            abort();
        }

    case SdvmCompLocationLocalSymbolValue:
        {
            switch(reg->size)
            {
            case 4:
                sdvm_compiler_x86_lea32RegLsv(compiler, reg->value, sourceLocation->symbolHandle, (int32_t)sourceLocation->symbolOffset);
                return;
            case 8:
                sdvm_compiler_x86_lea64RegLsv(compiler, reg->value, sourceLocation->symbolHandle, (int32_t)sourceLocation->symbolOffset);
                return;
            default:
                abort();
            }
        }
    case SdvmCompLocationGlobalSymbolValue:
        {
            switch(reg->size)
            {
            case 4:
                sdvm_compiler_x86_mov32RegGsv(compiler, reg->value, sourceLocation->symbolHandle, (int32_t)sourceLocation->symbolOffset);
                return;
            case 8:
                sdvm_compiler_x86_mov64RegGsv(compiler, reg->value, sourceLocation->symbolHandle, (int32_t)sourceLocation->symbolOffset);
                return;
            default:
                abort();
            }
        }
    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        sdvm_compiler_x86_xorpsRegReg(compiler, reg->value, reg->value);
        return;
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        sdvm_compiler_x86_movapsRegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        return;
    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        sdvm_compiler_x86_movdqaRegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        return;
    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(reg->kind)
    {
    case SdvmCompRegisterKindInteger:
        sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, reg);
        return;
    case SdvmCompRegisterKindFloat:
    case SdvmCompRegisterKindVectorFloat:
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatRegister(compiler, sourceLocation, reg);
        return;
    case SdvmCompRegisterKindVectorInteger:
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerRegister(compiler, sourceLocation, reg);
        return;
    default:
        abort();
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
        sdvm_compiler_x86_xor32RegReg(compiler, secondRegister->value, secondRegister->value);
        return;

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
                sdvm_compiler_x86_xchg64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }
            else if(isSecondInFirst)
            {
                sdvm_compiler_x86_mov64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
                sdvm_compiler_x86_mov64RegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
            }
            else
            {
                sdvm_compiler_x86_mov64RegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
                sdvm_compiler_x86_mov64RegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }

            return;
        }

    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
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
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatRegister(compiler, sourceLocation, firstRegister);
        sdvm_compiler_x86_xorpsRegReg(compiler, secondRegister->value, secondRegister->value);
        return;

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
                // XOR Swap: See https://en.wikipedia.org/wiki/XOR_swap_algorithm [April 2024]
                sdvm_compiler_x86_xorpsRegReg(compiler, destFirstRegisterValue, destSecondRegisterValue);
                sdvm_compiler_x86_xorpsRegReg(compiler, destSecondRegisterValue, destFirstRegisterValue);
                sdvm_compiler_x86_xorpsRegReg(compiler, destFirstRegisterValue, destSecondRegisterValue);
            }
            else if(isSecondInFirst)
            {
                sdvm_compiler_x86_movapsRegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
                sdvm_compiler_x86_movapsRegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
            }
            else
            {
                sdvm_compiler_x86_movapsRegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
                sdvm_compiler_x86_movapsRegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }

            return;
        }
    case SdvmCompLocationStack:
        switch(sourceLocation->firstStackLocation.size)
        {
        case 32:
            sdvm_compiler_x86_movapsRegRmo(compiler, firstRegister->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            sdvm_compiler_x86_movapsRegRmo(compiler, secondRegister->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset + 16);
            return;
        default:
            abort();
        }

    default: abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
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
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerRegister(compiler, sourceLocation, firstRegister);
        sdvm_compiler_x86_pxorRegReg(compiler, secondRegister->value, secondRegister->value);
        return;

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
                // XOR Swap: See https://en.wikipedia.org/wiki/XOR_swap_algorithm [April 2024]
                sdvm_compiler_x86_pxorRegReg(compiler, destFirstRegisterValue, destSecondRegisterValue);
                sdvm_compiler_x86_pxorRegReg(compiler, destSecondRegisterValue, destFirstRegisterValue);
                sdvm_compiler_x86_pxorRegReg(compiler, destFirstRegisterValue, destSecondRegisterValue);
            }
            else if(isSecondInFirst)
            {
                sdvm_compiler_x86_movdqaRegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
                sdvm_compiler_x86_movdqaRegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
            }
            else
            {
                sdvm_compiler_x86_movdqaRegReg(compiler, destFirstRegisterValue, sourceFirstRegisterValue);
                sdvm_compiler_x86_movdqaRegReg(compiler, destSecondRegisterValue, sourceSecondRegisterValue);
            }

            return;
        }
    case SdvmCompLocationStack:
        switch(sourceLocation->firstStackLocation.size)
        {
        case 32:
            sdvm_compiler_x86_movdqaRegRmo(compiler, firstRegister->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset);
            sdvm_compiler_x86_movdqaRegRmo(compiler, secondRegister->value, sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset + 16);
            return;
        default:
            abort();
        }

    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    switch(firstRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegisterPair(compiler, sourceLocation, firstRegister, secondRegister);
        return;
    case SdvmCompRegisterKindVectorFloat:
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloatRegisterPair(compiler, sourceLocation, firstRegister, secondRegister);
        return;
    case SdvmCompRegisterKindVectorInteger:
        sdvm_compiler_x64_emitMoveFromLocationIntoVectorIntegerRegisterPair(compiler, sourceLocation, firstRegister, secondRegister);
        return;
    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(sdvm_compiler_t *compiler, const sdvm_compilerRegister_t *sourceRegister, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        switch(sourceRegister->size)
        {
        case 1:
            sdvm_compiler_x86_mov8RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        case 2:
            sdvm_compiler_x86_mov16RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        case 4:
            sdvm_compiler_x86_mov32RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        case 8:
            sdvm_compiler_x86_mov64RmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        default:
            abort();
        }
    case SdvmCompRegisterKindFloat:
    case SdvmCompRegisterKindVectorFloat:
        switch(sourceRegister->size)
        {
        case 4:
            sdvm_compiler_x86_movssRmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        case 8:
            sdvm_compiler_x86_movsdRmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        case 16:
            sdvm_compiler_x86_movapsRmoReg(compiler, stackLocation->framePointerRegister, stackLocation->framePointerOffset, sourceRegister->value);
            return;
        default:
            abort();
        }
    case SdvmCompRegisterKindVectorInteger:
        // TODO: Implement this
        abort();

    default:
        abort();
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoStack(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerLocation_t *destinationLocation, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
        sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);
        return;
    case SdvmCompLocationRegisterPair:
        {
            sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);

            sdvm_compilerStackLocation_t nextLocation = *stackLocation;
            nextLocation.segmentOffset += sourceLocation->firstRegister.size;
            nextLocation.framePointerOffset += sourceLocation->firstRegister.size;

            sdvm_compiler_x64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->secondRegister, &nextLocation);
            return;
        }
    case SdvmCompLocationStack:
        SDVM_ASSERT(destinationLocation->scratchMoveRegister.isValid);
        sdvm_compiler_x64_emitMemoryToMemoryFixedSizedMove(compiler,
            sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset,
            destinationLocation->firstStackLocation.framePointerRegister, destinationLocation->firstStackLocation.framePointerOffset,
            sourceLocation->firstStackLocation.size <= destinationLocation->firstStackLocation.size ? sourceLocation->firstStackLocation.size : destinationLocation->firstStackLocation.size,
            &destinationLocation->scratchMoveRegister);
        return;
    default:
        abort();
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
        sdvm_compiler_x64_emitMoveFromLocationIntoRegister(compiler, sourceLocation, &destinationLocation->firstRegister);
        return;
    case SdvmCompLocationRegisterPair:
        sdvm_compiler_x64_emitMoveFromLocationIntoRegisterPair(compiler, sourceLocation, &destinationLocation->firstRegister, &destinationLocation->secondRegister);
        return;
    case SdvmCompLocationStack:
        sdvm_compiler_x64_emitMoveFromLocationIntoStack(compiler, sourceLocation, destinationLocation, &destinationLocation->firstStackLocation);
        return;
    case SdvmCompLocationStackPair:
        abort();
        return;
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
        abort();
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
    case SdvmInstCallFloat32x2:
    case SdvmInstCallFloat32x4:
    case SdvmInstCallFloat64x2:
    case SdvmInstCallFloat64x4:
    case SdvmInstCallInt32x2:
    case SdvmInstCallInt32x4:
    case SdvmInstCallUInt32x2:
    case SdvmInstCallUInt32x4:
        if(arg0->kind == SdvmCompLocationGlobalSymbolValue)
            sdvm_compiler_x86_callGsv(compiler, arg0->symbolHandle, 0);
        else if(arg0->kind == SdvmCompLocationLocalSymbolValue)
            sdvm_compiler_x86_callLsv(compiler, arg0->symbolHandle, (int32_t)arg0->symbolOffset);
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
    case SdvmInstCallClosureFloat32x2:
    case SdvmInstCallClosureFloat32x4:
    case SdvmInstCallClosureFloat64x2:
    case SdvmInstCallClosureFloat64x4:
    case SdvmInstCallClosureInt32x2:
    case SdvmInstCallClosureInt32x4:
    case SdvmInstCallClosureUInt32x2:
    case SdvmInstCallClosureUInt32x4:
        sdvm_compiler_x86_callRmo(compiler, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_movsxReg32Rmo8(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_movsxReg32Rmo8(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_movzxReg32Rmo8(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_movzxReg32Rmo8(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_movsxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_movsxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_movzxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_movzxReg32Rmo16(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt32:
    case SdvmInstLoadUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov32RegRmo(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_mov32RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;
    case SdvmInstLoadInt64:
    case SdvmInstLoadUInt64:
    case SdvmInstLoadPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
        else
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
        return true;

    case SdvmInstLoadGCPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset);
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->secondRegister.value, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + 8);
        }
        else
        {
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->firstRegister.value, arg0->firstRegister.value, 0);
            sdvm_compiler_x86_mov64RegRmo(compiler, dest->secondRegister.value, arg0->firstRegister.value, 8);
        }
        return true;

    case SdvmInstStoreInt8:
    case SdvmInstStoreUInt8:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov8RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
        else
            sdvm_compiler_x86_mov8RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;
    case SdvmInstStoreInt16:
    case SdvmInstStoreUInt16:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov16RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
        else
            sdvm_compiler_x86_mov16RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;
    case SdvmInstStoreInt32:
    case SdvmInstStoreUInt32:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov32RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
        else
            sdvm_compiler_x86_mov32RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;
    case SdvmInstStoreInt64:
    case SdvmInstStoreUInt64:
    case SdvmInstStorePointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
        else
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
        return true;

    case SdvmInstStoreGCPointer:
        if(arg0->kind == SdvmCompLocationStackAddress)
        {
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset, arg1->firstRegister.value);
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstStackLocation.framePointerRegister, arg0->firstStackLocation.framePointerOffset + 8, arg1->secondRegister.value);
        }
        else
        {
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstRegister.value, 0, arg1->firstRegister.value);
            sdvm_compiler_x86_mov64RmoReg(compiler, arg0->firstRegister.value, 8, arg1->secondRegister.value);
        }
        return true;

    case SdvmInstPointerAddOffsetUInt32:
    case SdvmInstPointerAddOffsetInt64:
    case SdvmInstPointerAddOffsetUInt64:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add64RegImmS32(compiler, dest->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_add64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstMemcopyFixed:
    case SdvmInstMemcopyGCFixed:
        {
            sdvm_moduleMemoryDescriptorTableEntry_t *descriptor = state->module->memoryDescriptorTable + instruction->decoding.instruction.arg3;
            if(descriptor->alignment >= 8 && descriptor->size % 8 == 0)
            {
                sdvm_compiler_x86_rep(compiler);
                sdvm_compiler_x86_movsq(compiler);
            }
            else if(descriptor->alignment >= 4 && descriptor->size % 4 == 0)
            {
                sdvm_compiler_x86_rep(compiler);
                sdvm_compiler_x86_movsd(compiler);
            }
            else if(descriptor->alignment >= 2 && descriptor->size % 2 == 0)
            {
                sdvm_compiler_x86_rep(compiler);
                sdvm_compiler_x86_movsw(compiler);
            }
            else
            {
                sdvm_compiler_x86_rep(compiler);
                sdvm_compiler_x86_movsb(compiler);
            }
        }
        return true;

    case SdvmInstInt8Add:
    case SdvmInstUInt8Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_add8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8Sub:
    case SdvmInstUInt8Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sub8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sub8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8And:
    case SdvmInstUInt8And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_and8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_and8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8Or:
    case SdvmInstUInt8Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_or8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_or8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8Xor:
    case SdvmInstUInt8Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_xor8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_xor8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8Asr:
    case SdvmInstUInt8Asr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sar8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sar8RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt8Lsl:
    case SdvmInstUInt8Lsl:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shl8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shl8RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt8Lsr:
    case SdvmInstUInt8Lsr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shr8RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shr8RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt8Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovg32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmova32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt8Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovl32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt8Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp8RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovb32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt8Equals:
    case SdvmInstInt8NotEquals:
    case SdvmInstInt8LessThan:
    case SdvmInstInt8LessOrEquals:
    case SdvmInstInt8GreaterThan:
    case SdvmInstInt8GreaterOrEquals:
    case SdvmInstUInt8Equals:
    case SdvmInstUInt8NotEquals:
    case SdvmInstUInt8LessThan:
    case SdvmInstUInt8LessOrEquals:
    case SdvmInstUInt8GreaterThan:
    case SdvmInstUInt8GreaterOrEquals:
        sdvm_compiler_x86_xor32RegReg(compiler, dest->firstRegister.value, dest->firstRegister.value);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_cmp8RegImm8(compiler, arg0->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_cmp8RegReg(compiler, arg0->firstRegister.value, arg1->firstRegister.value);

        sdvm_compiler_x86_setByteOnCondition(compiler, dest->firstRegister.value, sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode);
        return true;

    case SdvmInstInt16Add:
    case SdvmInstUInt16Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_add16RegImm16(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_add16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Sub:
    case SdvmInstUInt16Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sub16RegImm16(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sub16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Mul:
    case SdvmInstUInt16Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocation_x64_isImmPowerOfTwo(arg1))
            sdvm_compiler_x86_shl16RegImm8(compiler, dest->firstRegister.value, sdvm_compilerLocation_x64_log2(arg1));
        else
            sdvm_compiler_x86_imul16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Div:
    case SdvmInstInt16Rem:
    case SdvmInstUInt16Div:
    case SdvmInstUInt16Rem:
        sdvm_compiler_x86_cwd(compiler);
        sdvm_compiler_x86_idiv16Reg(compiler, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16UDiv:
    case SdvmInstInt16URem:
    case SdvmInstUInt16UDiv:
    case SdvmInstUInt16URem:
        sdvm_compiler_x86_xor32RegReg(compiler, SDVM_X86_EDX, SDVM_X86_EDX);
        sdvm_compiler_x86_div16Reg(compiler, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16And:
    case SdvmInstUInt16And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_and16RegImm16(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_and16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Or:
    case SdvmInstUInt16Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_or16RegImm16(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_or16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Xor:
    case SdvmInstUInt16Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_xor16RegImm16(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_xor16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Asr:
    case SdvmInstUInt16Asr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sar16RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sar16RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt16Lsl:
    case SdvmInstUInt16Lsl:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shl16RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shl16RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt16Lsr:
    case SdvmInstUInt16Lsr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shr16RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shr16RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt16Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovg32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt16Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmova32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt16Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovl32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt16Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp16RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovb32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt16Equals:
    case SdvmInstInt16NotEquals:
    case SdvmInstInt16LessThan:
    case SdvmInstInt16LessOrEquals:
    case SdvmInstInt16GreaterThan:
    case SdvmInstInt16GreaterOrEquals:
    case SdvmInstUInt16Equals:
    case SdvmInstUInt16NotEquals:
    case SdvmInstUInt16LessThan:
    case SdvmInstUInt16LessOrEquals:
    case SdvmInstUInt16GreaterThan:
    case SdvmInstUInt16GreaterOrEquals:
        sdvm_compiler_x86_xor32RegReg(compiler, dest->firstRegister.value, dest->firstRegister.value);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_cmp16RegImm16(compiler, arg0->firstRegister.value, (int16_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_cmp16RegReg(compiler, arg0->firstRegister.value, arg1->firstRegister.value);

        sdvm_compiler_x86_setByteOnCondition(compiler, dest->firstRegister.value, sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode);
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
    case SdvmInstInt32Mul:
    case SdvmInstUInt32Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocation_x64_isImmPowerOfTwo(arg1))
            sdvm_compiler_x86_shl32RegImm8(compiler, dest->firstRegister.value, sdvm_compilerLocation_x64_log2(arg1));
        else
            sdvm_compiler_x86_imul32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Div:
    case SdvmInstInt32Rem:
    case SdvmInstUInt32Div:
    case SdvmInstUInt32Rem:
        sdvm_compiler_x86_cdq(compiler);
        sdvm_compiler_x86_idiv32Reg(compiler, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32UDiv:
    case SdvmInstInt32URem:
    case SdvmInstUInt32UDiv:
    case SdvmInstUInt32URem:
        sdvm_compiler_x86_xor32RegReg(compiler, SDVM_X86_EDX, SDVM_X86_EDX);
        sdvm_compiler_x86_div32Reg(compiler, arg1->firstRegister.value);
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
    case SdvmInstInt32Asr:
    case SdvmInstUInt32Asr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sar32RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sar32RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt32Lsl:
    case SdvmInstUInt32Lsl:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shl32RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shl32RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt32Lsr:
    case SdvmInstUInt32Lsr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shr32RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shr32RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt32Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovg32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt32Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmova32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovl32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt32Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovb32RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt32Equals:
    case SdvmInstInt32NotEquals:
    case SdvmInstInt32LessThan:
    case SdvmInstInt32LessOrEquals:
    case SdvmInstInt32GreaterThan:
    case SdvmInstInt32GreaterOrEquals:
    case SdvmInstUInt32Equals:
    case SdvmInstUInt32NotEquals:
    case SdvmInstUInt32LessThan:
    case SdvmInstUInt32LessOrEquals:
    case SdvmInstUInt32GreaterThan:
    case SdvmInstUInt32GreaterOrEquals:
        sdvm_compiler_x86_xor32RegReg(compiler, dest->firstRegister.value, dest->firstRegister.value);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_cmp32RegImm32(compiler, arg0->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_cmp32RegReg(compiler, arg0->firstRegister.value, arg1->firstRegister.value);

        sdvm_compiler_x86_setByteOnCondition(compiler, dest->firstRegister.value, sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode);
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
    case SdvmInstInt64Mul:
    case SdvmInstUInt64Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocation_x64_isImmPowerOfTwo(arg1))
            sdvm_compiler_x86_shl64RegImm8(compiler, dest->firstRegister.value, sdvm_compilerLocation_x64_log2(arg1));
        else
            sdvm_compiler_x86_imul64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64Div:
    case SdvmInstInt64Rem:
    case SdvmInstUInt64Div:
    case SdvmInstUInt64Rem:
        sdvm_compiler_x86_cqo(compiler);
        sdvm_compiler_x86_idiv64Reg(compiler, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64UDiv:
    case SdvmInstInt64URem:
    case SdvmInstUInt64UDiv:
    case SdvmInstUInt64URem:
        sdvm_compiler_x86_xor32RegReg(compiler, SDVM_X86_EDX, SDVM_X86_EDX);
        sdvm_compiler_x86_div64Reg(compiler, arg1->firstRegister.value);
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
    case SdvmInstInt64Asr:
    case SdvmInstUInt64Asr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_sar64RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_sar64RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt64Lsl:
    case SdvmInstUInt64Lsl:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shl64RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shl64RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt64Lsr:
    case SdvmInstUInt64Lsr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_shr64RegImm8(compiler, dest->firstRegister.value, (int8_t)arg1->immediateS32);
        else
            sdvm_compiler_x86_shr64RegCL(compiler, dest->firstRegister.value);
        return true;
    case SdvmInstInt64Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovg64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt64Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmova64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt64Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovl64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt64Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_cmp64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_cmovb64RegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
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
        sdvm_compiler_x86_xor32RegReg(compiler, dest->firstRegister.value, dest->firstRegister.value);
        if(sdvm_compilerLocationKind_isImmediate(arg1->kind))
            sdvm_compiler_x86_cmp64RegImmS32(compiler, arg0->firstRegister.value, arg1->immediateS32);
        else
            sdvm_compiler_x86_cmp64RegReg(compiler, arg0->firstRegister.value, arg1->firstRegister.value);

        sdvm_compiler_x86_setByteOnCondition(compiler, dest->firstRegister.value, sdvm_instruction_typeIsSigned(instruction->decoding.instruction.arg0Type), instruction->decoding.baseOpcode);
        return true;

    case SdvmInstFloat32Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_addssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_subssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_mulssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Div:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_divssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_maxssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_minssRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32Sqrt:
        sdvm_compiler_x86_sqrtssRegReg(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstFloat32x2Add:
    case SdvmInstFloat32x4Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_addpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Sub:
    case SdvmInstFloat32x4Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_subpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Mul:
    case SdvmInstFloat32x4Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_mulpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Div:
    case SdvmInstFloat32x4Div:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_divpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Max:
    case SdvmInstFloat32x4Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_maxpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Min:
    case SdvmInstFloat32x4Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_minpsRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat32x2Sqrt:
    case SdvmInstFloat32x4Sqrt:
        sdvm_compiler_x86_sqrtpsRegReg(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstFloat64Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_addsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_subsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_mulsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Div:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_divsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_maxsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_minsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64Sqrt:
        sdvm_compiler_x86_sqrtsdRegReg(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstFloat64x2Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_addpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_subpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_mulpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Div:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_divpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_maxpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_minpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstFloat64x2Sqrt:
        sdvm_compiler_x86_sqrtpdRegReg(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstFloat64x4Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_addpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_addpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_subpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_subpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_mulpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_mulpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Div:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_divpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_divpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_maxpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_maxpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_minpdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        sdvm_compiler_x86_minpdRegReg(compiler, dest->secondRegister.value, arg1->secondRegister.value);
        return true;
    case SdvmInstFloat64x4Sqrt:
        sdvm_compiler_x86_sqrtpdRegReg(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        sdvm_compiler_x86_sqrtpdRegReg(compiler, dest->secondRegister.value, arg0->secondRegister.value);
        return true;

    case SdvmInstInt32x2Add:
    case SdvmInstInt32x4Add:
    case SdvmInstUInt32x2Add:
    case SdvmInstUInt32x4Add:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_padddRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Sub:
    case SdvmInstInt32x4Sub:
    case SdvmInstUInt32x2Sub:
    case SdvmInstUInt32x4Sub:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_psubdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Mul:
    case SdvmInstInt32x4Mul:
    case SdvmInstUInt32x2Mul:
    case SdvmInstUInt32x4Mul:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pmulldRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2And:
    case SdvmInstInt32x4And:
    case SdvmInstUInt32x2And:
    case SdvmInstUInt32x4And:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pandRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Or:
    case SdvmInstInt32x4Or:
    case SdvmInstUInt32x2Or:
    case SdvmInstUInt32x4Or:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_porRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Xor:
    case SdvmInstInt32x4Xor:
    case SdvmInstUInt32x2Xor:
    case SdvmInstUInt32x4Xor:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pxorRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Lsl:
    case SdvmInstInt32x4Lsl:
    case SdvmInstUInt32x2Lsl:
    case SdvmInstUInt32x4Lsl:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pslldRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Lsr:
    case SdvmInstInt32x4Lsr:
    case SdvmInstUInt32x2Lsr:
    case SdvmInstUInt32x4Lsr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_psrldRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Asr:
    case SdvmInstInt32x4Asr:
    case SdvmInstUInt32x2Asr:
    case SdvmInstUInt32x4Asr:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_psradRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstInt32x2Max:
    case SdvmInstInt32x4Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pmaxsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt32x2Max:
    case SdvmInstUInt32x4Max:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pmaxudRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstInt32x2Min:
    case SdvmInstInt32x4Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pminsdRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;
    case SdvmInstUInt32x2Min:
    case SdvmInstUInt32x4Min:
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        sdvm_compiler_x86_pminudRegReg(compiler, dest->firstRegister.value, arg1->firstRegister.value);
        return true;

    case SdvmInstJump:
        sdvm_compiler_x86_jmpLabel(compiler, arg0->immediateLabel);
        return true;
    case SdvmInstJumpIfTrue:
        sdvm_compiler_x86_test32RegReg(compiler, arg0->firstRegister.value, arg0->firstRegister.value);
        sdvm_compiler_x86_jnzLabel(compiler, arg1->immediateLabel);
        return true;
    case SdvmInstJumpIfFalse:
        sdvm_compiler_x86_test32RegReg(compiler, arg0->firstRegister.value, arg0->firstRegister.value);
        sdvm_compiler_x86_jzLabel(compiler, arg1->immediateLabel);
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
        sdvm_compiler_x64_emitMoveFromLocationInto(compiler, arg0, dest);
        return true;

    case SdvmInstInt8_SignExtend_Int16:
    case SdvmInstInt8_SignExtend_Int32:
        sdvm_compiler_x86_movsxReg32Reg8(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt8_SignExtend_Int64:
        sdvm_compiler_x86_movsxReg64Reg8(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt16_SignExtend_Int32:
        sdvm_compiler_x86_movsxReg32Reg16(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt16_SignExtend_Int64:
        sdvm_compiler_x86_movsxReg64Reg16(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt32_SignExtend_Int64:
        sdvm_compiler_x86_movsxdReg64Reg32(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    case SdvmInstInt8_ZeroExtend_UInt16:
    case SdvmInstInt8_ZeroExtend_UInt32:
    case SdvmInstUInt8_ZeroExtend_Int16:
    case SdvmInstUInt8_ZeroExtend_Int32:
    case SdvmInstUInt8_ZeroExtend_UInt16:
    case SdvmInstUInt8_ZeroExtend_UInt32:
        sdvm_compiler_x86_movzxReg32Reg8(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt8_ZeroExtend_UInt64:
    case SdvmInstUInt8_ZeroExtend_Int64:
    case SdvmInstUInt8_ZeroExtend_UInt64:
        sdvm_compiler_x86_movzxReg64Reg8(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt16_ZeroExtend_UInt32:
    case SdvmInstUInt16_ZeroExtend_Int32:
    case SdvmInstUInt16_ZeroExtend_UInt32:
    case SdvmInstInt16_ZeroExtend_UInt64:
    case SdvmInstUInt16_ZeroExtend_Int64:
    case SdvmInstUInt16_ZeroExtend_UInt64:
        sdvm_compiler_x86_movzxReg32Reg16(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;
    case SdvmInstInt32_ZeroExtend_UInt64:
    case SdvmInstUInt32_ZeroExtend_Int64:
    case SdvmInstUInt32_ZeroExtend_UInt64:
        sdvm_compiler_x86_mov32RegReg_noOpt(compiler, dest->firstRegister.value, arg0->firstRegister.value);
        return true;

    default:
        abort();
    }
    return true;
}

void sdvm_compiler_x64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isExtensionData)
        return;

    if(instruction->isBackwardBranchDestination || instruction->isIndirectBranchDestination)
        sdvm_compiler_x86_alignReacheableCode(state->compiler);

    sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, SdvmDebugLineInfoKindStatement, instruction->debugSourceLineInfo);

    if(instruction->isIndirectBranchDestination && state->compiler->target->usesCET)
        sdvm_compiler_x86_endbr64(state->compiler);

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
        sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &arg0->location, &instruction->arg0Location);
    }

    if(startInstruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + startInstruction->decoding.instruction.arg1;
        sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &arg1->location, &instruction->arg1Location);
    }

    // Used for variadic callouts, memcopy fixed.
    sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &startInstruction->implicitArg0SourceLocation, &startInstruction->implicitArg0Location);

    // Emit the actual instruction operation
    if(instruction->pattern)
    {
        if(!instruction->pattern->generator(state, instruction->pattern->size, instruction))
            return;
    }
    else
    {
        if(!sdvm_compiler_x64_emitFunctionInstructionOperation(state, instruction))
            return;
    }

    // Emit the result moves.
    sdvm_compiler_x64_emitMoveFromLocationInto(state->compiler, &endInstruction->destinationLocation, &endInstruction->location);
}

void sdvm_compiler_x64_emitFunctionInstructions(sdvm_functionCompilationState_t *state)
{
    uint32_t i = 0;
    while(i < state->instructionCount)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_x64_emitFunctionInstruction(state, instruction);
        if(instruction->pattern)
            i += instruction->pattern->size;
        else
            ++i;
    }
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
        || state->temporarySegment.size > 0
        || state->calloutStackSegment.size > 0;

    uint32_t pointerSize = state->compiler->pointerSize;
    state->prologueStackSegment.size = pointerSize;
    state->prologueStackSegment.alignment = 16;

    if(state->requiresStackFrame)
    {
        // Frame pointer.
        state->prologueStackSegment.size += pointerSize;
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

    if(state->requiresStackFramePointer)
    {
        state->stackFrameRegister = SDVM_X86_RBP;
        state->stackFramePointerAnchorOffset = pointerSize * 2;
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

    if(state->compiler->verbose)
        sdvm_functionCompilationState_dump(state);

    // Align the function start symbol.
    sdvm_compiler_x86_alignUnreacheableCode(state->compiler);

    // Set the function symbol
    size_t startOffset = state->compiler->textSection.contents.size;
    state->debugInfo->startPC = startOffset;
    sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&state->compiler->symbolTable, state->symbol, state->compiler->textSection.symbolIndex, startOffset);

    // Emit the prologue.
    sdvm_compiler_x64_emitFunctionPrologue(state);

    // Emit the instructions.
    sdvm_compiler_x64_emitFunctionInstructions(state);

    // End the function.
    sdvm_compiler_x64_emitFunctionEnding(state);

    // Set the symbol size.
    size_t endOffset = state->compiler->textSection.contents.size;
    state->debugInfo->endPC = endOffset;
    sdvm_compilerSymbolTable_setSymbolSize(&state->compiler->symbolTable, state->symbol, endOffset - startOffset);
    sdvm_compiler_x86_alignUnreacheableCode(state->compiler);

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
    case SdvmCompRelocationSectionRelative32: return SDVM_R_X86_64_32;
    default: abort();
    }
}

uint16_t sdvm_compiler_x64_mapCoffRelocationApplyingAddend(sdvm_compilerRelocation_t *relocation, uint8_t *target)
{
    switch(relocation->kind)
    {
    case SdvmCompRelocationAbsolute32:
        *(uint32_t*)target = (uint32_t)relocation->addend;
        return SDVM_IMAGE_REL_AMD64_ADDR32;
    case SdvmCompRelocationAbsolute64:
        *(uint64_t*)target = (uint64_t)relocation->addend;
        return SDVM_IMAGE_REL_AMD64_ADDR64;
    case SdvmCompRelocationRelative32:
    case SdvmCompRelocationRelative32AtGot:
    case SdvmCompRelocationRelative32AtPlt:
        *(uint32_t*)target = (uint32_t)(relocation->addend + 4);
        return SDVM_IMAGE_REL_AMD64_REL32;
    case SdvmCompRelocationSectionRelative32:
        *(uint32_t*)target = (uint32_t)relocation->addend;
        return SDVM_IMAGE_REL_AMD64_SECREL;
    default: abort();
    }
}

static sdvm_compilerTarget_t sdvm_compilerTarget_x64_linux_pic = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_X86_64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_AMD64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_X86_64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_X86_ALL,
    .usesUnderscorePrefix = false,
    .usesCET = true,
    .usesPIC = true,
    .usesEHFrame = true,

    .defaultCC = &sdvm_x64_sysv_callingConvention,
    .cdeclCC = &sdvm_x64_sysv_callingConvention,
    .stdcallCC = &sdvm_x64_sysv_callingConvention,
    .apicall = &sdvm_x64_sysv_callingConvention,
    .thiscallCC = &sdvm_x64_sysv_callingConvention,
    .vectorcallCC = &sdvm_x64_sysv_callingConvention,

    .compileModuleFunction = sdvm_compiler_x64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_x64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_x64_mapCoffRelocationApplyingAddend,

    .instructionPatterns = &sdvm_x64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_x64_linux()
{
    return &sdvm_compilerTarget_x64_linux_pic;
}

static sdvm_compilerTarget_t sdvm_compilerTarget_x64_macosx = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeMachO,
    .elfMachine = SDVM_EM_X86_64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_AMD64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_X86_64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_X86_ALL,
    .usesUnderscorePrefix = true,
    .usesCET = false,
    .usesPIC = true,
    .usesEHFrame = true,

    .defaultCC = &sdvm_x64_sysv_callingConvention,
    .cdeclCC = &sdvm_x64_sysv_callingConvention,
    .stdcallCC = &sdvm_x64_sysv_callingConvention,
    .apicall = &sdvm_x64_sysv_callingConvention,
    .thiscallCC = &sdvm_x64_sysv_callingConvention,
    .vectorcallCC = &sdvm_x64_sysv_callingConvention,

    .compileModuleFunction = sdvm_compiler_x64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_x64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_x64_mapCoffRelocationApplyingAddend,

    .instructionPatterns = &sdvm_x64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_x64_macosx()
{
    return &sdvm_compilerTarget_x64_macosx;
}

static sdvm_compilerTarget_t sdvm_compilerTarget_x64_windows = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeCoff,
    .elfMachine = SDVM_EM_X86_64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_AMD64,
    .machoCpuType = SDVM_MACHO_CPU_TYPE_X86_64,
    .machoCpuSubtype = SDVM_MACHO_CPU_SUBTYPE_X86_ALL,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .usesPIC = false,
    .usesEHFrame = false,
    .usesSEH = true,

    .defaultCC = &sdvm_x64_win64_callingConvention,
    .cdeclCC = &sdvm_x64_win64_callingConvention,
    .stdcallCC = &sdvm_x64_win64_callingConvention,
    .apicall = &sdvm_x64_win64_callingConvention,
    .thiscallCC = &sdvm_x64_win64_callingConvention,
    .vectorcallCC = &sdvm_x64_win64_callingConvention,

    .compileModuleFunction = sdvm_compiler_x64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_x64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_x64_mapCoffRelocationApplyingAddend,

    .instructionPatterns = &sdvm_x64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_x64_windows()
{
    return &sdvm_compilerTarget_x64_windows;
}
