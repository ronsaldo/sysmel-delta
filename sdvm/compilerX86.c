#include "compilerX86.h"

uint8_t sdvm_compiler_x86_modRM(int8_t rm, uint8_t regOpcode, uint8_t mod)
{
    return (rm & SDVM_X86_REG_HALF_MASK) | ((regOpcode & SDVM_X86_REG_HALF_MASK) << 3) | (mod << 6);
}

uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg)
{
    return (reg & SDVM_X86_REG_HALF_MASK) | (4 << 3) ;
}

uint8_t sdvm_compiler_x86_modRMRegister(sdvm_x86_register_t rm, sdvm_x86_register_t reg)
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

void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_register_t reg)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, reg > SDVM_X86_REG_HALF_MASK);
    sdvm_compiler_addInstructionByte(compiler, 0x50 + (reg & SDVM_X86_REG_HALF_MASK));
}

void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_register_t reg)
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

void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, sdvm_x86_register_t source)
{
    sdvm_compiler_x86_rex(compiler, true, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x8B,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value)
{
    sdvm_compiler_x86_rex(compiler, true, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xC7,
        sdvm_compiler_x86_modRMRegister(destination, 0),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_movabs64(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, uint64_t value)
{
    sdvm_compiler_x86_rex(compiler, true, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xB8 + (destination & SDVM_X86_REG_HALF_MASK),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
        (value >> 32) & 0xFF, (value >> 40) & 0xFF, (value >> 48) & 0xFF, (value >> 56) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_sub64RegImm32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value)
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

void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value)
{
    sdvm_compiler_x86_rex(compiler, false, false, false, destination > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0xC7,
        sdvm_compiler_x86_modRMRegister(destination, 0),
        value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF,
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, sdvm_x86_register_t source)
{
    sdvm_compiler_x86_rex(compiler, false, destination > SDVM_X86_REG_HALF_MASK, false, source > SDVM_X86_REG_HALF_MASK);

    uint8_t instruction[] = {
        0x8B,
        sdvm_compiler_x86_modRMRegister(source, destination),
    };

    sdvm_compiler_addInstructionBytes(compiler, sizeof(instruction), instruction);
}

void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value)
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


bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;

    sdvm_functionCompilationState_dump(state);

    sdvm_compiler_x86_endbr64(compiler);
    sdvm_compiler_x86_push(compiler, SDVM_X86_RBP);
    sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RBP, SDVM_X86_RSP);

    sdvm_compiler_x86_mov64RegReg(compiler, SDVM_X86_RSP, SDVM_X86_RBP);
    sdvm_compiler_x86_pop(compiler, SDVM_X86_RBP);
    sdvm_compiler_x86_ret(compiler);
    return true;
}
