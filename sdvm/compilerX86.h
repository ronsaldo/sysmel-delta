#ifndef SDVM_COMPILER_X86_H
#define SDVM_COMPILER_X86_H

#include "compiler.h"

typedef enum sdvm_x86_registerIndex_e
{
#define SDVM_X86_REG_DEF(kind, size, name, value) SDVM_X86_ ## name = value,
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

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
} sdvm_x86_registerIndex_t;

#define SDVM_X86_REG_DEF(kind, size, name, value) SDVM_API extern const sdvm_compilerRegister_t sdvm_x86_ ## name;
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

SDVM_API uint8_t sdvm_compiler_x86_modRM(int8_t rm, uint8_t regOpcode, uint8_t mod);
SDVM_API uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg);
SDVM_API uint8_t sdvm_compiler_x86_modRMRegister(sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg);

void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B);

SDVM_API void sdvm_compiler_x86_int3(sdvm_compiler_t *jit);
SDVM_API void sdvm_compiler_x86_ud2(sdvm_compiler_t *jit);
SDVM_API void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);

SDVM_API void sdvm_compiler_x86_endbr32(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_endbr64(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_mov64RegImmS64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int64_t value);
SDVM_API void sdvm_compiler_x86_mov64RegImmU64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value);
SDVM_API void sdvm_compiler_x86_movabs64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value);
SDVM_API void sdvm_compiler_x86_sub64RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);

SDVM_API void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_xor32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);


#endif //SDVM_COMPILER_X86_H

