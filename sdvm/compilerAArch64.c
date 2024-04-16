#include "compilerAArch64.h"
#include "module.h"
#include "elf.h"
#include "coff.h"
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
static const uint32_t sdvm_aarch64_eabi_callPreservedVectorRegisterCount = SDVM_C_ARRAY_SIZE(sdvm_aarch64_eabi_callTouchedVectorRegisters);

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

void sdvm_compiler_aarch64_alignUnreacheableCode(sdvm_compiler_t *compiler)
{
    if(compiler->textSection.alignment < 4)
        compiler->textSection.alignment = 4;
}

size_t sdvm_compiler_aarch64_addInstruction(sdvm_compiler_t *compiler, uint32_t instruction)
{
    size_t offset = compiler->textSection.contents.size;
    sdvm_compiler_addInstructionBytes(compiler, 4, &instruction);
    return offset;
}

void sdvm_compiler_aarch64_ret(sdvm_compiler_t *compiler)
{
    sdvm_compiler_aarch64_addInstruction(compiler, 0xD65F0000 | (SDVM_AARCH64_X30 << 5));
}

static sdvm_compilerInstructionPatternTable_t sdvm_aarch64_instructionPatternTable = {
};

void sdvm_compiler_aarch64_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
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

    sdvm_compiler_computeStackSegmentLayouts(state);

    if(state->requiresStackFrame)
    {
        state->stackFrameRegister = SDVM_AARCH64_FP;
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
        state->stackFrameRegister = SDVM_AARCH64_SP;
        state->stackFramePointerAnchorOffset = state->calloutStackSegment.endOffset;
    }

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

    // TODO: Construct the stack frame.
    abort();
}

void sdvm_compiler_aarch64_emitMoveFromLocationInto(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *destination, sdvm_compilerLocation_t *source)
{
}

bool sdvm_compiler_aarch64_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
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
        sdvm_compiler_aarch64_emitFunctionEpilogue(state);
        sdvm_compiler_aarch64_ret(compiler);
        return false;
    default:
        abort();
    }
}

void sdvm_compiler_aarch64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
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

    abort();
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
    default: abort();
    }
}

uint16_t sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend(sdvm_compilerRelocation_t *relocation, uint8_t *target)
{
    abort();
}

static sdvm_compilerTarget_t sdvm_compilerTarget_aarch64_linux = {
    .pointerSize = 8,
    .objectFileType = SdvmObjectFileTypeElf,
    .elfMachine = SDVM_EM_AARCH64,
    .coffMachine = SDVM_IMAGE_FILE_MACHINE_ARM64,
    .usesUnderscorePrefix = false,
    .usesCET = false,

    .defaultCC = &sdvm_aarch64_eabi_callingConvention,
    .cdecl = &sdvm_aarch64_eabi_callingConvention,
    .stdcall = &sdvm_aarch64_eabi_callingConvention,
    .apicall = &sdvm_aarch64_eabi_callingConvention,
    .thiscall = &sdvm_aarch64_eabi_callingConvention,
    .vectorcall = &sdvm_aarch64_eabi_callingConvention,

    .compileModuleFunction = sdvm_compiler_aarch64_compileModuleFunction,
    .mapElfRelocation = sdvm_compiler_aarch64_mapElfRelocation,
    .mapCoffRelocationApplyingAddend = sdvm_compiler_aarch64_mapCoffRelocationApplyingAddend,

    .instructionPatterns = &sdvm_aarch64_instructionPatternTable,
};

const sdvm_compilerTarget_t *sdvm_compilerTarget_get_aarch64_linux(void)
{
    return &sdvm_compilerTarget_aarch64_linux;
}