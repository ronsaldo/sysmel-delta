import struct
from .sdvmInstructionTypes import *
from .sdvmInstructions import *
from .memoryDescriptor import *

def sdvmModuleFourCC(cc):
    assert len(cc) == 4
    return ord(cc[0]) | (ord(cc[1]) << 8) | (ord(cc[2]) << 16) | (ord(cc[3]) << 24)

SdvmModuleMagic = sdvmModuleFourCC('SDVM')
SdvmModuleVersion = 1

SdvmModuleHeaderSize = 36
SdvmModuleSectionHeaderSize = 12

SdvmModuleSectionTypeNull = 0
SdvmModuleSectionTypeConstant = sdvmModuleFourCC('cont')
SdvmModuleSectionTypeData = sdvmModuleFourCC('data')
SdvmModuleSectionTypeText = sdvmModuleFourCC('text')
SdvmModuleSectionTypeString = sdvmModuleFourCC('strn')
SdvmModuleSectionTypeFunctionTable = sdvmModuleFourCC('funt')
SdvmModuleSectionTypeObjectTable = sdvmModuleFourCC('objt')
SdvmModuleSectionTypeImportModuleTable = sdvmModuleFourCC('impm')
SdvmModuleSectionTypeImportModuleValueTable = sdvmModuleFourCC('impv')
SdvmModuleSectionTypeExportModuleValueTable = sdvmModuleFourCC('expv')
SdvmModuleSectionTypeMemoryDescriptorTable = sdvmModuleFourCC('memd')

SdvmModuleSectionTypeDebugSourceDirectory = sdvmModuleFourCC('dsrd')
SdvmModuleSectionTypeDebugSourceCode = sdvmModuleFourCC('dsrc')
SdvmModuleSectionTypeDebugLineData = sdvmModuleFourCC('dlnd')
SdvmModuleSectionTypeDebugFunctionTable = sdvmModuleFourCC('dfnt')

SdvmModuleValueKindNull = 0
SdvmModuleValueKindFunctionHandle = sdvmModuleFourCC('funh')
SdvmModuleValueKindDataSectionValue = sdvmModuleFourCC('data')
SdvmModuleValueKindConstantSectionValue = sdvmModuleFourCC('cont')
SdvmModuleValueKindObjectHandle = sdvmModuleFourCC('objh')

SdvmModuleExternalTypeNone = 0
SdvmModuleExternalTypeC = sdvmModuleFourCC('C   ')
SdvmModuleExternalTypeCpp = sdvmModuleFourCC('C++ ')

SdvmDebugSourceCodeKindFile = sdvmModuleFourCC('file')
SdvmDebugSourceCodeKindString = sdvmModuleFourCC('strn')

SdvmModuleExternalTypeMap = {None: SdvmModuleExternalTypeNone, '': SdvmModuleExternalTypeNone, 'C': SdvmModuleExternalTypeC}

SdvmConstantPayloadBits = 52
SdvmConstantPayloadHalfBits = SdvmConstantPayloadBits // 2
SdvmConstantPayloadHalfMaxValue = (1 << SdvmConstantPayloadHalfBits) - 1

SdvmBeginCallFixedArgumentMask = 0xFF
SdvmBeginCallVariadicFlag = 1<<8

class SDVMString:
    def __init__(self, offset: int = 0, size: int = 0, value: str = None) -> None:
        self.value = value
        self.offset = offset
        self.size = size

    def encodeForConstant(self) -> int:
        assert 0 <= self.offset and self.offset <= SdvmConstantPayloadHalfMaxValue
        assert 0 <= self.size and self.size <= SdvmConstantPayloadHalfMaxValue
        return self.offset | (self.size << SdvmConstantPayloadHalfBits)

    def __str__(self) -> str:
        if self.size == 0:
            return ''
        return self.value.decode('utf-8')
    
