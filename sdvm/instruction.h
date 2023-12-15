#ifndef SDVM_INSTRUCTION_H
#define SDVM_INSTRUCTION_H

#include <stdint.h>

typedef enum sdvm_opcode_e
{
#define SDVM_OPCODE_DEF(name, value, description) SdvmOp ## name = value
#include "opcode.inc"
#undef SDVM_OPCODE_DEF
} sdvm_opcode_t;

typedef struct sdvm_instruction_s
{
    int32_t opcode;
    int32_t destination;
    int32_t arg0;
    int32_t arg1;
} sdvm_instruction_t;

#endif //SDVM_INSTRUCTION_H
