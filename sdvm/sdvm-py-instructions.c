#include "instruction.h"
#include <stdio.h>

int main()
{
    printf("from .sdvmInstructionTypes import *\n");
    printf("\n");

#define SDVM_TYPE_DEF(name, code) \
    printf("SdvmType%s = sdvmTypeDef('%s', code = %d)\n", #name, #name, code);
#include "type.inc"
#undef SDVM_TYPE_DEF

#define SDVM_CONSTANT_OPCODE_DEF(name, opcode, description) \
    printf("SdvmConstOp%s = sdvmConstantOpcodeDef('SdvmOp%s', opcode = 0x%04X, description = '%s')\n", #name, #name, SdvmConstOp ## name, #description);

#define SDVM_CONSTANT_DEF(name, opcode, type, description) \
    printf("SdvmConst%s = sdvmConstantDef('SdvmConst%s', opcode = 0x%04X, type = SdvmType%s, description = '%s')\n", #name, #name, SdvmConst ## name, #type, #description);
#define SDVM_OPCODE_DEF(name, opcode, description) \
    printf("SdvmOp%s = sdvmOpcodeDef('SdvmOp%s', opcode = 0x%04X, description = '%s')\n", #name, #name, SdvmOp ## name, #description);
#define SDVM_INSTRUCTION_DEF(name, opcode, type, arg0Type, arg1Type, description) \
    printf("SdvmInst%s = sdvmInstructionDef('SdvmInst%s', opcode = 0x%04X, type = SdvmType%s, arg0Type = SdvmType%s, arg1Type = SdvmType%s, description = '%s')\n", \
        #name, #name, SdvmInst ## name, #type, #arg0Type, #arg1Type, description);
#include "opcode.inc"
#undef SDVM_CONSTANT_OPCODE_DEF
#undef SDVM_CONSTANT_DEF
#undef SDVM_OPCODE_DEF
#undef SDVM_INSTRUCTION_DEF

    return 0;
}