class SDVMModule:
    def __init__(self, pointerSize: int = 8) -> None:
        self.pointerSize = pointerSize
        self.constantSection = SDVMConstantSection()
        self.dataSection = SDVMDataSection()
        self.textSection = SDVMTextSection()
        self.stringSection = SDVMStringSection()
        self.importModuleTable = SDVMImportModuleTableSection(self)
        self.importModuleValueTable = SDVMImportModuleValueTableSection(self)
        self.objectTable = SDVMObjectTableSection()
        self.functionTable = SDVMFunctionTableSection()
        self.exportModuleValueTable = SDVMExportModuleValueTableSection(self)
        self.memoryDescriptorTable = SDVMMemoryDescriptorTableSection(self)
        self.debugSourceDirectoryTable = SDVMDebugSourceDirectoryTableSection(self)
        self.debugSourceCodeTable = SDVMDebugSourceCodeTableSection(self)
        self.debugLineData = SDVMDebugLineDataSection(self)
        self.debugFunctionTable = SDVMDebugFunctionTableSection(self)

        self.sections: list[SDVMModuleSection] = [
            SDVMNullSection(),
            self.constantSection, self.dataSection, self.textSection,
            self.stringSection,
            self.memoryDescriptorTable, self.objectTable,
            self.importModuleTable, self.importModuleValueTable,
            self.functionTable, self.exportModuleValueTable,
            self.debugSourceDirectoryTable, self.debugSourceCodeTable, self.debugLineData, self.debugFunctionTable
        ]
        self.entryPoint = 0
        self.entryPointClosure = 0
        self.name = self.addString('')

    def importModule(self, name: str):
        return self.importModuleTable.importModule(name)
    
    def importExternalValue(self, externalName: str, valueName: str, typeDescriptor: str):
        return self.importModuleValueTable.importExternalValue(externalName, valueName, typeDescriptor)

    def exportValue(self, name: str, value, externalName: str, typeDescriptor: str):
        return value.addExportEntryIntoModule(self, name, externalName, typeDescriptor)
    
    def exportFunctionHandle(self, function, name: str, externalName: str, typeDescriptor: str):
        return self.exportModuleValueTable.exportValue(SdvmModuleValueKindFunctionHandle, SdvmModuleExternalTypeMap[externalName], function.index, name, typeDescriptor)

    def addString(self, value: str) -> SDVMString:
        return self.stringSection.add(value)

    def addEncodedString(self, value: bytes) -> SDVMString:
        return self.stringSection.addEncoded(value)
    
    def addMemoryDescriptor(self, descriptor: MemoryDescriptor):
        return self.memoryDescriptorTable.addDescriptor(descriptor)

    def setName(self, name: str) -> SDVMString:
        self.name = self.addString(name)
        return self.name
    
    def newFunction(self, name: str = None, typeDescriptor: str = None, sourcePosition = None):
        function = SDVMFunction(self, name, typeDescriptor, sourcePosition)
        self.functionTable.addFunction(function)
        self.debugFunctionTable.addFunction(function)
        return function

    def finishBuilding(self):
        self.functionTable.finishBuilding()
        self.debugFunctionTable.finishBuilding()

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
        result += struct.pack('<IIIIIIIII', SdvmModuleMagic, SdvmModuleHeaderSize, SdvmModuleVersion, self.pointerSize, len(self.sections), self.entryPoint, self.entryPointClosure, self.name.offset, self.name.size)
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

class SDVMDataSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeConstant)

class SDVMTextSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeText)

class SDVMStringSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeString)
        self.stringDict: dict[str,SDVMString] = dict()
        self.encodedStringDict: dict[bytes,SDVMString] = dict()

    def add(self, value: str) -> SDVMString:
        if value is None or len(value) == 0:
            return SDVMString()
        if value in self.stringDict:
            return self.stringDict[value]
        
        stringValue = self.addEncoded(value.encode('utf-8'))
        self.stringDict[value] = stringValue
        return stringValue

    def addEncoded(self, encodedValue: bytes) -> SDVMString:
        if encodedValue is None or len(encodedValue) == 0:
            return SDVMString()
        if encodedValue in self.encodedStringDict:
            return self.encodedStringDict

        stringValue = SDVMString(len(self.contents), len(encodedValue), encodedValue)
        self.contents += encodedValue
        self.encodedStringDict[encodedValue] = stringValue
        return stringValue

class SDVMImportModuleTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeImportModuleTable)
        self.module = module
        self.importedModules: list[SDVMImportedModule] = []

    def importModule(self, name: str):
        importedModule = SDVMImportedModule(self.module, name)
        self.importedModules.append(importedModule)
        importedModule.index = len(self.importedModules)
        self.contents += importedModule.encode()
        return importedModule

class SDVMImportModuleValueTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeImportModuleValueTable)
        self.module = module
        self.importedModuleValues: list[SDVMImportedModuleValue] = []

    def importModuleValue(self, importedModule, name: str, typeDescriptor: str):
        importedModuleValue = SDVMImportedModuleValue(self.module, importedModule, name, typeDescriptor)
        self.importedModuleValues.append(importedModuleValue)
        importedModuleValue.index = len(self.importedModuleValues)
        self.contents += importedModuleValue.encode()
        return importedModuleValue
    
    def importExternalValue(self, externalName: str, valueName: str, typeDescriptor: str):
        importedExternalValue = SDVMImportedExternalValue(self.module, externalName, valueName, typeDescriptor)
        self.importedModuleValues.append(importedExternalValue)
        importedExternalValue.index = len(self.importedModuleValues)
        self.contents += importedExternalValue.encode()
        return importedExternalValue

class SDVMObjectTableSection(SDVMModuleSection):
    def __init__(self,) -> None:
        super().__init__(SdvmModuleSectionTypeObjectTable)

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
            self.contents += function.encode()

    def prettyPrint(self) -> str:
        result = super().prettyPrint()
        for function in self.functions:
            result += function.prettyPrint()
        result += '\n'
        return result

class SDVMDebugSourceDirectoryTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeDebugSourceDirectory)
        self.module = module
        self.directoryTable = dict()
    
    def getOrAddDirectory(self, value: str) -> int:
        if value is None or value == '':
            return 0

        if value in self.directoryTable:
            return self.directoryTable[value]
        
        string = self.module.addString(value)
        self.contents += struct.pack('<II', string.offset, string.size)
        index = len(self.directoryTable) + 1
        self.directoryTable[value] = index
        return index

class SDVMDebugSourceCodeTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeDebugSourceCode)
        self.module = module
        self.sourceCodeTable = dict()
    
    def getOrAddSourceCode(self, sourceCode) -> int:
        if sourceCode is None: return 0
        if sourceCode in self.sourceCodeTable:
            return self.sourceCodeTable[sourceCode]
        
        index = len(self.sourceCodeTable) + 1

        kind = SdvmDebugSourceCodeKindFile
        directory = self.module.debugSourceDirectoryTable.getOrAddDirectory(sourceCode.directory)
        name = self.module.addString(sourceCode.name)
        language = self.module.addString(sourceCode.language)
        self.contents += struct.pack('<IIIIIIII', kind, directory, name.offset, name.size, language.offset, language.size, 0, 0)
        self.sourceCodeTable[sourceCode] = index
        return index

class SDVMDebugLineDataSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeDebugLineData)
        self.module = module
        self.tableSize = 0
        self.lastSourcePosition = None

    def getTableSize(self) -> int:
        return self.tableSize
    
    def beginBuildingFunction(self):
        self.lastSourcePosition = None

    def endBuildingFunction(self):
        pass

    def addLineSourcePositionEntry(self, pc, sourcePosition):
        if self.lastSourcePosition == sourcePosition:
            return
        
        sourceCode = 0
        startIndex = 0
        endIndex = 0
        startLine = 0
        endLine = 0
        startColumn = 0
        endColumn = 0

        if sourcePosition is not None:
            sourceCode = self.module.debugSourceCodeTable.getOrAddSourceCode(sourcePosition.sourceCode)
            startIndex = sourcePosition.startIndex
            endIndex = sourcePosition.endIndex
            startLine = sourcePosition.startLine
            endLine = sourcePosition.endLine
            startColumn = sourcePosition.startColumn
            endColumn = sourcePosition.endColumn
       
        self.contents += struct.pack('<IIIIIIII', pc, sourceCode, startIndex, endIndex, startLine, endLine, startColumn, endColumn)
        self.tableSize += 1
        self.lastSourcePosition = sourcePosition

class SDVMDebugFunctionTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeDebugFunctionTable)
        self.module = module
        self.functions = []

    def addFunction(self, function):
        self.functions.append(function)

    def buildDebugFunctionData(self, function):
        sourceCode = 0
        startIndex = 0
        endIndex = 0
        startLine = 0
        endLine = 0
        startColumn = 0
        endColumn = 0

        if function.sourcePosition is not None:
            sourceCode = self.module.debugSourceCodeTable.getOrAddSourceCode(function.sourcePosition.sourceCode)
            startIndex = function.sourcePosition.startIndex
            endIndex = function.sourcePosition.endIndex
            startLine = function.sourcePosition.startLine
            endLine = function.sourcePosition.endLine
            startColumn = function.sourcePosition.startColumn
            endColumn = function.sourcePosition.endColumn

        pc = 0
        self.module.debugLineData.beginBuildingFunction()
        sourceLineInfoStartIndex = self.module.debugLineData.getTableSize()
        for instruction in function.allInstructions():
            self.module.debugLineData.addLineSourcePositionEntry(pc, instruction.sourcePosition)
            pc += 1
        self.module.debugLineData.endBuildingFunction()
        sourceLineInfoEntryCount = self.module.debugLineData.getTableSize() - sourceLineInfoStartIndex

        return struct.pack('<IIIIIIIII', sourceCode, startIndex, endIndex, startLine, endLine, startColumn, endColumn, sourceLineInfoStartIndex, sourceLineInfoEntryCount)


    def finishBuilding(self):
        for function in self.functions:
            self.contents += self.buildDebugFunctionData(function)

class SDVMExportModuleValueTableEntry:
    def __init__(self, module: SDVMModule, kind: int, externalType: int, firstValue: int, secondValue: int, name: str, typeDescriptor: str) -> None:
        self.kind = kind
        self.externalType = externalType
        self.firstValue = firstValue
        self.secondValue = secondValue
        self.name = module.addString(name)
        self.typeDescriptor = module.addString(typeDescriptor)

    def encode(self) -> bytes:
        return struct.pack('<IIQQIIII', self.kind, self.externalType, self.firstValue, self.secondValue, self.name.offset, self.name.size, self.typeDescriptor.offset, self.typeDescriptor.size)

class SDVMExportModuleValueTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeExportModuleValueTable)
        self.module = module
        self.entries = []

    def exportValue(self, kind: int, externalType: int, value: int, name: str, typeDescriptor: str):
        exportedEntry = SDVMExportModuleValueTableEntry(self.module, kind, externalType, value, 0, name, typeDescriptor)
        self.contents += exportedEntry.encode()
        self.entries.append(exportedEntry)

class SDVMMemoryDescriptorTableSection(SDVMModuleSection):
    def __init__(self, module: SDVMModule) -> None:
        super().__init__(SdvmModuleSectionTypeMemoryDescriptorTable)
        self.entries = []
        self.encodedDescriptors = dict()

    def addDescriptor(self, descriptor: MemoryDescriptor):
        if descriptor in self.encodedDescriptors:
            return self.encodedDescriptors[descriptor]
        
        sdvmDescriptor = SDVMMemoryDescriptor(descriptor)
        self.entries.append(sdvmDescriptor)
        self.contents += sdvmDescriptor.encode()
        sdvmDescriptor.index = len(self.entries)
        self.encodedDescriptors[descriptor] = sdvmDescriptor
        return sdvmDescriptor

