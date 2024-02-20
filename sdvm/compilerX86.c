#include "compilerX86.h"
#include "module.h"
#include <string.h>

#define SDVM_X86_REG_DEF(regKind, regSize, name, regValue) const sdvm_compilerRegister_t sdvm_x86_ ## name = {\
    .kind = SdvmCompRegisterKind ## regKind, \
    .size = regSize, \
    .value = regValue, \
};
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

uint8_t sdvm_compiler_x86_modRM(int8_t rm, uint8_t regOpcode, uint8_t mod)
{
    return (rm & SDVM_X86_REG_HALF_MASK) | ((regOpcode & SDVM_X86_REG_HALF_MASK) << 3) | (mod << 6);
}

uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg)
{
    return (reg & SDVM_X86_REG_HALF_MASK) | (4 << 3) ;
}

uint8_t sdvm_compiler_x86_modRMRegister(sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg)
{
    return sdvm_compiler_x86_modRM(rm, reg, 3);
}

void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B)
{
    if(W || R || X || B)
    {
        sdvm_compiler_addInstructionByte(compiler, 0x40 | ((W ? 1 : 0) << 3) | ((R ? 1 : 0) << 2) | ((X ? 1 : 0) << 1) | (B ? 1 : 0));
    }
}

void sdvm_compiler_x86_int3(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0xCC,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_ud2(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0x0F, 0x0B,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0xc3
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, reg > SDVM_X86_REG_HALF_MASK);
    sdvm_compiler_addInstructionByte(compiler, 0x50 + (reg & SDVM_X86_REG_HALF_MASK));
}

void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, reg > SDVM_X86_REG_HALF_MASK);
    sdvm_compiler_addInstructionByte(compiler, 0x58 + (reg & SDVM_X86_REG_HALF_MASK));
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

void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rex(compiler, true, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x8B,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);
    
    sdvm_compiler_x86_rex(compiler, true, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xC7,
        sdvm_compiler_x86_modRMRegister(destination, 0),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
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
    sdvm_compiler_x86_rex(compiler, true, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xB8 + (destination & SDVM_X86_REG_HALF_MASK),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
        (value >> 32) & 0xFF, (value >> 40) & 0xFF, (value >> 48) & 0xFF, (value >> 56) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_sub64RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rex(compiler, true, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x81,
        sdvm_compiler_x86_modRMRegister(destination, 5),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return sdvm_compiler_x86_xor32RegReg(compiler, destination, destination);

    sdvm_compiler_x86_rex(compiler, false, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xC7,
        sdvm_compiler_x86_modRMRegister(destination, 0),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rex(compiler, false, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x8B,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value)
{
    if(value == 0)
        return;

    sdvm_compiler_x86_rex(compiler, false, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x81,
        sdvm_compiler_x86_modRMRegister(destination, 5),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_xor32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rex(compiler, false, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x31,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

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

    switch (instruction->decoding.opcode)
    {
    case SdvmInstReturnInteger:
    case SdvmInstReturnPointer:
    case SdvmInstReturnProcedureHandle:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        return;
    case SdvmInstReturnGCPointer:
        instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(sdvm_x86_RAX, sdvm_x86_RDX);
        return;
    case SdvmInstReturnFloat:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_XMM0);
        return;
    case SdvmInstReturnFloatVector128:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_XMM0);
        return;
    case SdvmInstReturnIntegerVector128:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_XMM0I);
        return;
    case SdvmInstReturnFloatVector256:
        instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(sdvm_x86_XMM0, sdvm_x86_XMM1);
        return;
    case SdvmInstReturnIntegerVector256:
        instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(sdvm_x86_XMM0I, sdvm_x86_XMM1I);
        return;
    default:
        sdvm_functionCompilationState_computeInstructionLocationConstraints(state, instruction);
    }
}

void sdvm_compiler_x64_computeFunctionLocationConstraints(sdvm_functionCompilationState_t *state)
{
    for(uint32_t i = 0; i < state->instructionCount; ++i)
        sdvm_compiler_x64_computeInstructionLocationConstraints(state, state->instructions + i);
}

void sdvm_compiler_x64_emitFunctionPrologue(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;
    sdvm_compiler_x86_endbr64(compiler);
    //sdvm_compiler_x86_push(compiler, SDVM_X86_RBP);
    //sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RBP, SDVM_X86_RSP);
}

void sdvm_compiler_x64_emitFunctionEpilogue(sdvm_functionCompilationState_t *state)
{
    //sdvm_compiler_t *compiler = state->compiler;
    //sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RSP, SDVM_X86_RBP);
    //sdvm_compiler_x86_pop(compiler, SDVM_X86_RBP);
}

bool sdvm_compiler_x64_emitFunctionInstructionOperation(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_compiler_t *compiler = state->compiler;

    switch(instruction->decoding.opcode)
    {
    case SdvmInstReturnInteger:
    case SdvmInstReturnPointer:
    case SdvmInstReturnProcedureHandle:
    case SdvmInstReturnGCPointer:
    case SdvmInstReturnFloat:
    case SdvmInstReturnFloatVector128:
    case SdvmInstReturnIntegerVector128:
    case SdvmInstReturnFloatVector256:
    case SdvmInstReturnIntegerVector256:
        sdvm_compiler_x64_emitFunctionEpilogue(state);
        sdvm_compiler_x86_ret(compiler);
        return false;
    default:
        abort();
    }
    return true;
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
        return sdvm_compiler_x86_mov64RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
    /*SdvmCompLocationNull = 0,
    SdvmCompLocationImmediateLabel,
    SdvmCompLocationConstantSection,
    SdvmCompLocationRegisterPair,
    SdvmCompLocationSpecificRegister,
    SdvmCompLocationSpecificRegisterPair,
    SdvmCompLocationStack,
    SdvmCompLocationStackPair,
    */
    default: abort();
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
    case SdvmCompRegisterKindVectorFloat:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorFloat(compiler, sourceLocation, reg);
    case SdvmCompRegisterKindVectorInteger:
        return sdvm_compiler_x64_emitMoveFromLocationIntoVectorInteger(compiler, sourceLocation, reg);
    }
}

void sdvm_compiler_x64_emitMoveFromLocationIntoIntegerRegisterPair(sdvm_compiler_t *compiler, const sdvm_compilerLocation_t *sourceLocation, const sdvm_compilerRegister_t *firstRegister, const sdvm_compilerRegister_t *secondRegister)
{
    switch(sourceLocation->kind)
    {
    case SdvmCompLocationNull:
        sdvm_compiler_x86_xor32RegReg(compiler, firstRegister->value, firstRegister->value);
        return sdvm_compiler_x86_xor32RegReg(compiler, secondRegister->value, secondRegister->value);
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
    switch(sourceLocation->kind)
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
        return abort();
    case SdvmCompLocationStackPair:
        return abort();
    default:
        return abort();
    }
}

void sdvm_compiler_x64_emitFunctionInstruction(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        // TODO: emit the label, if this is a label.
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

bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_x64_computeFunctionLocationConstraints(state);

    sdvm_functionCompilationState_dump(state);
    sdvm_compiler_x64_emitFunctionPrologue(state);
    sdvm_compiler_x64_emitFunctionInstructions(state);

    //sdvm_compiler_x86_ret(compiler);
    return true;
}
