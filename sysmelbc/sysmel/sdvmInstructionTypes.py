class SdvmTypeDef:
    def __init__(self, code: int, name: str) -> None:
        self.code = code
        self.name = name

    def __str__(self) -> str:
        return self.name

class SdvmConstantDef:
    def __init__(self, name: str, opcode: int, type: SdvmTypeDef, description: str) -> None:
        self.name = name
        self.opcode = opcode
        self.type = type
        self.description = description

class SdvmOpcodeDef:
    def __init__(self, name: str, opcode: int, description: str) -> None:
        self.name = name
        self.opcode = opcode
        self.description = description

class SdvmInstructionDef:
    def __init__(self, name: str, opcode: int, type: SdvmTypeDef, arg0Type: SdvmTypeDef, arg1Type: SdvmTypeDef, description: str) -> None:
        self.name = name
        self.opcode = opcode
        self.type = type
        self.arg0Type = arg0Type
        self.arg1Type = arg1Type
        self.description = description

def sdvmTypeDef(name: str, code: int):
    return SdvmTypeDef(name, code)

def sdvmConstantDef(name: str, opcode: int, type: SdvmTypeDef, description: str):
    return SdvmConstantDef(name, opcode, type, description)

def sdvmOpcodeDef(name: str, opcode: int, description: str):
    return SdvmOpcodeDef(name, opcode, description)

def sdvmInstructionDef(name: str, opcode: int, type: SdvmTypeDef, arg0Type: SdvmTypeDef, arg1Type: SdvmTypeDef, description: str):
    return SdvmInstructionDef(name, opcode, type, arg0Type, arg1Type, description)