class SDVMOperand:
    def __init__(self) -> None:
        self.index = None

    def __str__(self) -> str:
        return '$%d' % self.index
    
    def isInstruction(self):
        return False
    
    def markUsedOperand(self):
        pass

    def clearUsedOpenad(self):
        pass

class SDVMMemoryDescriptor(SDVMOperand):
    def __init__(self, descriptor: MemoryDescriptor) -> None:
        super().__init__()
        self.descriptor = descriptor

    def __str__(self) -> str:
        return 'memd:%d %s' % (self.index, str(self.descriptor))

    def encode(self) -> bytes:
        return struct.pack('<QQII', self.descriptor.alignment, self.descriptor.size, 0, 0)
    
class SDVMConstant(SDVMOperand):
    def __init__(self, definition: SdvmConstantDef, value = None, payload: int = 0, sourcePosition = None) -> None:
        super().__init__()
        self.definition = definition
        self.value = value
        self.payload = payload
        self.sourcePosition = sourcePosition

    def prettyPrint(self) -> str:
        if self.value is None:
            return '%s := %s()' % (str(self), self.definition.name)
        return '%s := %s(%s)' % (str(self), self.definition.name, str(self.value))
    
    def encode(self) -> int:
        return struct.pack('<Q', self.definition.opcode | (self.payload << 12))

