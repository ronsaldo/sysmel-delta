#ifndef SDVM_COMPILER_X86_H
#define SDVM_COMPILER_X86_H

#include "compiler.h"

typedef enum sdvm_x86_register_e
{
    SDVM_X86_RAX = 0,
    SDVM_X86_RCX = 1,
    SDVM_X86_RDX = 2,
    SDVM_X86_RBX = 3,
    SDVM_X86_RSP = 4,
    SDVM_X86_RBP = 5,
    SDVM_X86_RSI = 6,
    SDVM_X86_RDI = 7,

    SDVM_X86_R8 = 8,
    SDVM_X86_R9 = 9,
    SDVM_X86_R10 = 10,
    SDVM_X86_R11 = 11,
    SDVM_X86_R12 = 12,
    SDVM_X86_R13 = 13,
    SDVM_X86_R14 = 14,
    SDVM_X86_R15 = 15,

    SDVM_X86_EAX = 0,
    SDVM_X86_ECX = 1,
    SDVM_X86_EDX = 2,
    SDVM_X86_EBX = 3,
    SDVM_X86_ESP = 4,
    SDVM_X86_EBP = 5,
    SDVM_X86_ESI = 6,
    SDVM_X86_EDI = 7,

    SDVM_X86_REG_HALF_MASK = 7,

    SDVM_X86_WIN64_ARG0 = SDVM_X86_RCX,
    SDVM_X86_WIN64_ARG1 = SDVM_X86_RDX,
    SDVM_X86_WIN64_ARG2 = SDVM_X86_R8,
    SDVM_X86_WIN64_ARG3 = SDVM_X86_R9,
    SDVM_X86_WIN64_SHADOW_SPACE = 32,

    SDVM_X86_SYSV_ARG0 = SDVM_X86_RDI,
    SDVM_X86_SYSV_ARG1 = SDVM_X86_RSI,
    SDVM_X86_SYSV_ARG2 = SDVM_X86_RDX,
    SDVM_X86_SYSV_ARG3 = SDVM_X86_RCX,
    SDVM_X86_SYSV_ARG4 = SDVM_X86_R8,
    SDVM_X86_SYSV_ARG5 = SDVM_X86_R9,
    SDVM_X86_SYSV_SHADOW_SPACE = 0,

    SDVM_X86_64_ARG0 = SDVM_X86_SYSV_ARG0,
    SDVM_X86_64_ARG1 = SDVM_X86_SYSV_ARG1,
    SDVM_X86_64_ARG2 = SDVM_X86_SYSV_ARG2,
    SDVM_X86_64_ARG3 = SDVM_X86_SYSV_ARG3,
} sdvm_x86_register_t;

SDVM_API uint8_t sdvm_compiler_x86_modRM(int8_t rm, uint8_t regOpcode, uint8_t mod);
SDVM_API uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg);
SDVM_API uint8_t sdvm_compiler_x86_modRMRegister(sdvm_x86_register_t rm, sdvm_x86_register_t reg);

void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B);

SDVM_API void sdvm_compiler_x86_int3(sdvm_compiler_t *jit);
SDVM_API void sdvm_compiler_x86_ud2(sdvm_compiler_t *jit);
SDVM_API void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_register_t reg);
SDVM_API void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_register_t reg);

SDVM_API void sdvm_compiler_x86_endbr32(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_endbr64(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, sdvm_x86_register_t source);
SDVM_API void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_movabs64(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, uint64_t value);
SDVM_API void sdvm_compiler_x86_sub64RegImm32(sdvm_compiler_t *compiler, sdvm_x86_register_t destination, int32_t value);


#endif //SDVM_COMPILER_X86_H

