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

static const sdvm_compilerRegisterValue_t sdvm_x64_allocatableVectorRegisters[] = {
    SDVM_X86_XMM0,  SDVM_X86_XMM1,  SDVM_X86_XMM2,  SDVM_X86_XMM3,
    SDVM_X86_XMM4,  SDVM_X86_XMM5,  SDVM_X86_XMM6,  SDVM_X86_XMM7,
    SDVM_X86_XMM8,  SDVM_X86_XMM9,  SDVM_X86_XMM10, SDVM_X86_XMM11,
    SDVM_X86_XMM12, SDVM_X86_XMM13, SDVM_X86_XMM14, SDVM_X86_XMM15,
};
static const uint32_t sdvm_x64_allocatableVectorRegisterCount = sizeof(sdvm_x64_allocatableVectorRegisters) / sizeof(sdvm_x64_allocatableVectorRegisters[0]);

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
    if(destination == source)
        return;

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

void sdvm_compiler_x86_mov32RegReg_noOpt(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rex(compiler, false, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x8B,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    if(destination != source)
        sdvm_compiler_x86_mov32RegReg_noOpt(compiler, destination, source);
}

void sdvm_compiler_x86_alu32RmReg(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source)
{
    sdvm_compiler_x86_rex(compiler, false, source > SDVM_X86_REG_HALF_MASK, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        opcode,
        sdvm_compiler_x86_modRMRegister(destination, source)
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}


void sdvm_compiler_x86_alu32RmImm32(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint32_t value)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        opcode,
        sdvm_compiler_x86_modRMRegister(destination, regOpcode),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_alu32RmImm8(sdvm_compiler_t *compiler, uint8_t opcode, sdvm_x86_registerIndex_t destination, uint8_t regOpcode, uint8_t value)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        opcode,
        sdvm_compiler_x86_modRMRegister(destination, regOpcode),
        value & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
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
    case SdvmInstArgInt8:
    case SdvmInstArgInt16:
    case SdvmInstArgInt32:
    case SdvmInstArgUInt8:
    case SdvmInstArgUInt16:
    case SdvmInstArgUInt32:
        if(state->usedArgumentIntegerRegisterCount < sdvm_x64_sysv_integerPassingDwordRegisterCount)
        {
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*sdvm_x64_sysv_integerPassingDwordRegisters[state->usedArgumentIntegerRegisterCount++]);
        }
        else
        {
            // TODO: Support passing parameters through the stack
            abort();
        }
        return;
    case SdvmInstArgInt64:
    case SdvmInstArgUInt64:
    case SdvmInstArgPointer:
    case SdvmInstArgProcedureHandle:
        if(state->usedArgumentIntegerRegisterCount < sdvm_x64_sysv_integerPassingRegisterCount)
        {
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*sdvm_x64_sysv_integerPassingRegisters[state->usedArgumentIntegerRegisterCount++]);
        }
        else
        {
            // TODO: Support passing parameters through the stack
            abort();
        }
        return;
    
    case SdvmInstArgGCPointer:
        if(state->usedArgumentIntegerRegisterCount + 1 < sdvm_x64_sysv_integerPassingRegisterCount)
        {
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*sdvm_x64_sysv_integerPassingRegisters[state->usedArgumentIntegerRegisterCount], *sdvm_x64_sysv_integerPassingRegisters[state->usedArgumentIntegerRegisterCount + 1]);
            state->usedArgumentIntegerRegisterCount += 2;
        }
        else
        {
            // TODO: Support passing parameters through the stack
            abort();
        }
        return;

    case SdvmInstReturnInt8:
    case SdvmInstReturnInt16:
    case SdvmInstReturnInt32:
    case SdvmInstReturnUInt8:
    case SdvmInstReturnUInt16:
    case SdvmInstReturnUInt32:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_EAX);
        return;
    case SdvmInstReturnInt64:
    case SdvmInstReturnUInt64:
    case SdvmInstReturnPointer:
    case SdvmInstReturnProcedureHandle:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(sdvm_x86_RAX);
        return;
    case SdvmInstReturnGCPointer:
        instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(sdvm_x86_RAX, sdvm_x86_RDX);
        return;
    case SdvmInstReturnFloat32:
    case SdvmInstReturnFloat64:
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
        if(sourceLocation->firstRegister.size <= 4)
            return sdvm_compiler_x86_mov32RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
        return sdvm_compiler_x86_mov64RegReg(compiler, reg->value, sourceLocation->firstRegister.value);
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
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateLabel:
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
    case SdvmInstBeginArguments:
    case SdvmInstArgInt8:
    case SdvmInstArgInt16:
    case SdvmInstArgInt32:
    case SdvmInstArgInt64:
    case SdvmInstArgUInt8:
    case SdvmInstArgUInt16:
    case SdvmInstArgUInt32:
    case SdvmInstArgUInt64:
        return true;

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

void sdvm_compiler_x64_allocateFunctionRegisters(sdvm_functionCompilationState_t *state)
{
    sdvm_linearScanRegisterAllocatorFile_t integerRegisterFile = {
        .allocatableRegisterCount = sdvm_x64_sysv_allocatableIntegerRegisterCount,
        .allocatableRegisters = sdvm_x64_sysv_allocatableIntegerRegisters
    };

    sdvm_linearScanRegisterAllocatorFile_t vectorRegisterFile = {
        .allocatableRegisterCount = sdvm_x64_allocatableVectorRegisterCount,
        .allocatableRegisters = sdvm_x64_allocatableVectorRegisters
    };

    sdvm_linearScanRegisterAllocator_t registerAllocator = {
        .integerRegisterFile = &integerRegisterFile,
        .floatRegisterFile = &vectorRegisterFile,
        .vectorFloatRegisterFile = &vectorRegisterFile,
        .vectorIntegerRegisterFile = &vectorRegisterFile,
    };

    sdvm_compiler_allocateFunctionRegisters(state, &registerAllocator);

    // Store a copy of the used register sets. We need it for preserving called saved registers.
    state->usedIntegerRegisterSet = registerAllocator.integerRegisterFile->usedRegisterSet;
    state->usedFloatRegisterSet = registerAllocator.floatRegisterFile->usedRegisterSet;
    state->usedVectorFloatRegisterSet = registerAllocator.vectorFloatRegisterFile->usedRegisterSet;
    state->usedVectorIntegerRegisterSet = registerAllocator.vectorIntegerRegisterFile->usedRegisterSet;
}

bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_x64_computeFunctionLocationConstraints(state);
    sdvm_compiler_x64_allocateFunctionRegisters(state);

    sdvm_functionCompilationState_dump(state);
    sdvm_compiler_x64_emitFunctionPrologue(state);
    sdvm_compiler_x64_emitFunctionInstructions(state);
    return true;
}
