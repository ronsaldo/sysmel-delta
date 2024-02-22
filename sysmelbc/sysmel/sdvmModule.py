import struct
from .sdvmInstructionTypes import *
from .sdvmInstructions import *

def sdvmModuleFourCC(cc):
    assert len(cc) == 4
    return ord(cc[0]) | (ord(cc[1]) << 8) | (ord(cc[2]) << 16) | (ord(cc[3]) << 24)

SdvmModuleMagic = sdvmModuleFourCC('SDVM')
SdvmModuleVersion = 1

SdvmModuleHeaderSize = 24
SdvmModuleSectionHeaderSize = 12

SdvmModuleSectionTypeNull = 0
SdvmModuleSectionTypeConstant = sdvmModuleFourCC('cont')
SdvmModuleSectionTypeText = sdvmModuleFourCC('text')
SdvmModuleSectionTypeFunctionTable = sdvmModuleFourCC('funt')

SdvmModuleSectionTypeDebugLineStart = sdvmModuleFourCC('dlns')
SdvmModuleSectionTypeDebugLineEnd = sdvmModuleFourCC('dlne')

class SDVMModule:
    def __init__(self, pointerSize = 8) -> None:
        self.pointerSize = pointerSize
        self.constantSection = SDVMConstantSection()
        self.textSection = SDVMTextSection()
        self.functionTable = SDVMFunctionTableSection()
        self.sections: list[SDVMModuleSection] = [SDVMNullSection(), self.constantSection, self.textSection, self.functionTable]
        self.entryPoint = 0
        self.entryPointClosure = 0

    def exportValue(self, name: str, value):
        pass

    def newFunction(self, name: str = None):
        function = SDVMFunction(self, name)
        self.functionTable.addFunction(function)
        return function

    def finishBuilding(self):
        self.functionTable.finishBuilding()

    def prettyPrint(self) -> str:
        result = ''
        if self.entryPoint != 0:
            result += 'entryPoint: %d\n' % self.entryPoint
        if self.entryPointClosure != 0:
            result += 'entryPointClosure: %d\n' % self.entryPointClosure

        for section in self.sections:
            result += section.prettyPrint()
        return result

    def encode(self) -> bytearray:
        startOffset = SdvmModuleHeaderSize + SdvmModuleSectionHeaderSize * len(self.sections)
        for section in self.sections:
            startOffset += section.finish(startOffset)

        result = bytearray()
        result += struct.pack('<IIIIII', SdvmModuleMagic, SdvmModuleVersion, self.pointerSize, len(self.sections), self.entryPoint, self.entryPointClosure)
        for section in self.sections:
            result += struct.pack('<III', section.sectionType, section.fileOffset, len(section.contents))
        for section in self.sections:
            result += section.contents        
        return result
    
    def saveToFileNamed(self, fileName):
        encodedModule = self.encode()
        with open(fileName, "wb") as f:
            f.write(encodedModule)

class SDVMModuleSection:
    def __init__(self, sectionType) -> None:
        self.sectionType = sectionType
        self.contents = bytearray()
        self.fileOffset = 0

    def getSize(self) -> int:
        return self.size

    def finish(self, fileOffset) -> int:
        self.fileOffset = fileOffset
        return len(self.contents)
    
    def prettyPrint(self) -> str:
        return 'section type %08x size %d\n' % (self.sectionType, len(self.contents))
    
    def appendData(self, data) -> tuple[int, int]:
        offset = len(self.contents)
        self.contents += data
        return offset, len(data)

class SDVMNullSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeNull)

class SDVMConstantSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeConstant)

class SDVMTextSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeText)

class SDVMFunctionTableSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeFunctionTable)
        self.functions: list[SDVMFunction] = []

    def addFunction(self, function):
        assert function.index is None
        assert function not in self.functions
        self.functions.append(function)
        function.index = len(self.functions)

    def finishBuilding(self):
        for function in self.functions:
            function.finishBuilding()

        self.contents = bytearray()
        for function in self.functions:
            self.contents += struct.pack('<II', function.textSectionOffset, function.textSectionSize)

    def prettyPrint(self) -> str:
        result = super().prettyPrint()
        for function in self.functions:
            result += function.prettyPrint()
        result += '\n'
        return result

class SDVMOperand:
    def __init__(self) -> None:
        self.index = None

    def __str__(self) -> str:
        return '$%d' % self.index

class SDVMInlineConstant(SDVMOperand):
    def __init__(self, definition: SdvmConstantDef, value = None, payload: int = 0) -> None:
        super().__init__()
        self.definition = definition
        self.value = value
        self.payload = payload

    def prettyPrint(self) -> str:
        if self.value is None:
            return '%s := %s()' % (str(self), self.definition.name)
        return '%s := %s(%s)' % (str(self), self.definition.name, str(self.value))
    
    def encode(self) -> int:
        return struct.pack('<Q', self.definition.opcode | (self.payload << 12))

