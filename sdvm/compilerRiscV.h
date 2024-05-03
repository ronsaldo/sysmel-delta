#ifndef SDVM_COMPILER_RISCV_H
#define SDVM_COMPILER_RISCV_H

#include "compiler.h"

typedef enum sdvm_riscv_registerIndex_e
{
#define SDVM_RISCV_INTEGER_REG_DEF(name, value) \
    SDVM_RISCV_ ## name = value,
#include "riscvRegs.inc"
#undef SDVM_RISCV_INTEGER_REG_DEF
} sdvm_riscv_registerIndex_t;

typedef enum sdvm_riscv_attribute_e
{
    SDVM_Tag_RISCV_file = 1,
    SDVM_Tag_RISCV_stack_align = 4,
    SDVM_Tag_RISCV_arch = 5,
    SDVM_Tag_RISCV_unaligned_access = 6,
    SDVM_Tag_RISCV_atomic_abi = 14,
    SDVM_Tag_RISCV_x3_reg_usage = 16,
} sdvm_riscv_attribute_t;

#define SDVM_RISCV_INTEGER_REG_DEF(name, value) \
    SDVM_API extern const sdvm_compilerRegister_t sdvm_riscv32_ ## name; \
    SDVM_API extern const sdvm_compilerRegister_t sdvm_riscv64_ ## name; \
    SDVM_API extern const sdvm_compilerRegister_t sdvm_riscv64_ ## name ## W;
#include "riscvRegs.inc"
#undef SDVM_RISCV_INTEGER_REG_DEF

#endif //SDVM_COMPILER_RISCV_H
