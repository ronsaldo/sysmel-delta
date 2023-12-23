#ifndef SDVM_INSTRUCTION_H
#define SDVM_INSTRUCTION_H

#include <stdint.h>

typedef enum sdvm_type_e
{
    SdvmTypeVoid = 0,
    SdvmTypeInteger = 1,
    SdvmTypePointer = 2,
    SdvmTypeProcedureHandle = 3,
    SdvmTypeFatPointer = 5,
    SdvmTypeFloat = 6,
    SdvmTypeFloatVector = 7,
    SdvmTypeIntegerVector = 8,
    SdvmTypeInfo = 9,
} sdvm_type_t;

#define SDVM_ENCODE_OPCODE(isConstant, opcode, destinationType, arg0Type, arg1Type) \
    (isConstant \
        ? (1 | (opcode << 1)) \
        : (opcode << 1) | (destinationType << 12) | (arg0Type << 16) | (arg1Type << 20))

typedef enum sdvm_opcode_e
{
#define SDVM_CONSTANT_DEF(name, opcode, type, description) \
    SdvmConst ## name = SDVM_ENCODE_OPCODE(1, opcode, SdvmType ## type, SdvmTypeVoid, SdvmTypeVoid),
#define SDVM_OPCODE_DEF(name, opcode, description) \
    SdvmOp ## name = opcode,
#define SDVM_INSTRUCTION_DEF(name, opcode, type, arg0Type, arg1Type, description) \
    SdvmInst ## name = SDVM_ENCODE_OPCODE(0, SdvmOp ## opcode, SdvmType ## type, SdvmType ## arg0Type, SdvmType ## arg1Type),
#include "opcode.inc"
#undef SDVM_CONSTANT_DEF
#undef SDVM_INSTRUCTION_DEF
} sdvm_opcode_t;

#endif //SDVM_INSTRUCTION_H