class SDVMInstruction(SDVMOperand):
    def __init__(self, definition: SdvmInstructionDef, arg0: SDVMOperand | None = None, arg1: SDVMOperand | None = None) -> None:
        super().__init__()
        self.definition = definition
        self.arg0 = arg0
        self.arg1 = arg1

    def prettyPrint(self) -> str:
        if self.arg1 is None:
            if self.arg0 is None:
                return '%s := %s()' % (str(self), self.definition.name)
            return '%s := %s(%s)' % (str(self), self.definition.name, str(self.arg0))
        return '%s := %s(%s, %s)' % (str(self), self.definition.name, str(self.arg0), str(self.arg1))
    
    def encodeArgument(self, arg) -> int:
        if arg is None:
            return 0
        if isinstance(arg, int):
            return arg & ((1<<20) - 1)
        return arg.index & ((1<<20) - 1)

    def encode(self) -> int:
        return struct.pack('<Q', self.definition.opcode | (self.encodeArgument(self.arg0) << 24) | (self.encodeArgument(self.arg1) << 44))

class SDVMFunction:
    def __init__(self, module: SDVMModule, name: str = None) -> None:
        self.module = module
        self.name = name
        self.constants = []
        self.argumentInstructions = []
        self.captureInstructions = []
        self.instructions = []
        self.textSectionOffset = 0
        self.textSectionSize = 0
        self.isFinished = False
        self.index = None

    def addInlineConstant(self, constant: SDVMInlineConstant) -> SDVMInlineConstant:
        self.constants.append(constant)
        return constant

    def addArgumentInstruction(self, instruction: SDVMInstruction) -> SDVMInlineConstant:
        self.argumentInstructions.append(instruction)
        return instruction

    def addCaptureInstruction(self, instruction: SDVMInstruction) -> SDVMInlineConstant:
        self.captureInstructions.append(instruction)
        return instruction

    def addInstruction(self, instruction: SDVMInstruction) -> SDVMInlineConstant:
        self.instructions.append(instruction)
        return instruction
    
    def beginArguments(self, argumentCount: int) -> SDVMInstruction | None:
        if argumentCount == 0:
            return
        return self.addArgumentInstruction(SDVMInstruction(SdvmInstBeginArguments, argumentCount, 0))

    def beginCaptures(self, captureCount: int) -> SDVMInstruction | None:
        if captureCount == 0:
            return
        return self.addCaptureInstruction(SDVMInstruction(SdvmInstBeginCaptures, captureCount))

    def const(self, definition: SdvmConstantDef, value: int = 0, payload: int = 0) -> SDVMInlineConstant:
        return self.addInlineConstant(SDVMInlineConstant(definition, value, payload))

    def inst(self, definition: SdvmInstructionDef, arg0: SDVMOperand | None = None, arg1: SDVMOperand | None = None) -> SDVMInlineConstant:
        return self.addInstruction(SDVMInstruction(definition, arg0, arg1))

    def constBoolean(self, value: bool) -> SDVMInlineConstant:
        if value:
            return self.const(SdvmConstBoolean, 1, value)
        else:
            return self.const(SdvmConstBoolean, 0, value)

    def constInt8(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstInt8, value, value)

    def constInt16(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstInt16, value, value)

    def constInt32(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstInt32, value, value)

    def constInt64(self, value: int) -> SDVMInlineConstant:
        ## FIXME: Check the payload range
        return self.const(SdvmConstInt64SExt, value, value)

    def constUInt8(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstUInt8, value, value)

    def constUInt16(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstUInt16, value, value)

    def constUInt32(self, value: int) -> SDVMInlineConstant:
        return self.const(SdvmConstUInt32, value, value)

    def constUInt64(self, value: int) -> SDVMInlineConstant:
        ## FIXME: Check the payload range
        return self.const(SdvmConstUInt64ZExt, value, value)

    def constFloat32(self, value: float) -> SDVMInlineConstant:
        assert False

    def constFloat64(self, value: float) -> SDVMInlineConstant:
        assert False

    def finishBuilding(self):
        if self.isFinished:
            return

        self.textSectionOffset, self.textSectionSize = self.module.textSection.appendData(self.encodeInstructions())
        self.isFinished = True

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (self.name, self.index)
        return '@%d' % self.index

    def prettyPrint(self):
        self.enumerateInstructions()
        result = '%s:\n' % str(self)
        for instruction in self.allInstructions():
            result += '    %s\n' % instruction.prettyPrint()
        return result
    
    def allInstructions(self):
        for instruction in self.constants:
            yield instruction
        for instruction in self.argumentInstructions:
            yield instruction
        for instruction in self.captureInstructions:
            yield instruction
        for instruction in self.instructions:
            yield instruction
    
    def enumerateInstructions(self):
        index = 0
        for instruction in self.allInstructions():
            instruction.index = index
            index += 1

    def encodeInstructions(self):
        self.enumerateInstructions()
        encodedInstructions = bytearray()
        for instruction in self.allInstructions():
            encodedInstructions += instruction.encode()
        return encodedInstructions

