#ifndef SDVM_INSTRUCTION_H
#define SDVM_INSTRUCTION_H

#include <stdint.h>
#include <stdbool.h>
#include "common.h"

#define SDVM_TYPE_BITS 5
#define SDVM_TYPE_MASK ((1<<SDVM_TYPE_BITS) - 1)

typedef enum sdvm_type_e
{
#define SDVM_TYPE_DEF(name, code) SdvmType ## name = code,
#include "type.inc"
#undef SDVM_TYPE_DEF
} sdvm_type_t;

#define SDVM_ENCODE_OPCODE(isConstant, opcode, destinationType, arg0Type, arg1Type) \
    (isConstant \
        ? (1 | (opcode << 1) | (destinationType << 7)) \
        : (opcode << 1) | (destinationType << 9) | (arg0Type << 14) | (arg1Type << 19))

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
 * Payload/52 - DestinationType/4 - Opcode/6 bits - 1/1
 * 
 * Instructions have the following format (Least significant bit is 0):
 * Arg1/20 - Arg0/20 - Instruction spec (Arg1Type/5 - Arg0Type/5 - DestinationType/5 - Opcode/8 - 0/1)/24
 */
typedef uint64_t sdvm_constOrInstruction_t;

typedef struct sdvm_decodedConstOrInstruction_s
{
    uint8_t isConstant : 1;
    uint8_t arg0IsInstruction : 1;
    uint8_t arg1IsInstruction : 1;

    uint32_t opcode;
    uint32_t baseOpcode;
    sdvm_type_t destType;
    union
    {
        struct
        {
            sdvm_type_t arg0Type;
            sdvm_type_t arg1Type;
            int32_t arg0;
            int32_t arg1;
        } instruction;

        struct
        {
            int64_t signedPayload;
            int64_t unsignedPayload;
        } constant;
    };
} sdvm_decodedConstOrInstruction_t;

SDVM_API const char *sdvm_instruction_typeToString(sdvm_type_t type);
SDVM_API const char *sdvm_instruction_fullOpcodeToString(sdvm_opcode_t opcode);
SDVM_API bool sdvm_instruction_typeExpectsInstruction(sdvm_type_t type);
SDVM_API sdvm_decodedConstOrInstruction_t sdvm_instruction_decode(sdvm_constOrInstruction_t instruction);

#endif //SDVM_INSTRUCTION_H
