#include "compilerRiscV.h"
#include "assert.h"
#include "module.h"
#include "elf.h"
#include "coff.h"
#include "macho.h"
#include "dwarf.h"
#include "utils.h"
#include <string.h>

void sdvm_compiler_riscv64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state);

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

    .closureRegister = &sdvm_riscv64_X9,
    .closureGCRegister = &sdvm_riscv64_X10,

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

uint32_t sdvm_compiler_riscv_32_R_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, uint8_t funct7)
{
    return opcode | (rd << 7) | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | (funct7 << 25);
}

uint32_t sdvm_compiler_riscv_32_I_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, int16_t imm)
{
    return opcode | (rd << 7) | (funct3 << 12) | (rs1 << 15) | (imm << 11);
}

uint32_t sdvm_compiler_riscv_32_S_encode(uint8_t opcode, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, int16_t imm)
{
    int32_t immHigh = imm >> 5;
    int32_t immLow = imm & 31;
    return opcode | (immLow << 7) | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | (immHigh << 25);
}

uint32_t sdvm_compiler_riscv_32_B_encode(uint8_t opcode, uint8_t funct3, sdvm_riscv_registerIndex_t rs1, sdvm_riscv_registerIndex_t rs2, int16_t imm)
{
    int32_t immSign = (imm & (1<<12)) ? 1 : 0;
    int32_t immHigh = (imm >> 5) & 31;
    int32_t immLow = (imm >> 1) & 15;
    int32_t immExtraBit = (imm & (1<<11)) ? 1 : 0;
    return opcode | (((immLow<<1) | immExtraBit) << 7) | (funct3 << 12) | (rs1 << 15) | (rs2 << 20) | (immHigh << 25) | (immSign << 31);
}

uint32_t sdvm_compiler_riscv_32_U_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    int32_t immPart = imm >> 12;
    return opcode | (rd << 7) | (immPart << 12);
}

uint32_t sdvm_compiler_riscv_32_J_encode(uint8_t opcode, sdvm_riscv_registerIndex_t rd, int32_t imm)
{
    int32_t imm20 = (imm & (1<<20)) ? 1 : 0;
    int32_t imm10_1 = (imm >> 1) & 1023;
    int32_t imm11 = (imm & (1<<11)) ? 1 : 0;
    int32_t imm19_12 = (imm >> 12) & 255;
    return opcode | (rd << 7) | (imm19_12 << 12) | (imm11 << 20) | (imm10_1 << 21) | (imm20 << 31);
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

void sdvm_compiler_riscv_jalr(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs, int16_t imm)
{
    sdvm_compiler_riscv_addInstruction(compiler, sdvm_compiler_riscv_32_I_encode(0x67, rd, 0, rs, imm));
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

void sdvm_compiler_riscv_nop(sdvm_compiler_t *compiler)
{
    sdvm_compiler_riscv_addi_noOpt(compiler, SDVM_RISCV_ZERO, SDVM_RISCV_ZERO, 0);
}

void sdvm_compiler_riscv_mv(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t rd, sdvm_riscv_registerIndex_t rs)
{
    if(rd == rs)
        return 0;
    sdvm_compiler_riscv_addi(compiler, rd, rs, 0);
}

void sdvm_compiler_riscv_ret(sdvm_compiler_t *compiler)
{
    sdvm_compiler_riscv_jalr(compiler, SDVM_RISCV_ZERO, SDVM_RISCV_RA, 0);
}

#pragma endregion GeneralPurposeInstructions

static sdvm_compilerInstructionPatternTable_t sdvm_riscv64_instructionPatternTable = {
};

sdvm_compilerLocation_t sdvm_compilerLocation_riscv64_immediateS32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateS32(value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv64_immediateU32(sdvm_compiler_t *compiler, int32_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateU32(value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv64_immediateS64(sdvm_compiler_t *compiler, int64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateS64(value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_riscv64_immediateU64(sdvm_compiler_t *compiler, uint64_t value)
{
    if(value == 0)
        return sdvm_compilerLocation_null();
    else
        return sdvm_compilerLocation_immediateU64(value);
}

void sdvm_compiler_riscv64_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_riscv64_immediateS32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstUInt32:
            instruction->location = sdvm_compilerLocation_riscv64_immediateU32(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64SExt:
        case SdvmConstUInt64SExt:
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_riscv64_immediateS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
        case SdvmConstUInt64ZExt:
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_riscv64_immediateU64(state->compiler, instruction->decoding.constant.unsignedPayload);
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

void sdvm_compiler_riscv64_computeFunctionLocationConstraints(sdvm_functionCompilationState_t *state)
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
            sdvm_compiler_riscv64_computeInstructionLocationConstraints(state, instruction);
            ++i;
        }
    }
}

void sdvm_compiler_riscv64_allocateFunctionRegisters(sdvm_functionCompilationState_t *state)
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

void sdvm_compiler_riscv64_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_allocateFunctionSpillLocations(state);
}

void sdvm_compiler_riscv64_computeFunctionStackLayout(sdvm_functionCompilationState_t *state)
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

void sdvm_compiler_riscv64_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;

    sdvm_compiler_riscv_ensureCIE(state->moduleState);
    sdvm_dwarf_cfi_beginFDE(cfi, &compiler->textSection, sdvm_compiler_getCurrentPC(compiler));

    if(state->debugFunctionTableEntry)
        sdvm_moduleCompilationState_addDebugLineInfo(state->moduleState, SdvmDebugLineInfoKindBeginPrologue, state->debugFunctionTableEntry->declarationLineInfo);

    if(!state->requiresStackFrame)
    {
        sdvm_dwarf_cfi_endPrologue(cfi);
        return;
    }

    abort();
    sdvm_dwarf_cfi_endPrologue(cfi);
}

void sdvm_compiler_riscv64_emitMemoryToMemoryFixedSizedAlignedMove(sdvm_compiler_t *compiler, sdvm_riscv_registerIndex_t sourcePointer, int32_t sourcePointerOffset, sdvm_riscv_registerIndex_t destinationPointer, int32_t destinationPointerOffset, size_t copySize, const sdvm_compilerScratchMoveRegisters_t *scratchMoveRegister)
{
    abort();
}

void sdvm_compiler_riscv64_emitMoveFromLocationIntoIntegerRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        return sdvm_compiler_riscv_mv(compiler, reg->value, SDVM_RISCV_ZERO);
    case SdvmCompLocationRegister:
    case SdvmCompLocationRegisterPair:
        return sdvm_compiler_riscv_mv(compiler, reg->value, sourceLocation->firstRegister.value);
    default: return abort();
    }
}

void sdvm_compiler_riscv64_emitMoveFromLocationIntoFloatRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(sourceLocation->kind)
    {
    default: return abort();
    }
}