class SDVMInstruction(SDVMOperand):
    def __init__(self, definition: SdvmInstructionDef, arg0: SDVMOperand = None, arg1: SDVMOperand = None, sourcePosition = None) -> None:
        super().__init__()
        self.definition = definition
        self.arg0 = arg0
        self.arg1 = arg1
        self.sourcePosition = sourcePosition
        self.isUsedAsOperand = False

    def isInstruction(self):
        return True
    
    def isLabel(self):
        return self.definition is SdvmConstLabel

    def markUsedOperand(self):
        self.isUsedAsOperand = True

    def clearUsedOpenad(self):
        self.isUsedAsOperand = False

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
    def __init__(self, module: SDVMModule, name: str = None, typeDescriptor: str = None, sourcePosition = None) -> None:
        self.module = module
        self.name = module.addString(name)
        self.typeDescriptor = module.addString(typeDescriptor)
        self.sourcePosition = sourcePosition
        self.constants = []
        self.argumentInstructions = []
        self.captureInstructions = []
        self.instructions = []
        self.textSectionOffset = 0
        self.textSectionSize = 0
        self.isFinished = False
        self.index = None

    def addExportEntryIntoModule(self, module, name: str, externalName: str, typeDescriptor: str):
        return module.exportFunctionHandle(self, name, externalName, typeDescriptor)

    def addConstant(self, constant: SDVMConstant) -> SDVMConstant:
        self.constants.append(constant)
        return constant

    def addArgumentInstruction(self, instruction: SDVMInstruction) -> SDVMConstant:
        self.argumentInstructions.append(instruction)
        return instruction

    def addCaptureInstruction(self, instruction: SDVMInstruction) -> SDVMConstant:
        self.captureInstructions.append(instruction)
        return instruction

    def addInstruction(self, instruction: SDVMInstruction) -> SDVMConstant:
        self.instructions.append(instruction)
        return instruction
    
    def beginArguments(self, argumentCount: int) -> SDVMInstruction:
        if argumentCount == 0:
            return
        return self.addArgumentInstruction(SDVMInstruction(SdvmInstBeginArguments, argumentCount, 0))

    def beginCaptures(self, captureCount: int) -> SDVMInstruction:
        if captureCount == 0:
            return
        return self.addCaptureInstruction(SDVMInstruction(SdvmInstBeginCaptures, captureCount))

    def const(self, definition: SdvmConstantDef, value: int = 0, payload: int = 0) -> SDVMConstant:
        return self.addConstant(SDVMConstant(definition, value, payload))

    def inst(self, definition: SdvmInstructionDef, arg0: SDVMOperand = None, arg1: SDVMOperand = None) -> SDVMConstant:
        return self.addInstruction(SDVMInstruction(definition, arg0, arg1))

    def constBoolean(self, value: bool) -> SDVMConstant:
        if value:
            return self.const(SdvmConstBoolean, 1, value)
        else:
            return self.const(SdvmConstBoolean, 0, value)

    def constInt8(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstInt8, value, value)

    def constInt16(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstInt16, value, value)

    def constInt32(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstInt32, value, value)

    def constInt64(self, value: int) -> SDVMConstant:
        ## FIXME: Check the payload range
        return self.const(SdvmConstInt64SExt, value, value)

    def constUInt8(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstUInt8, value, value)

    def constUInt16(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstUInt16, value, value)

    def constUInt32(self, value: int) -> SDVMConstant:
        return self.const(SdvmConstUInt32, value, value)

    def constUInt64(self, value: int) -> SDVMConstant:
        ## FIXME: Check the payload range
        return self.const(SdvmConstUInt64ZExt, value, value)

    def constFloat32(self, value: float) -> SDVMConstant:
        ieee754Float, = struct.unpack('<I', struct.pack('<f', value))
        return self.const(SdvmConstFloat32, value, ieee754Float)

    def constFloat64(self, value: float) -> SDVMConstant:
        assert False

    def constFloat32x2(self, value: tuple[float, float]) -> SDVMConstant:
        assert False

    def constFloat32x3(self, value: tuple[float, float, float]) -> SDVMConstant:
        assert False

    def constFloat32x4(self, value: tuple[float, float, float, float]) -> SDVMConstant:
        assert False

    def constFloat64x2(self, value: tuple[float, float]) -> SDVMConstant:
        assert False

    def constFloat64x3(self, value: tuple[float, float, float]) -> SDVMConstant:
        assert False

    def constFloat64x4(self, value: tuple[float, float, float, float]) -> SDVMConstant:
        assert False

    def constInt32x2(self, value: tuple[int, int]) -> SDVMConstant:
        assert False

    def constInt32x3(self, value: tuple[int, int, int]) -> SDVMConstant:
        assert False

    def constInt32x4(self, value: tuple[int, int, int, int]) -> SDVMConstant:
        assert False

    def constUInt32x2(self, value: tuple[int, int]) -> SDVMConstant:
        assert False

    def constUInt32x3(self, value: tuple[int, int, int]) -> SDVMConstant:
        assert False

    def constUInt32x4(self, value: tuple[int, int, int, int]) -> SDVMConstant:
        assert False

    def constCString(self, value: bytes) -> SDVMConstant:
        stringValue = self.module.addEncodedString(value)
        return self.const(SdvmConstPointerCString, stringValue, stringValue.encodeForConstant())

    def constString(self, value: bytes) -> SDVMConstant:
        stringValue = self.module.addEncodedString(value)
        return self.const(SdvmConstPointerString, stringValue, stringValue.encodeForConstant())
    
    def constLocalProcedure(self, value) -> SDVMConstant:
        return self.const(SdvmConstLocalProcedureHandle, value, value.index)
    
    def isSuccessorOf(self, argument, instruction):
        if not argument.isInstruction() or argument.index <= instruction.index:
            return False

        for i in range(instruction.index + 1, argument.index):
            middleInstruction = self.instructions[i]
            if not middleInstruction.isLabel():
                return False
        return True

    def removeJumpsToSuccessor(self):
        self.enumerateOnlyInstructions()
        optimizedInstructions = []
        instructionCount = len(self.instructions)
        for i in range(instructionCount):
            instruction = self.instructions[i]
            if i + 1 < instructionCount:
                if instruction.definition is SdvmInstJump and self.isSuccessorOf(instruction.arg0, instruction):
                    continue
                elif instruction.definition is SdvmInstJumpIfTrue and self.isSuccessorOf(instruction.arg1, instruction):
                    continue
                elif instruction.definition is SdvmInstJumpIfFalse and self.isSuccessorOf(instruction.arg1, instruction):
                    continue
            optimizedInstructions.append(instruction)
        self.instructions = optimizedInstructions

    def optimize(self):
        self.removeJumpsToSuccessor()

    def finishBuilding(self):
        if self.isFinished:
            return

        self.textSectionOffset, self.textSectionSize = self.module.textSection.appendData(self.encodeInstructions())
        self.isFinished = True

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (str(self.name), self.index)
        return '@%d' % self.index

    def prettyPrint(self):
        self.enumerateInstructions()
        result = '%s:\n' % str(self)
        for instruction in self.allInstructions():
            result += '    %s\n' % instruction.prettyPrint()
        return result
    
    def allInstructions(self):
        for instruction in self.argumentInstructions:
            yield instruction
        for instruction in self.captureInstructions:
            yield instruction
        for instruction in self.constants:
            yield instruction
        for instruction in self.instructions:
            yield instruction

    def enumerateOnlyInstructions(self):
        index = 0
        for instruction in self.instructions:
            instruction.index = index
            index += 1

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
    
    def encode(self):
        return struct.pack('<IIIIII',
            self.textSectionOffset, self.textSectionSize,
            self.name.offset, self.name.size,
            self.typeDescriptor.offset, self.typeDescriptor.size)

