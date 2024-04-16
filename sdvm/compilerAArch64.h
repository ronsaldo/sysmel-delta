#ifndef SDVM_COMPILER_AARCH64_H
#define SDVM_COMPILER_AARCH64_H

#include "compiler.h"

typedef enum sdvm_aarch64_registerIndex_e
{
#define SDVM_AARCH64_REG_DEF(kind, size, name, value) SDVM_AARCH64_ ## name = value,
#include "aarch64Regs.inc"
#undef SDVM_AARCH64_REG_DEF
} sdvm_aarch64_registerIndex_t;

#define SDVM_AARCH64_REG_DEF(kind, size, name, value) SDVM_API extern const sdvm_compilerRegister_t sdvm_aarch64_ ## name;
#include "aarch64Regs.inc"
#undef SDVM_AARCH64_REG_DEF

typedef enum sdvm_aarch64_condition_e
{
    SDVM_AARCH64_EQ = 0,
    SDVM_AARCH64_NE = 1,
    SDVM_AARCH64_CS = 2,
    SDVM_AARCH64_CC = 3,
    SDVM_AARCH64_MI = 4,
    SDVM_AARCH64_PL = 5,
    SDVM_AARCH64_VS = 6,
    SDVM_AARCH64_VC = 7,
    SDVM_AARCH64_HI = 8,
    SDVM_AARCH64_LS = 9,
    SDVM_AARCH64_GE = 10,
    SDVM_AARCH64_LT = 11,
    SDVM_AARCH64_GT = 12,
    SDVM_AARCH64_LE = 13,
    SDVM_AARCH64_AL = 14,
    SDVM_AARCH64_NV = 15,
} sdvm_aarch64_condition_t;

typedef enum sdvm_aarch64_extendOption_e
{
    SDVM_AARCH64_UXTB = 0,
    SDVM_AARCH64_UXTH = 1,
    SDVM_AARCH64_UXTW = 2,
    SDVM_AARCH64_UXTX = 3,
    SDVM_AARCH64_SXTB = 4,
    SDVM_AARCH64_SXTH = 5,
    SDVM_AARCH64_SXTW = 6,
    SDVM_AARCH64_SXTX = 7,
} sdvm_aarch64_extendOption_t;

typedef enum sdvm_aarch64_shiftType_e
{
    SDVM_AARCH64_LSL = 0,
    SDVM_AARCH64_LSR = 1,
    SDVM_AARCH64_ASR = 2,
} sdvm_aarch64_shiftType_t;

#endif //SDVM_COMPILER_AARCH64_H