void sdvm_compiler_riscv64_emitMoveFromLocationIntoRegister(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *reg)
{
    switch(reg->kind)
    {
    case SdvmCompRegisterKindInteger:
        return sdvm_compiler_riscv64_emitMoveFromLocationIntoIntegerRegister(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindFloat:
        return sdvm_compiler_riscv64_emitMoveFromLocationIntoFloatRegister(compiler, sourceLocation, reg);
    default: abort();
    }
}

void sdvm_compiler_riscv64_emitMoveFromRegisterIntoStackLocation(sdvm_compiler_t *compiler, const sdvm_compilerRegister_t *sourceRegister, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceRegister->kind)
    {
    case SdvmCompRegisterKindInteger:
        switch(sourceRegister->size)
        {
        default:
            return abort();
        }
    default:
        return abort();
    }
}

void sdvm_compiler_riscv64_emitMoveFromLocationIntoStack(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation, const sdvm_compilerStackLocation_t *stackLocation)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationRegister:
        return sdvm_compiler_riscv64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);
    case SdvmCompLocationRegisterPair:
        {
            sdvm_compiler_riscv64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->firstRegister, stackLocation);

            sdvm_compilerStackLocation_t nextLocation = *stackLocation;
            nextLocation.segmentOffset += sourceLocation->firstRegister.size;
            nextLocation.framePointerOffset += sourceLocation->firstRegister.size;

            return sdvm_compiler_riscv64_emitMoveFromRegisterIntoStackLocation(compiler, &sourceLocation->secondRegister, &nextLocation);
        }
    case SdvmCompLocationStack:
        SDVM_ASSERT(destinationLocation->scratchMoveRegister.isValid);
        return sdvm_compiler_riscv64_emitMemoryToMemoryFixedSizedAlignedMove(compiler,
            sourceLocation->firstStackLocation.framePointerRegister, sourceLocation->firstStackLocation.framePointerOffset,
            destinationLocation->firstStackLocation.framePointerRegister, destinationLocation->firstStackLocation.framePointerOffset,
            sourceLocation->firstStackLocation.size <= destinationLocation->firstStackLocation.size ? sourceLocation->firstStackLocation.size : destinationLocation->firstStackLocation.size,
            &destinationLocation->scratchMoveRegister);
    default: return abort();
    }
}

void sdvm_compiler_riscv64_emitMoveFromLocationInto(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *sourceLocation, sdvm_compilerLocation_t *destinationLocation)
{
    switch(destinationLocation->kind)
    {
    case SdvmCompLocationNull:
        // Ignored.
        return;
    case SdvmCompLocationRegister:
        return sdvm_compiler_riscv64_emitMoveFromLocationIntoRegister(compiler, sourceLocation, &destinationLocation->firstRegister);
    case SdvmCompLocationRegisterPair:
        // TODO:
        return abort();
    case SdvmCompLocationStack:
        return sdvm_compiler_riscv64_emitMoveFromLocationIntoStack(compiler, sourceLocation, destinationLocation, &destinationLocation->firstStackLocation);
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

bool sdvm_compiler_riscv64_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
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
        sdvm_compiler_riscv64_emitFunctionEpilogue(state);
        sdvm_compiler_riscv_ret(compiler);
        return false;

    default:
        abort();
    }
}

