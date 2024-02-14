#ifndef SDVM_INSTRUCTION_H
#define SDVM_INSTRUCTION_H

#include <stdint.h>

typedef enum sdvm_type_e
{
#define SDVM_TYPE_DEF(name, code) SdvmType ## name = code,
#include "type.inc"
#undef SDVM_TYPE_DEF
} sdvm_type_t;

#define SDVM_ENCODE_OPCODE(isConstant, opcode, destinationType, arg0Type, arg1Type) \
    (isConstant \
        ? (1 | (opcode << 1) | (destinationType << 8)) \
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
#undef SDVM_OPCODE_DEF
#undef SDVM_INSTRUCTION_DEF
} sdvm_opcode_t;

/**
 * Instruction and inline constants are 64 bits long. The destination index is implicit.

 * Constants have the following format (Least significant bit is 1):
 * Payload/52 - DestinationType/4 - Opcode/7 bits - 1/1
 * 
 * Instructions have the following format (Least significant bit is 0):
 * Arg1/20 - Arg0/20 - Instruction spec (Arg1Type/4 - Arg0Type/4 - DestinationType/4 - Opcode/11 - 0/1)/24
 */
typedef uint64_t sdvm_constOrInstruction_t;

#endif //SDVM_INSTRUCTION_H
