#ifndef SDVM_COMPILER_X86_H
#define SDVM_COMPILER_X86_H

#include "compiler.h"

typedef struct sdvm_x86_win64_runtime_info_s
{
    uint32_t functionStartAddress;
    uint32_t functionEndAddress;
    uint32_t unwindInfoAddress;
} sdvm_x86_win64_runtime_info_t;

typedef struct sdvm_x86_win64_unwind_info_s
{
    uint8_t versionAndFlags;
    uint8_t prologueSize;
    uint8_t unwindCodeCount;
    uint8_t frameRegisterAndOffset;
} sdvm_x86_win64_unwind_info_t;

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
SDVM_API void sdvm_compiler_x86_jmpLabel(sdvm_compiler_t *compiler, uint32_t label);

SDVM_API void sdvm_compiler_x86_jnzLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jneLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jzLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jeLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jaLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jaeLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jbLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jbeLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jgLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jgeLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jlLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jleLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jleLabel(sdvm_compiler_t *compiler, uint32_t label);
SDVM_API void sdvm_compiler_x86_jumpOnCondition(sdvm_compiler_t *compiler, uint32_t label, bool isSigned, sdvm_baseOpcode_t condition);
SDVM_API void sdvm_compiler_x86_jumpOnInverseCondition(sdvm_compiler_t *compiler, uint32_t label, bool isSigned, sdvm_baseOpcode_t condition);

SDVM_API void sdvm_compiler_x86_push(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_pop(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);

SDVM_API void sdvm_compiler_x86_cwd(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_cdq(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_cqo(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_endbr32(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_x86_endbr64(sdvm_compiler_t *compiler);

SDVM_API void sdvm_compiler_x86_sete(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setne(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setb(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setbe(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_seta(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setae(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setl(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setle(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setge(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t reg);
SDVM_API void sdvm_compiler_x86_setByteOnCondition(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, bool isSigned, sdvm_baseOpcode_t condition);
SDVM_API void sdvm_compiler_x86_setByteOnInverseCondition(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, bool isSigned, sdvm_baseOpcode_t condition);

SDVM_API void sdvm_compiler_x86_xchg64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmove64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovne64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmova64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovae64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovb64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovbe64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovg64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovge64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovl64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovle64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
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
SDVM_API void sdvm_compiler_x86_cmp64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_test64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_imul64RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_div64Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_idiv64Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_add64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sub64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_cmp64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_test64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_and64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_or64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_xor64RegImmS32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sar64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_sar64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shl64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shl64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shr64RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shr64RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);

SDVM_API void sdvm_compiler_x86_cmove32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovne32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmova32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovae32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovb32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovbe32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovg32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovge32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovl32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmovle32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_mov32RegReg_noOpt(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_mov32RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mov32RegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_lea32RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_lea32RegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsxdReg64Reg32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsxdReg64Rmo32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_lea32RegLsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol, int32_t offset);
SDVM_API void sdvm_compiler_x86_add32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmp32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_test32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_imul32RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_div32Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_idiv32Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_add32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sub32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_cmp32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_test32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_and32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_or32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_xor32RegImm32(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int32_t value);
SDVM_API void sdvm_compiler_x86_sar32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_sar32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shl32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shl32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shr32RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shr32RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);

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
SDVM_API void sdvm_compiler_x86_cmp16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_test16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_imul16RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_div16Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_idiv16Reg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t operand);
SDVM_API void sdvm_compiler_x86_add16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_sub16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_cmp16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_test16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_and16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_or16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_xor16RegImm16(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int16_t value);
SDVM_API void sdvm_compiler_x86_sar16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_sar16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shl16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shl16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shr16RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shr16RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);

SDVM_API void sdvm_compiler_x86_mov8RmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg32Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg32Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movzxReg64Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movzxReg64Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsxReg32Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsxReg32Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsxReg64Reg8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsxReg64Rmo8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_add8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sub8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_cmp8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_test8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_and8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_or8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xor8RegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_add8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_sub8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_cmp8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_test8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_and8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_or8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_xor8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_sar8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_sar8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shl8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shl8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);
SDVM_API void sdvm_compiler_x86_shr8RegCL(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination);
SDVM_API void sdvm_compiler_x86_shr8RegImm8(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, int8_t value);

SDVM_API void sdvm_compiler_x86_addpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_subpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mulpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_divpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sqrtpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_maxpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_minpdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);

SDVM_API void sdvm_compiler_x86_movapsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movapsRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movapsRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movapsRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol);
SDVM_API void sdvm_compiler_x86_addpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_subpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mulpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_divpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sqrtpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_maxpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_minpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_xorpsRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);

SDVM_API void sdvm_compiler_x86_movsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsdRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movsdRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movsdRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol);
SDVM_API void sdvm_compiler_x86_addsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_subsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mulsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_divsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sqrtsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_maxsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_minsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);

SDVM_API void sdvm_compiler_x86_movssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movssRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movssRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movssRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol);
SDVM_API void sdvm_compiler_x86_addssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_subssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_mulssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_divssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_sqrtssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_maxssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_minssRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);

SDVM_API void sdvm_compiler_x86_movdqaRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movdqaRegRmo(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t base, int32_t offset);
SDVM_API void sdvm_compiler_x86_movdqaRmoReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t base, int32_t offset, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_movdqaRegGsv(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_compilerSymbolHandle_t sourceSymbol);
SDVM_API void sdvm_compiler_x86_padddRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_psubdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pmulldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pmaxsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pmaxudRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pminsdRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pminudRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pandRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_porRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pxorRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_pslldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_psradRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);
SDVM_API void sdvm_compiler_x86_psrldRegReg(sdvm_compiler_t *compiler, sdvm_x86_registerIndex_t destination, sdvm_x86_registerIndex_t source);

#endif //SDVM_COMPILER_X86_H