class SDVMImportedModule:
    def __init__(self, module: SDVMModule, name: str) -> None:
        self.index = 0
        self.module = module
        self.name = module.addString(name)
        self.importedValues = []
        self.importedValueDict = dict()

    def importValue(self, name: str, typeDescriptor: str):
        key = (name, typeDescriptor)
        if key in self.importedValueDict:
            return self.importedValueDict[key]
        
        importedValue = self.module.importModuleValueTable.importModuleValue(self, name, typeDescriptor)
        self.importedValueDict[key] = importedValue
        return importedValue
    
    def encode(self) -> bytes:
        return struct.pack('<II', self.name.offset, self.name.size)
    
    def __str__(self) -> str:
        return str(self.name)

class SDVMImportedModuleValue:
    def __init__(self, module: SDVMModule, importedModule: SDVMImportedModule, name: str, typeDescriptor: str) -> None:
        self.index = 0
        self.importedModule = importedModule
        self.name = module.addString(name)
        self.typeDescriptor = module.addString(typeDescriptor)

    def encode(self) -> bytes:
        return struct.pack('<IIIIII', self.importedModule.index, 0, self.name.offset, self.name.size, self.typeDescriptor.offset, self.typeDescriptor.size)

    def __str__(self) -> str:
        typeDesc = str(self.typeDescriptor)
        if len(typeDesc) == 0:
            return '[%s]"%s"' % (str(self.importedModule), str(self.name))
        return '[%s : %s]"%s"' % (str(self.importedModule), typeDesc, str(self.name))

class SDVMImportedExternalValue:
    def __init__(self, module: SDVMModule, externalName: str, name: str, typeDescriptor: str) -> None:
        self.index = 0
        self.externalIndex = SdvmModuleExternalTypeMap[externalName]
        self.externalName = externalName
        self.name = module.addString(name)
        self.typeDescriptor = module.addString(typeDescriptor)

    def encode(self) -> bytes:
        return struct.pack('<IIIIII', 0, self.externalIndex, self.name.offset, self.name.size, self.typeDescriptor.offset, self.typeDescriptor.size)

    def __str__(self) -> str:
        typeDesc = str(self.typeDescriptor)
        if len(typeDesc) == 0:
            return '[external %s]"%s"' % (self.externalName, str(self.name))
        return '[external %s : %s]"%s"' % (self.externalName, typeDesc, str(self.name))
