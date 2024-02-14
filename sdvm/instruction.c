#include "instruction.h"

const char *sdvm_instruction_typeToString(sdvm_type_t type)
{
    switch(type)
    {
#define SDVM_TYPE_DEF(name, code) case SdvmType ## name: return "SdvmType" #name;
#include "type.inc"
#undef SDVM_TYPE_DEF
    default: return "Unknown";
    }
}
const char *sdvm_instruction_fullOpcodeToString(sdvm_opcode_t opcode)
{
    switch(opcode)
    {
#define SDVM_CONSTANT_DEF(name, opcode, type, description) \
    case SdvmConst ## name: return "SdvmConst" #name;
#define SDVM_OPCODE_DEF(name, opcode, description)
#define SDVM_INSTRUCTION_DEF(name, opcode, type, arg0Type, arg1Type, description) \
    case SdvmInst ## name: return "SdvmInst" #name;
#include "opcode.inc"
#undef SDVM_CONSTANT_DEF
#undef SDVM_OPCODE_DEF
#undef SDVM_INSTRUCTION_DEF
    default: return "Unknown";
    }
}

static int sdvm_intruction_decodeArg(uint32_t argValue)
{
    return (argValue & ((1<<19) - 1)) - (argValue & (1<<19));
}

sdvm_decodedConstOrInstruction_t sdvm_instruction_decode(sdvm_constOrInstruction_t instruction)
{
    sdvm_decodedConstOrInstruction_t decoded = {0};
    decoded.isConstant = (instruction & 1) != 0;
    if(decoded.isConstant)
    {
        decoded.opcode = instruction & ((1<<12) - 1);
        decoded.baseOpcode = (decoded.opcode >> 1) & ((1<<7) - 1);
        decoded.destType = (decoded.opcode >> 8) & SDVM_TYPE_MASK;
        decoded.constant.signedPayload = (int64_t)instruction >> 12;
        decoded.constant.unsignedPayload = (uint64_t)instruction >> 12;
    }
    else
    {
        decoded.opcode = instruction & ((1<<24) - 1);
        decoded.baseOpcode = (decoded.opcode >> 1) & ((1<<11) - 1);
        decoded.destType = (decoded.opcode >> 12) & SDVM_TYPE_MASK;
        decoded.instruction.arg0Type = (decoded.opcode >> 16) & SDVM_TYPE_MASK;
        decoded.instruction.arg1Type = (decoded.opcode >> 20) & SDVM_TYPE_MASK;
        decoded.instruction.arg0 = sdvm_intruction_decodeArg(instruction >> 24);
        decoded.instruction.arg1 = sdvm_intruction_decodeArg(instruction >> 44);
    }

    return decoded;
}