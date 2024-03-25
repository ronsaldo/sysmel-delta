#ifndef SDVM_COMPILER_X86_H
#define SDVM_COMPILER_X86_H

#include "compiler.h"

typedef enum sdvm_x86_registerIndex_e
{
#define SDVM_X86_REG_DEF(kind, size, name, value) SDVM_X86_ ## name = value,
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

    SDVM_X86_REG_HALF_MASK = 7,
} sdvm_x86_registerIndex_t;

#define SDVM_X86_REG_DEF(kind, size, name, value) SDVM_API extern const sdvm_compilerRegister_t sdvm_x86_ ## name;
#include "x86Regs.inc"
#undef SDVM_X86_REG_DEF

SDVM_API uint8_t sdvm_compiler_x86_modRM(int8_t rm, uint8_t regOpcode, uint8_t mod);
SDVM_API uint8_t sdvm_compiler_x86_sibOnlyBase(uint8_t reg);
SDVM_API uint8_t sdvm_compiler_x86_modRMRegister(sdvm_x86_registerIndex_t rm, sdvm_x86_registerIndex_t reg);

SDVM_API void sdvm_compiler_x86_lock(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_repne(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_rep(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_fsPrefix(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_gsPrefix(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_operandPrefix(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_addressPrefix(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_rex(sdvm_compiler_t *compiler, bool W, bool R, bool X, bool B);

SDVM_API void sdvm_compiler_x86_int3(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_ud2(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_callGsv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend);
SDVM_API void sdvm_compiler_x86_callLsv(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t symbolHandle, int32_t addend);
SDVM_API void sdvm_compiler_x86_callReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_callRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_jmpReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_jmpRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset);

SDVM_API void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);

SDVM_API void sdvm_compiler_x86_endbr32(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_endbr64(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_xchg64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov64RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_mov64RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov64RegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int64_t offset);
SDVM_API void sdvm_compiler_x86_lea64RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_lea64RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_mov64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_mov64RegImmS64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int64_t value);
SDVM_API void sdvm_compiler_x86_mov64RegImmU64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value);
SDVM_API void sdvm_compiler_x86_movabs64(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, uint64_t value);
SDVM_API void sdvm_compiler_x86_add64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_add64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sub64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_and64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_or64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_xor64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);

SDVM_API void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_mov32RegReg_noOpt(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_mov32RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_lea32RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_add32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_add32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_and32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_or32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_xor32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);

SDVM_API void sdvm_compiler_x86_mov16RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg32Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg32Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movzxReg64Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg64Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsxReg32Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsxReg32Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsxReg64Reg16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsxReg64Rmo16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_add16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_add16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_sub16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_and16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_or16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_xor16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);

#endif //SDVM_COMPILER_X86_H

