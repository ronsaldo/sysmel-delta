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

#endif //SDVM_COMPILER_AARCH64_H