void sdvm_compiler_riscv64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
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
        sdvm_compiler_riscv64_emitMoveFromLocationInto(state->compiler, &arg0->location, &instruction->arg0Location);
    }

    if(startInstruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + startInstruction->decoding.instruction.arg1;
        sdvm_compiler_riscv64_emitMoveFromLocationInto(state->compiler, &arg1->location, &instruction->arg1Location);
    }

    // Emit the actual instruction operation
    if(instruction->pattern)
    {
        if(!instruction->pattern->generator(state, instruction->pattern->size, instruction))
            return;
    }
    else
    {
        if(!sdvm_compiler_riscv64_emitFunctionInstructionOperation(state, instruction))
            return;
    }

    // Emit the result moves.
    sdvm_compiler_riscv64_emitMoveFromLocationInto(state->compiler, &endInstruction->destinationLocation, &endInstruction->location);
}


void sdvm_compiler_riscv64_emitFunctionInstructions(sdvm_functionCompilationState_t *state)
{
    uint32_t i = 0;
    while(i < state->instructionCount)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_riscv64_emitFunctionInstruction(state, instruction);
        if(instruction->pattern)
            i += instruction->pattern->size;
        else
            ++i;
    }
}

void sdvm_compiler_riscv64_emitFunctionEnding(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    sdvm_dwarf_cfi_endFDE(cfi, sdvm_compiler_getCurrentPC(compiler));
}

void sdvm_compiler_riscv64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    if(!state->requiresStackFrame)
        return;

    sdvm_compiler_t *compiler = state->compiler;
    sdvm_dwarf_cfi_builder_t *cfi = &state->moduleState->cfi;
    sdvm_dwarf_cfi_beginEpilogue(cfi);

    abort();

    sdvm_dwarf_cfi_endEpilogue(cfi);
}

bool sdvm_compiler_riscv64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_riscv64_computeFunctionLocationConstraints(state);
    sdvm_compiler_riscv64_allocateFunctionRegisters(state);
    sdvm_compiler_riscv64_allocateFunctionSpillLocations(state);
    sdvm_compiler_riscv64_computeFunctionStackLayout(state);

    if(state->compiler->verbose)
        sdvm_functionCompilationState_dump(state);

    // Align the function start symbol.
    sdvm_compiler_riscv_alignUnreacheableCode(state->compiler);

    // Set the function symbol
    size_t startOffset = state->compiler->textSection.contents.size;
    state->debugInfo->startPC = startOffset;
    sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&state->compiler->symbolTable, state->symbol, state->compiler->textSection.symbolIndex, startOffset);

    // Emit the prologue.
    sdvm_compiler_riscv64_emitFunctionPrologue(state);

    // Emit the instructions.
    sdvm_compiler_riscv64_emitFunctionInstructions(state);

    // End the function.
    sdvm_compiler_riscv64_emitFunctionEnding(state);

    // Set the symbol size.
    size_t endOffset = state->compiler->textSection.contents.size;
    state->debugInfo->endPC = endOffset;
    sdvm_compilerSymbolTable_setSymbolSize(&state->compiler->symbolTable, state->symbol, endOffset - startOffset);
    sdvm_compiler_riscv_alignUnreacheableCode(state->compiler);

    return true;
}

uint32_t sdvm_compiler_riscv64_mapElfRelocation(sdvm_compilerRelocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompRelocationAbsolute32: return SDVM_R_RISCV_32;
    case SdvmCompRelocationAbsolute64: return SDVM_R_RISCV_64;
    case SdvmCompRelocationRelative32: return SDVM_R_RISCV_32_PCREL;
    case SdvmCompRelocationSectionRelative32: return SDVM_R_RISCV_32;
    default: abort();
    }
}

static sdvm_compilerTarget_t sdvm_compilerTarget_riscv64_linux = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_RISCV,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_RISCV64,
    .usesUnderscorePrefix = false,
    .usesCET = false,
    .closureCallNeedsScratch = true,

    .defaultCC = &sdvm_riscv64_abi_callingConvention,
    .cdecl = &sdvm_riscv64_abi_callingConvention,
    .stdcall = &sdvm_riscv64_abi_callingConvention,
    .apicall = &sdvm_riscv64_abi_callingConvention,
    .thiscall = &sdvm_riscv64_abi_callingConvention,
    .vectorcall = &sdvm_riscv64_abi_callingConvention,

    .compileModuleFunction = sdvm_compiler_riscv64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_riscv64_mapElfRelocation,

    .instructionPatterns = &sdvm_riscv64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_riscv64_linux(void)
{
    return &sdvm_compilerTarget_riscv64_linux;
}
