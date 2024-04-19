from .hir import *
from .memoryDescriptor import *
from .sdvmInstructions import *
from abc import ABC, abstractmethod

class MIRContext:
    def __init__(self, pointerSize: int = 8) -> None:
        self.pointerSize = pointerSize
        self.pointerAlignment = pointerSize
        self.gcPointerSize = pointerSize*2
        self.gcPointerAlignment = pointerSize
        self.closureType = MIRClosureType(self, 'Closure', self.gcPointerSize, self.gcPointerAlignment)
        self.functionType = MIRFunctionType(self, 'Function', self.pointerSize, self.pointerAlignment)
        self.cdeclFunctionType = MIRFunctionType(self, 'CdeclFunction', self.pointerSize, self.pointerAlignment, 'cdecl')
        self.stdcallFunctionType = MIRFunctionType(self, 'StdcallFunction', self.pointerSize, self.pointerAlignment, 'stdcall')
        self.apicallFunctionType = MIRFunctionType(self, 'ApicallFunction', self.pointerSize, self.pointerAlignment, 'apicall')
        self.thiscallFunctionType = MIRFunctionType(self, 'ThiscallFunction', self.pointerSize, self.pointerAlignment, 'thiscall')
        self.vectorcallFunctionType = MIRFunctionType(self, 'VectorcallFunction', self.pointerSize, self.pointerAlignment, 'vectorcall')
        self.basicBlockType = MIRBasicBlockType(self, 'BasicBlock', self.pointerSize, self.pointerAlignment)
        self.gcPointerType = MIRGCPointerType(self, 'GCPointer', self.gcPointerSize, self.gcPointerAlignment)
        self.pointerType = MIRPointerType(self, 'Pointer', self.pointerSize, self.pointerAlignment)
        self.voidType = MIRAbortType(self, 'Void', 0, 1)
        self.void = MIRConstantVoid(self, self.voidType)
        self.booleanType = MIRBooleanType(self, 'Boolean', 1, 1)
        self.int8Type   = MIRSignedIntegerType(self, 'Int8', 1, 1)
        self.int16Type  = MIRSignedIntegerType(self, 'Int16', 2, 2)
        self.int32Type  = MIRSignedIntegerType(self, 'Int32', 4, 4)
        self.int64Type  = MIRSignedIntegerType(self, 'Int64', 8, 8)
        self.uint8Type  = MIRUnsignedIntegerType(self, 'UInt8', 1, 1)
        self.uint16Type = MIRUnsignedIntegerType(self, 'UInt16', 2, 2)
        self.uint32Type = MIRUnsignedIntegerType(self, 'UInt32', 4, 4)
        self.uint64Type = MIRUnsignedIntegerType(self, 'UInt64', 8, 8)
        self.float32Type = MIRFloatingPointType(self, 'Float32', 4, 4)
        self.float64Type = MIRFloatingPointType(self, 'Float64', 8, 8)

        self.float32x2Type = MIRPrimitiveVectorType(self, 'Float32x2', self.float32Type, 2, 8)
        self.float32x3Type = MIRPrimitiveVectorType(self, 'Float32x3', self.float32Type, 3, 16)
        self.float32x4Type = MIRPrimitiveVectorType(self, 'Float32x4', self.float32Type, 4, 16)
        self.float64x2Type = MIRPrimitiveVectorType(self, 'Float64x2', self.float64Type, 2, 16)
        self.float64x3Type = MIRPrimitiveVectorType(self, 'Float64x3', self.float64Type, 3, 32)
        self.float64x4Type = MIRPrimitiveVectorType(self, 'Float64x4', self.float64Type, 4, 32)

        self.int32x2Type = MIRPrimitiveVectorType(self, 'Int32x2', self.int32Type, 2, 8)
        self.int32x3Type = MIRPrimitiveVectorType(self, 'Int32x3', self.int32Type, 3, 16)
        self.int32x4Type = MIRPrimitiveVectorType(self, 'Int32x4', self.int32Type, 4, 16)
        self.uint32x2Type = MIRPrimitiveVectorType(self, 'UInt32x2', self.uint32Type, 2, 8)
        self.uint32x3Type = MIRPrimitiveVectorType(self, 'UInt32x3', self.uint32Type, 3, 16)
        self.uint32x4Type = MIRPrimitiveVectorType(self, 'UInt32x4', self.uint32Type, 4, 16)

        self.primitiveMulTable = {
            self.int8Type   : SdvmInstInt8Mul,
            self.int16Type  : SdvmInstInt16Mul,
            self.int32Type  : SdvmInstInt32Mul,
            self.int64Type  : SdvmInstInt64Mul,
            self.uint8Type  : SdvmInstUInt8Mul,
            self.uint16Type : SdvmInstUInt16Mul,
            self.uint32Type : SdvmInstUInt32Mul,
            self.uint64Type : SdvmInstUInt64Mul,
        }

        self.pointerAddOffsetTable = {
            (self.pointerType, self.int32Type)  : SdvmInstPointerAddOffsetInt32,
            (self.pointerType, self.int64Type)  : SdvmInstPointerAddOffsetInt64,
            (self.pointerType, self.uint32Type) : SdvmInstPointerAddOffsetUInt32,
            (self.pointerType, self.uint64Type) : SdvmInstPointerAddOffsetUInt64,
            (self.gcPointerType, self.int32Type)  : SdvmInstGCPointerAddOffsetInt32,
            (self.gcPointerType, self.int64Type)  : SdvmInstGCPointerAddOffsetInt64,
            (self.gcPointerType, self.uint32Type) : SdvmInstGCPointerAddOffsetUInt32,
            (self.gcPointerType, self.uint64Type) : SdvmInstGCPointerAddOffsetUInt64,
        }

        self.callingConventionFunctionTypeMap = {
            'cdecl': self.cdeclFunctionType,
            'stdcall': self.stdcallFunctionType,
            'apicall': self.apicallFunctionType,
            'thiscall': self.thiscallFunctionType,
            'vectorcall': self.vectorcallFunctionType,
        }

class MIRType(ABC):
    def __init__(self, context: MIRContext, name: str, size: int, alignment: int) -> None:
        self.context = context
        self.name = name
        self.size = size
        self.alignment = alignment

    def isGCPointerType(self) -> bool:
        return False

    def isAbortType(self) -> bool:
        return False
    
    def isClosureType(self) -> bool:
        return False
    
    def isFunctionType(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.name

class MIRAbortType(MIRType):
    def isAbortType(self) -> bool:
        return True

class MIRBooleanType(MIRType):
    pass

class MIRUnsignedIntegerType(MIRType):
    pass

class MIRSignedIntegerType(MIRType):
    pass

class MIRFloatingPointType(MIRType):
    pass

class MIRPrimitiveVectorType(MIRType):
    def __init__(self, context: MIRContext, name: str, elementType: MIRType, elements: int, alignment: int) -> None:
        super().__init__(context, name, elementType.size*elements, alignment)
        self.elements = elements
        self.alignment = alignment

class MIRGCPointerType(MIRType):
    def isGCPointerType(self) -> bool:
        return True

class MIRClosureType(MIRType):
    def isClosureType(self) -> bool:
        return True

class MIRFunctionType(MIRType):
    def __init__(self, context: MIRContext, name: str, size: int, alignment: int, callingConvention: str | None = None) -> None:
        super().__init__(context, name, size, alignment)
        self.callingConvention = callingConvention

    def isFunctionType(self) -> bool:
        return True

class MIRBasicBlockType(MIRType):
    pass

class MIRPointerType(MIRType):
    pass

class MIRValueVisitor(ABC):
    @abstractmethod
    def visitImportedModule(self, value):
        pass

    @abstractmethod
    def visitImportedModuleValue(self, value):
        pass

    @abstractmethod
    def visitConstantInteger(self, value):
        pass

    @abstractmethod
    def visitConstantFloat(self, value):
        pass

    @abstractmethod
    def visitGlobalVariable(self, value):
        pass

    @abstractmethod
    def visitFunction(self, value):
        pass

    @abstractmethod
    def visitCallInstruction(self, value):
        pass

    @abstractmethod
    def visitReturnInstruction(self, value):
        pass

class MIRValue(ABC):
    def __init__(self, context: MIRContext, sourcePosition: SourcePosition = None) -> None:
        self.context = context
        self.sourcePosition = sourcePosition

    @abstractmethod
    def getType(self) -> MIRType:
        pass

    def isConstant(self) -> bool:
        return False

    def isFunctionLocalValue(self) -> bool:
        return False

    def isInstruction(self) -> bool:
        return False
    
    def isGCPointer(self) -> bool:
        return self.getType().isGCPointerType()

    def hasAbortType(self) -> bool:
        return self.getType().isAbortType()

    def hasNotAbortType(self) -> bool:
        return not self.getType().isAbortType()

class MIRConstant(MIRValue):
    def isConstant(self) -> bool:
        return True

class MIRConstantValue(MIRConstant):
    def __init__(self, context: MIRContext, type: MIRType) -> None:
        super().__init__(context)
        self.type = type

    def getType(self):
        return self.type

class MIRConstantVoid(MIRConstantValue):
    pass

class MIRConstantStringData(MIRConstantValue):
    def __init__(self, type: MIRType, value: bytes, nullTerminated: bool = True) -> None:
        super().__init__(type.context, type)
        self.value = value
        self.nullTerminated = nullTerminated

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitConstantStringData(self)

    def __str__(self) -> str:
        if self.nullTerminated:
            return '%s cstring(%s)' % (str(self.type), repr(self.value))
        return '%s string(%s)' % (str(self.type), repr(self.value))

class MIRConstantInteger(MIRConstantValue):
    def __init__(self, type: MIRType, value: int) -> None:
        super().__init__(type.context, type)
        self.value = value

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitConstantInteger(self)

    def __str__(self) -> str:
        return '%s(%d)' % (str(self.type), self.value)

class MIRConstantFloat(MIRConstantValue):
    def __init__(self, type: MIRType, value: float) -> None:
        super().__init__(type.context, type)
        self.value = value

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitConstantFloat(self)

    def __str__(self) -> str:
        return '%s(%f)' % (str(self.type), self.value)

class MIRGlobalValue(MIRConstant):
    def __init__(self, context: MIRContext, name: str = None) -> None:
        super().__init__(context)
        self.name = name
        self.globalValueIndex = 0

    def getType(self) -> MIRType:
        return self.context.pointerType

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (self.name, self.globalValueIndex)
        return '@%d' % self.globalValueIndex
    
    def fullPrintString(self) -> str:
        return str(self)

class MIRImportedModule(MIRGlobalValue):
    def __init__(self, context: MIRContext, parentModule, moduleName: str = None) -> None:
        super().__init__(context, moduleName)
        self.parentModule = parentModule
        self.moduleName = moduleName
        self.importedValues: list[MIRImportedModuleValue] = []

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitImportedModule(self)
    
    def importValueWithType(self, name: str, type: MIRType):
        for importedValue in self.importedValues:
            if importedValue.valueName == name and importedValue.type == type:
                return importedValue

        importedValue = MIRImportedModuleValue(self.context, self, type, name)
        self.parentModule.addGlobalValue(importedValue)
        return importedValue

class MIRImportedValue(MIRGlobalValue):
    def __init__(self, context: MIRContext, valueType: MIRType, valueName: str = None) -> None:
        super().__init__(context, valueName)
        self.valueName = valueName
        self.valueType = valueType
        self.type = self.context.pointerType
        if self.valueType.isFunctionType():
            self.type = self.valueType
    def getType(self) -> MIRType:
        return self.type

class MIRImportedModuleValue(MIRImportedValue):
    def __init__(self, context: MIRContext, importedModule: MIRImportedModule, valueType: MIRType, valueName: str = None) -> None:
        super().__init__(context, valueType, valueName)
        self.importedModule = importedModule

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitImportedModuleValue(self)

class MIRImportedExternalValue(MIRImportedValue):
    def __init__(self, context: MIRContext, externalName: str, valueType: MIRType, valueName: str = None) -> None:
        super().__init__(context, valueType, valueName)
        self.externalName = externalName

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitImportedExternalValue(self)

class MIRGlobalVariable(MIRGlobalValue):
    def __init__(self, context: MIRContext, name: str = None) -> None:
        super().__init__(context, name)
        self.alignment = 1
        self.size = 0
        self.blob = bytearray()
        self.blobRelocations = []

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitGlobalVariable(self)

    def getType(self) -> MIRType:
        return self.context.pointerType
    
    def fullPrintString(self) -> str:
        result = str(self)
        result += ' := global size %d alignment %d' % (self.size, self.alignment)
        return result

class MIRGlobalVariableWriter:
    def __init__(self, globalVariable: MIRGlobalVariable) -> None:
        self.context = globalVariable.context
        self.globalVariable = globalVariable
        self.alignment = self.globalVariable.alignment
        self.size = self.globalVariable.size
        self.blob = bytearray()
        self.blobRelocations = []

    def writeFunctionHandle(self, value: MIRValue):
        assert value.getType() is self.context.functionType

    def finish(self) -> MIRGlobalVariable:
        self.globalVariable.size += self.size
        self.globalVariable.alignment = max(self.globalVariable.alignment, self.alignment)
        self.globalVariable.blob += self.blob
        self.globalVariable.blobRelocations += self.blobRelocations
        return self.globalVariable

class MIRFunction(MIRGlobalValue):
    def __init__(self, context: MIRContext, name: str = None) -> None:
        super().__init__(context, name)
        self.arguments = []
        self.captures = []
        self.firstBasicBlock: MIRBasicBlock = None
        self.lastBasicBlock: MIRBasicBlock = None

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitFunction(self)

    def getType(self) -> MIRType:
        return self.context.functionType

    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBasicBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBasicBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def basicBlocks(self):
        position = self.firstBasicBlock
        while position is not None:
            yield position
            position = position.nextBasicBlock

    def basicBlocksInReversePostOrder(self):
        visitedSet = set()
        visitedList = []

        def visit(basicBlock: HIRBasicBlock):
            if basicBlock in visitedSet:
                return
            
            visitedSet.add(basicBlock)
            for successor in reversed(basicBlock.successorBlocks()):
                visit(successor)
            visitedList.append(basicBlock)

        for basicBlock in self.basicBlocks():
            visit(basicBlock)

        return list(reversed(visitedList))
    
    def reachableBasicBlocksInReversePostOrder(self):
        visitedSet = set()
        visitedList = []

        def visit(basicBlock: HIRBasicBlock):
            if basicBlock in visitedSet:
                return
            
            visitedSet.add(basicBlock)
            for successor in reversed(basicBlock.successorBlocks()):
                visit(successor)
            visitedList.append(basicBlock)

        if self.firstBasicBlock is not None:
            visit(self.firstBasicBlock)

        return list(reversed(visitedList))
    
    def allLocalValues(self):
        for argument in self.arguments:
            yield argument

        for capture in self.captures:
            yield capture

        for basicBlock in self.basicBlocks():
            yield basicBlock
            for instruction in basicBlock.instructions():
                yield instruction

    def enumerateLocalValues(self):
        index = 0
        for localValue in self.allLocalValues():
            localValue.localValueIndex = index
            index += 1

    def fullPrintString(self) -> str:
        self.enumerateLocalValues()
        result = str(self)
        result += ':= function ('
        isFirst = True
        for argument in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += argument.fullPrintString()
        result +=') captures ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += capture.fullPrintString()
        result += ']\n'
        result += '{\n'
        for basicBlock in self.basicBlocks():
            result += basicBlock.fullPrintString()
        result += '}\n'
        return result

class MIRFunctionLocalValue(MIRValue):
    def __init__(self, context: MIRContext, type: MIRType, name: str = None, sourcePosition: SourcePosition = None) -> None:
        super().__init__(context, sourcePosition)
        self.name = name
        self.type = type
        self.localValueIndex = 0

    def isFunctionLocalValue(self) -> bool:
        return True

    def getType(self) -> MIRType:
        return self.type
    
    def __str__(self) -> str:
        if self.name is not None:
            return '$%s|%d' % (self.name, self.localValueIndex)
        return '$%d' % self.localValueIndex

class MIRArgument(MIRFunctionLocalValue):
    def fullPrintString(self):
        return '%s %s' % (str(self.type), str(self))

class MIRCapture(MIRFunctionLocalValue):
    def fullPrintString(self):
        return '%s %s' % (str(self.type), str(self))

class MIRBasicBlock(MIRFunctionLocalValue):
    def __init__(self, context: MIRContext, name: str = None, sourcePosition: SourcePosition = None) -> None:
        super().__init__(context, context.basicBlockType, name, sourcePosition)
        self.previousBasicBlock: MIRBasicBlock = None
        self.nextBasicBlock: MIRBasicBlock = None
        self.firstInstruction: MIRInstruction = None
        self.lastInstruction: MIRInstruction = None

    def addInstruction(self, instruction):
        if self.lastInstruction is None:
            self.firstInstruction = self.lastInstruction = instruction
        else:
            instruction.previousInstruction = self.lastInstruction
            self.lastInstruction.nextInstruction = instruction
            self.lastInstruction = instruction

    def instructions(self):
        position = self.firstInstruction
        while position is not None:
            yield position
            position = position.nextInstruction

    def successorBlocks(self):
        if self.lastInstruction is None:
            return []
        return self.lastInstruction.successorBlocks()
    
    def fullPrintString(self) -> str:
        result = str(self)
        result += ':\n'
        for instruction in self.instructions():
            result += '    '
            result += instruction.fullPrintString()
            result += '\n'
        return result
    
class MIRInstruction(MIRFunctionLocalValue):
    def __init__(self, context: MIRContext, type: MIRType, name: str = None) -> None:
        super().__init__(context, type, name)
        self.previousInstruction: MIRInstruction = None
        self.nextInstruction: MIRInstruction = None

    def isInstruction(self) -> bool:
        return True
    
    def successorBlocks(self) -> list[MIRBasicBlock]:
        return []

class MIRAllocaInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRValue, memoryDescriptor: MemoryDescriptor, name: str = None) -> None:
        super().__init__(context, type, name)
        self.memoryDescriptor = memoryDescriptor
        self.hasNoEscape = False

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitAllocaInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := alloca %s' % (str(self), str(self.memoryDescriptor))
    
class MIRLoadInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRValue, pointer: MIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.pointer = pointer
        self.isVolatile = False

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitLoadInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := load %s' % (str(self), str(self.pointer))

class MIRStoreInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, pointer: MIRValue, value: MIRValue, name: str = None) -> None:
        super().__init__(context, context.voidType, name)
        self.pointer = pointer
        self.value = value
        self.isVolatile = False

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitStoreInstruction(self)

    def fullPrintString(self) -> str:
        return 'store %s value %s' % (str(self.pointer), str(self.value))

class MIRCallInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRValue, functional: MIRValue, arguments: list[MIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.functional = functional
        self.arguments = arguments

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitCallInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s := call %s (' % (str(self.type), str(self.functional))
        isFirst = True
        for arg in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result

class MIRNullaryPrimitiveInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRType, instructionDef: SdvmInstructionDef, name: str = None) -> None:
        super().__init__(context, type, name)
        self.instructionDef = instructionDef

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitNullaryPrimitiveInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := %s()' % (str(self), self.instructionDef.name)

class MIRUnaryPrimitiveInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRType, instructionDef: SdvmInstructionDef, operand: MIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.instructionDef = instructionDef
        self.operand = operand

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitUnaryPrimitiveInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := %s(%s)' % (str(self), self.instructionDef.name, str(self.operand))

class MIRBinaryPrimitiveInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRType, instructionDef: SdvmInstructionDef, left: MIRValue, right: MIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.instructionDef = instructionDef
        self.left = left
        self.right = right

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitBinaryPrimitiveInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := %s(%s, %s)' % (str(self), self.instructionDef.name, str(self.left), str(self.right))
    
class MIRTerminatorInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, name: str = None) -> None:
        super().__init__(context, context.voidType, name)
    
    def isTerminatorInstruction(self) -> bool:
        return True

class MIRBranchInstruction(MIRTerminatorInstruction):
    def __init__(self, context: MIRContext, destination: MIRBasicBlock) -> None:
        super().__init__(context)
        self.destination = destination

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitBranchInstruction(self)

    def successorBlocks(self) -> list[MIRBasicBlock]:
        return [self.destination]

    def fullPrintString(self) -> str:
        return 'branch %s' % str(self.destination)

class MIRCondBranchInstruction(MIRTerminatorInstruction):
    def __init__(self, context: MIRContext, condition: MIRValue, trueDestination: MIRBasicBlock, falseDestination: MIRBasicBlock) -> None:
        super().__init__(context)
        self.condition = condition
        self.trueDestination = trueDestination
        self.falseDestination = falseDestination

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitCondBranchInstruction(self)

    def successorBlocks(self) -> list[MIRBasicBlock]:
        return [self.trueDestination, self.falseDestination]

    def fullPrintString(self) -> str:
        return 'condBranch: %s ifTrue: %s ifFalse: %s' % (str(self.condition), str(self.trueDestination), str(self.falseDestination))
    
class MIRReturnInstruction(MIRTerminatorInstruction):
    def __init__(self, context: MIRContext, result: MIRValue) -> None:
        super().__init__(context)
        self.result = result

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitReturnInstruction(self)

    def fullPrintString(self) -> str:
        return 'return %s' % str(self.result)

class MIRBuilder:
    def __init__(self, context: MIRContext, function: MIRFunction) -> None:
        self.context = context
        self.function = function
        self.sourcePosition: SourcePosition = None
        self.basicBlock = None

    def withSourcePositionDo(self, sourcePosition: SourcePosition, aBlock):
        oldSourcePosition = self.sourcePosition
        self.sourcePosition = sourcePosition
        try:
            return aBlock()
        finally:
            self.sourcePosition = oldSourcePosition

    def newBasicBlock(self, name: str):
        return MIRBasicBlock(self.context, name, self.sourcePosition)

    def beginBasicBlock(self, basicBlock: HIRBasicBlock) -> HIRBasicBlock:
        self.function.addBasicBlock(basicBlock)
        self.basicBlock = basicBlock
        return basicBlock

    def beginNewBasicBlock(self, name: str) -> HIRBasicBlock:
        return self.beginBasicBlock(self.newBasicBlock(name))
    
    def isLastTerminator(self) -> bool:
        return self.basicBlock is not None and self.basicBlock.lastInstruction is not None and self.basicBlock.lastInstruction.isTerminatorInstruction()
    
    def addInstruction(self, instruction: MIRInstruction) -> HIRValue:
        instruction.sourcePosition = self.sourcePosition
        self.basicBlock.addInstruction(instruction)
        return instruction

    def branch(self, destination: MIRBasicBlock) -> MIRInstruction:
        return self.addInstruction(MIRBranchInstruction(self.context, destination))

    def call(self, resultType: MIRType, function: MIRValue, arguments: list[HIRValue]) -> MIRInstruction:
        return self.addInstruction(MIRCallInstruction(self.context, resultType, function, arguments))

    def condBranch(self, condition: MIRBasicBlock, trueDestination: MIRBasicBlock, falseDestination: MIRBasicBlock) -> MIRInstruction:
        return self.addInstruction(MIRCondBranchInstruction(self.context, condition, trueDestination, falseDestination))

    def returnValue(self, value: MIRValue) -> MIRInstruction:
        return self.addInstruction(MIRReturnInstruction(self.context, value))

    def alloca(self, type: MIRType, memoryDescriptor: MemoryDescriptor) -> MIRLoadInstruction:
        return self.addInstruction(MIRAllocaInstruction(self.context, type, memoryDescriptor))

    def load(self, type: MIRType, pointer: MIRValue) -> MIRLoadInstruction:
        return self.addInstruction(MIRLoadInstruction(self.context, type, pointer))

    def store(self, pointer: MIRValue, value: MIRValue) -> MIRLoadInstruction:
        return self.addInstruction(MIRStoreInstruction(self.context, pointer, value))

    def pointerAddOffset(self, pointerType: MIRType, pointer: MIRValue, offset: MIRValue):
        return self.addInstruction(MIRBinaryPrimitiveInstruction(self.context, pointerType, self.context.pointerAddOffsetTable[pointerType, offset.getType()], pointer, offset))

    def mulPrimitiveInteger(self, a: MIRValue, b: MIRValue):
        assert a.getType() == b.getType()
        return self.addInstruction(MIRBinaryPrimitiveInstruction(self.context, a.getType(), self.context.primitiveMulTable[a.getType()], a, b))

    def offsetConstant(self, offset: int):
        return MIRConstantInteger(self.context.intPointerType, offset)

    def scalePointerIndex(self, index: MIRValue, stride: int):
        strideConstant = MIRConstantInteger(index.getType(), stride)
        return self.mulPrimitiveInteger(index, strideConstant)

    def pointerAddScaledIndex(self, pointerType: MIRType, pointer: MIRValue, index: MIRValue, stride: int):
        if stride == 0:
            return pointer
        return self.pointerAddOffset(pointerType, pointer, self.scalePointerIndex(index, stride))

    def pointerAddConstantOffset(self, pointerType: MIRType, pointer: MIRValue, offset: int):
        return self.pointerAddOffset(pointerType, pointer, self.offsetConstant(offset))

class MIRModule:
    def __init__(self, context: MIRContext) -> None:
        self.context = context
        self.importedModules: list[MIRImportedModule] = []
        self.importedModuleDictionary: dict[str, MIRImportedModule] = dict()
        self.globalValues: list[MIRGlobalValue] = []
        self.exportedValues: list[tuple[str, MIRConstant]] = []
        self.entryPoint: MIRFunction = None
        self.entryPointClosure: MIRGlobalVariable = None
        self.name = ''

    def exportValue(self, name: str, value: MIRConstant, externalName: str | None = None) -> None:
        self.exportedValues.append((name, value, externalName))

    def importModule(self, name: str) -> MIRImportedModule:
        if name in self.importedModuleDictionary:
            return self.importedModuleDictionary[name]

        importedModule = MIRImportedModule(self.context, self, name)
        self.importedModules.append(importedModule)
        self.importedModuleDictionary[name] = importedModule
        return importedModule

    def addGlobalValue(self, globalValue) -> None:
        self.globalValues.append(globalValue)

    def allGlobalValues(self):
        for value in self.importedModules:
            yield value
        for value in self.globalValues:
            yield value

    def enumerateGlobalValues(self):
        index = 0
        for globalValue in self.allGlobalValues():
            globalValue.globalValueIndex = index
            index += 1

    def prettyPrint(self) -> str:
        self.enumerateGlobalValues()
        result = ''
        for name, value, externalName in self.exportedValues:
            if externalName is not None:
                result += 'export "%s" external %s := %s' % (name, externalName, value)
            else:
                result += 'export "%s" := %s' % (name, value)
        if self.entryPoint is not None:
            result += 'entryPoint: %s\n' % (self.entryPoint)
        if self.entryPointClosure is not None:
            result += 'entryPointClosure: %s\n' % (self.entryPointClosure)

        if len(result) != 0:
            result += '\n'

        for function in self.allGlobalValues():
            result += function.fullPrintString()
            result += '\n'
        return result

class MIRModuleFrontend:
    def __init__(self) -> None:
        self.context = MIRContext()
        self.module = MIRModule(self.context)
        self.translatedValueDictionary = dict()
        self.translatedTypeDictionary = dict()

    def compileHIRModule(self, hirModule: HIRModule):
        mirContext = self.context
        hirContext = hirModule.context
        self.module.name = hirModule.name

        for hirType, mirType in [
            (hirContext.voidType,  mirContext.voidType),
            (hirContext.booleanType,  mirContext.booleanType),
            (hirContext.int8Type,  mirContext.int8Type),
            (hirContext.int16Type, mirContext.int16Type),
            (hirContext.int32Type, mirContext.int32Type),
            (hirContext.int64Type, mirContext.int64Type),
            (hirContext.uint8Type,  mirContext.uint8Type),
            (hirContext.uint16Type, mirContext.uint16Type),
            (hirContext.uint32Type, mirContext.uint32Type),
            (hirContext.uint64Type, mirContext.uint64Type),
            (hirContext.float32Type, mirContext.float32Type),
            (hirContext.float64Type, mirContext.float64Type),
            (hirContext.float32x2Type, mirContext.float32x2Type),
            (hirContext.float32x3Type, mirContext.float32x3Type),
            (hirContext.float32x4Type, mirContext.float32x4Type),
            (hirContext.float64x2Type, mirContext.float64x2Type),
            (hirContext.float64x3Type, mirContext.float64x3Type),
            (hirContext.float64x4Type, mirContext.float64x4Type),
            (hirContext.int32x2Type, mirContext.int32x2Type),
            (hirContext.int32x3Type, mirContext.int32x3Type),
            (hirContext.int32x4Type, mirContext.int32x4Type),
            (hirContext.uint32x2Type, mirContext.uint32x2Type),
            (hirContext.uint32x3Type, mirContext.uint32x3Type),
            (hirContext.uint32x4Type, mirContext.uint32x4Type),
            (hirContext.basicBlockType, mirContext.basicBlockType),
            (hirContext.functionalDefinitionType, mirContext.functionType),
        ]:
            self.translatedTypeDictionary[hirType] = mirType

        for globalValue in hirModule.globalValues:
            self.translateValue(globalValue)

        for name, value, externalName in hirModule.exportedValues:
            self.module.exportValue(name, self.translateValue(value), externalName)

        if hirModule.entryPoint is not None:
            assert hirModule.entryPoint.isConstantLambda()
            entryPointLambda: HIRConstantLambda = hirModule.entryPoint
            self.module.entryPoint = self.translateValue(entryPointLambda.definition)
            self.module.entryPointClosure = self.translateValue(entryPointLambda)

        return self.module
    
    def translateValue(self, value: HIRValue) -> MIRValue:
        if value in self.translatedValueDictionary:
            return self.translatedValueDictionary[value]
        
        translatedValue = value.accept(self)
        self.translatedValueDictionary[value] = translatedValue
        return translatedValue

    def translateType(self, type: HIRValue):
        if type in self.translatedTypeDictionary:
            return self.translatedTypeDictionary[type]
        translatedType = type.accept(self)
        self.translatedTypeDictionary[type] = translatedType
        return translatedType

    def visitArrayType(self, type: HIRArrayType):
        return self.context.pointerType

    def visitPointerLikeType(self, type: HIRPointerLikeType):
        return self.context.pointerType

    def visitPointerType(self, type: HIRPointerType):
        return self.visitPointerLikeType(type)

    def visitReferenceType(self, type: HIRPointerType):
        return self.visitPointerLikeType(type)

    def visitTemporaryReferenceType(self, type: HIRPointerType):
        return self.visitPointerLikeType(type)

    def visitFunctionType(self, type: HIRFunctionType):
        if type.callingConvention is not None:
            return self.context.callingConventionFunctionTypeMap[type.callingConvention]
        return self.context.closureType
    
    def visitSumType(self, type: HIRSumType):
        if type.isStateless():
            return type.discriminantType
        assert False
    
    def visitConstantUnit(self, constant: HIRConstantUnit) -> MIRValue:
        return self.context.void
    
    def visitConstantStringData(self, constant: HIRConstantStringData) -> MIRValue:
        return MIRConstantStringData(self.translateType(constant.getType()), constant.value, constant.nullTerminated)

    def visitConstantPrimitiveInteger(self, constant: HIRConstantPrimitiveInteger) -> MIRValue:
        return MIRConstantInteger(self.translateType(constant.getType()), constant.value)

    def visitFunctionalDefinitionValue(self, functional: HIRFunctionalDefinition) -> MIRValue:
        mirFunction = MIRFunction(self.context, functional.name)
        mirFunction.sourcePosition = functional.sourcePosition
        self.translatedValueDictionary[functional] = mirFunction
        self.module.addGlobalValue(mirFunction)
        MIRFunctionFrontend(self).translateFunctionDefinitionInto(functional, mirFunction)
        return mirFunction

    def visitConstantLambda(self, value: HIRConstantLambda) -> MIRValue:
        ## If the calling convention is not None, translate the as the function itself.
        ## This is used for exporting functions into the C world.
        if value.type.callingConvention is not None:
            assert len(value.captures) == 0
            return self.translateValue(value.definition)

        writer = self.beginWritingGlobalVariableFor(value)
        writer.writeFunctionHandle(self.translateValue(value.definition))
        ## FIXME: Write the capture values.
        assert len(value.captures) == 0
        return writer.finish()

    def visitImportedModule(self, value: HIRImportedModule) -> MIRValue:
        return self.module.importModule(value.name)

    def visitImportedModuleValue(self, value: HIRImportedModuleValue) -> MIRValue:
        module = self.translateValue(value.module)
        return module.importValueWithType(value.name, self.translateType(value.type))

    def visitImportedExternalValue(self, value: HIRImportedExternalValue) -> MIRValue:
        importedValue = MIRImportedExternalValue(self.context, value.externalName, self.translateType(value.type), value.valueName)
        self.module.addGlobalValue(importedValue)
        return importedValue

    def beginWritingGlobalVariableFor(self, targetValue: HIRValue) -> MIRValue:
        mirGlobal = MIRGlobalVariable(self.context)
        self.module.addGlobalValue(mirGlobal)
        self.translatedValueDictionary[targetValue] = mirGlobal
        return MIRGlobalVariableWriter(mirGlobal)


def sdvmNullaryPrimitiveFor(sdvmInstructionDef: SdvmInstructionDef):
    def translator(self: MIRFunctionFrontend, hirInstruction: HIRCallInstruction, resultType: MIRType, arguments: list[MIRValue]):
        assert len(arguments) == 0
        return self.builder.addInstruction(MIRNullaryPrimitiveInstruction(self.context, resultType, sdvmInstructionDef))
    return translator

def sdvmUnaryPrimitiveFor(sdvmInstructionDef: SdvmInstructionDef):
    def translator(self: MIRFunctionFrontend, hirInstruction: HIRCallInstruction, resultType: MIRType, arguments: list[MIRValue]):
        assert len(arguments) == 1
        return self.builder.addInstruction(MIRUnaryPrimitiveInstruction(self.context, resultType, sdvmInstructionDef, arguments[0]))
    return translator

def sdvmBinaryPrimitiveFor(sdvmInstructionDef: SdvmInstructionDef):
    def translator(self: MIRFunctionFrontend, hirInstruction: HIRCallInstruction, resultType: MIRType, arguments: list[MIRValue]):
        assert len(arguments) == 2
        return self.builder.addInstruction(MIRBinaryPrimitiveInstruction(self.context, resultType, sdvmInstructionDef, arguments[0], arguments[1]))
    return translator

def yourselfTranslator(self, hirInstruction: HIRCallInstruction, resultType: MIRType, arguments: list[MIRValue]):
    return arguments[0]

def pointerSizeTranslatorFor(pointer32Translator, pointer64Translator):
    def translator(self: MIRFunctionFrontend, *args):
        if self.context.pointerSize == 4:
            return pointer32Translator(self, *args)
        elif self.context.pointerSize == 8:
            return pointer64Translator(self, *args)
        assert False
    return translator

PrimitiveFunctionTranslators = {}

class MIRFunctionFrontend:
    def __init__(self, moduleFrontend: MIRModuleFrontend) -> None:
        self.moduleFrontend = moduleFrontend
        self.context = moduleFrontend.context
        self.function: MIRFunction = None
        self.builder: MIRBuilder = None
        self.translatedValueDictionary = dict()

    def translateFunctionDefinitionInto(self, hirDefinition: HIRFunctionalDefinition, function: MIRFunction):
        self.function = function
        self.builder = MIRBuilder(self.context, function)

        for argument in hirDefinition.arguments:
            self.translateArgument(argument)

        for capture in hirDefinition.captures:
            self.translateCapture(capture)

        self.translateBasicBlocksOf(hirDefinition)

    def translateType(self, type: HIRValue):
        return self.moduleFrontend.translateType(type)

    def translateArgument(self, hirArgument: HIRFunctionalArgumentValue):
        mirArgument = MIRArgument(self.context, self.translateType(hirArgument.getType()), hirArgument.name, hirArgument.sourcePosition)
        if mirArgument.hasAbortType():
            self.translatedValueDictionary[mirArgument] = self.context.void
            return

        self.translatedValueDictionary[hirArgument] = mirArgument
        self.function.arguments.append(mirArgument)

    def translateCapture(self, hirCapture: HIRFunctionalCaptureValue):
        mirCapture = MIRCapture(self.context, self.translateType(hirCapture.getType()), hirCapture.name, hirCapture.sourcePosition)
        if mirCapture.hasAbortType():
            self.translatedValueDictionary[hirCapture] = self.context.void
            return

        self.translatedValueDictionary[hirCapture] = mirCapture
        self.function.captures.append(mirCapture)

    def translateBasicBlocksOf(self, functional: HIRFunctionalDefinition):
        hirBasicBlocks: list[HIRBasicBlock] = functional.reachableBasicBlocksInReversePostOrder()
        for hirBasicBlock in hirBasicBlocks:
            mirBasicBlock = MIRBasicBlock(self.context, hirBasicBlock.name, hirBasicBlock.sourcePosition)
            self.translatedValueDictionary[hirBasicBlock] = mirBasicBlock

        for hirBasicBlock in hirBasicBlocks:
            mirBasicBlock: MIRBasicBlock = self.translatedValueDictionary[hirBasicBlock]
            self.builder.beginBasicBlock(mirBasicBlock)
            self.translateBasicBlock(hirBasicBlock, mirBasicBlock)

    def translateBasicBlock(self, hirBasicBlock: HIRBasicBlock, mirBasicBlock: MIRBasicBlock):
        for instruction in hirBasicBlock.instructions():
            self.translateInstruction(instruction)

    def translateInstruction(self, hirInstruction: HIRInstruction):
        assert hirInstruction not in self.translatedValueDictionary
        translatedValue = self.builder.withSourcePositionDo(hirInstruction.sourcePosition, lambda: hirInstruction.accept(self))
        self.translatedValueDictionary[hirInstruction] = translatedValue

    def translateValue(self, value: HIRValue):
        if value.isFunctionalLocalValue():
            return self.translatedValueDictionary[value]
        
        if value.isImportedValue():
            importedValue = self.moduleFrontend.translateValue(value)
            valueType = self.translateType(value.getType())
            if valueType.isFunctionType():
                return importedValue
            return self.builder.load(valueType, importedValue)

        return self.moduleFrontend.translateValue(value)
    
    def translateGetElementPointerAccesses(self, resultPointerType: MIRType, pointer: MIRValue, pointerType: HIRTypeValue, indices: list[HIRValue]):
        currentType = pointerType
        totalOffset = 0
        stridedAccesses: list[tuple[HIRValue, int]] = []
        for index in indices:
            currentType, offset, stridedAccess = currentType.computeIndexedElementAccess(index)
            totalOffset += offset
            if stridedAccess is not None:
                stridedAccesses.append(stridedAccess)

        result = pointer
        for index, stride in stridedAccesses:
            result = self.builder.pointerAddScaledIndex(resultPointerType, result, self.translateValue(index), stride)
        if totalOffset != 0:
            result = self.builder.pointerAddConstantOffset(resultPointerType, result, totalOffset)
        return result

    def visitGetElementPointerInstruction(self, hirInstruction: HIRGetElementPointerInstruction):
        pointer = self.translateValue(hirInstruction.pointer)
        resultType = self.translateType(hirInstruction.getType())
        return self.translateGetElementPointerAccesses(resultType, pointer, hirInstruction.pointer.getType(), hirInstruction.indices)

    def visitExtractValueInstruction(self, hirInstruction: HIRExtractValueInstruction):
        valueType = self.translateType(hirInstruction.getType())
        aggregate = self.translateValue(hirInstruction.aggregate)
        elementPointer = self.translateGetElementPointerAccesses(self.context.pointerType, aggregate, hirInstruction.aggregate.getType(), hirInstruction.indices)
        return self.builder.load(valueType, elementPointer)

    def visitExtractValueReferenceInstruction(self, hirInstruction: HIRExtractValueReferenceInstruction):
        aggregate = self.translateValue(hirInstruction.aggregate)
        resultType = self.translateType(hirInstruction.getType())
        return self.translateGetElementPointerAccesses(resultType, aggregate, hirInstruction.aggregate.getType(), hirInstruction.indices)

    def visitBranchInstruction(self, hirInstruction: HIRBranchInstruction):
        destination = self.translateValue(hirInstruction.destination)
        return self.builder.branch(destination)
    
    def visitAllocaInstruction(self, hirInstruction: HIRAllocaInstruction):
        pointerType = self.translateType(hirInstruction.getType())
        memoryDescriptor = hirInstruction.valueType.getMemoryDescriptor()
        return self.builder.alloca(pointerType, memoryDescriptor)

    def visitLoadInstruction(self, hirInstruction: HIRLoadInstruction):
        valueType = self.translateType(hirInstruction.getType())
        pointer = self.translateValue(hirInstruction.pointer)
        load = self.builder.load(valueType, pointer)
        load.isVolatile = hirInstruction.isVolatile
        return load

    def visitStoreInstruction(self, hirInstruction: HIRStoreInstruction):
        pointer = self.translateValue(hirInstruction.pointer)
        value = self.translateValue(hirInstruction.value)
        store = self.builder.store(pointer, value)
        store.isVolatile = hirInstruction.isVolatile
        return store

    def visitCallInstruction(self, hirInstruction: HIRCallInstruction):
        hirFunctional = hirInstruction.functional
        if hirFunctional.isConstantPrimitiveFunction():
            constantPrimitiveFunction: HIRConstantPrimitiveFunction = hirFunctional
            primitiveName = constantPrimitiveFunction.name
            if primitiveName is not None and primitiveName in PrimitiveFunctionTranslators:
                resultType = self.translateType(hirInstruction.type)
                arguments = list(map(self.translateValue, hirInstruction.arguments))
                primitiveTranslationResult = PrimitiveFunctionTranslators[primitiveName](self, hirInstruction, resultType, arguments)
                if primitiveTranslationResult is not None:
                    return primitiveTranslationResult

        resultType = self.translateType(hirInstruction.type)
        functional = self.translateValue(hirInstruction.functional)
        arguments = list(filter(lambda x: x.hasNotAbortType(), map(self.translateValue, hirInstruction.arguments)))
        return self.builder.call(resultType, functional, arguments)
    
    def visitCondBranchInstruction(self, hirInstruction: HIRCondBranchInstruction):
        condition = self.translateValue(hirInstruction.condition)
        trueDestination = self.translateValue(hirInstruction.trueDestination)
        falseDestination = self.translateValue(hirInstruction.falseDestination)
        return self.builder.condBranch(condition, trueDestination, falseDestination)

    def visitReturnInstruction(self, hirInstruction: HIRReturnInstruction):
        resultValue = self.translateValue(hirInstruction.result)
        return self.builder.returnValue(resultValue)

for primitiveDef in [
    ('Int8::+',    sdvmBinaryPrimitiveFor(SdvmInstInt8Add)),
    ('Int8::-',    sdvmBinaryPrimitiveFor(SdvmInstInt8Sub)),
    ('Int8::*',    sdvmBinaryPrimitiveFor(SdvmInstInt8Mul)),
    ('Int8:://',   sdvmBinaryPrimitiveFor(SdvmInstInt8Div)),
    ('Int8::%',    sdvmBinaryPrimitiveFor(SdvmInstInt8Rem)),
    ('Int8::&',    sdvmBinaryPrimitiveFor(SdvmInstInt8And)),
    ('Int8::|',    sdvmBinaryPrimitiveFor(SdvmInstInt8Or)),
    ('Int8::^',    sdvmBinaryPrimitiveFor(SdvmInstInt8Xor)),
    ('Int8::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt8Lsl)),
    ('Int8::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt8Asr)),
    ('Int8::=',    sdvmBinaryPrimitiveFor(SdvmInstInt8Equals)),
    ('Int8::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt8NotEquals)),
    ('Int8::<',    sdvmBinaryPrimitiveFor(SdvmInstInt8LessThan)),
    ('Int8::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt8LessOrEquals)),
    ('Int8::>',    sdvmBinaryPrimitiveFor(SdvmInstInt8GreaterThan)),
    ('Int8::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt8GreaterOrEquals)),
    ('Int8::min:', sdvmBinaryPrimitiveFor(SdvmInstInt8Min)),
    ('Int8::max:', sdvmBinaryPrimitiveFor(SdvmInstInt8Max)),

    ('UInt8::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Add)),
    ('UInt8::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Sub)),
    ('UInt8::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Mul)),
    ('UInt8:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt8UDiv)),
    ('UInt8::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt8URem)),
    ('UInt8::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt8And)),
    ('UInt8::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Or)),
    ('UInt8::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Xor)),
    ('UInt8::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsl)),
    ('UInt8::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsr)),
    ('UInt8::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Equals)),
    ('UInt8::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8NotEquals)),
    ('UInt8::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt8LessThan)),
    ('UInt8::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8LessOrEquals)),
    ('UInt8::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterThan)),
    ('UInt8::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterOrEquals)),
    ('UInt8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Min)),
    ('UInt8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Max)),

    ('Char8::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Add)),
    ('Char8::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Sub)),
    ('Char8::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Mul)),
    ('Char8:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt8UDiv)),
    ('Char8::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt8URem)),
    ('Char8::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt8And)),
    ('Char8::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Or)),
    ('Char8::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Xor)),
    ('Char8::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsl)),
    ('Char8::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsr)),
    ('Char8::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Equals)),
    ('Char8::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8NotEquals)),
    ('Char8::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt8LessThan)),
    ('Char8::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8LessOrEquals)),
    ('Char8::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterThan)),
    ('Char8::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterOrEquals)),
    ('Char8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Min)),
    ('Char8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Max)),

    ('Int16::+',    sdvmBinaryPrimitiveFor(SdvmInstInt16Add)),
    ('Int16::-',    sdvmBinaryPrimitiveFor(SdvmInstInt16Sub)),
    ('Int16::*',    sdvmBinaryPrimitiveFor(SdvmInstInt16Mul)),
    ('Int16:://',   sdvmBinaryPrimitiveFor(SdvmInstInt16Div)),
    ('Int16::%',    sdvmBinaryPrimitiveFor(SdvmInstInt16Rem)),
    ('Int16::&',    sdvmBinaryPrimitiveFor(SdvmInstInt16And)),
    ('Int16::|',    sdvmBinaryPrimitiveFor(SdvmInstInt16Or)),
    ('Int16::^',    sdvmBinaryPrimitiveFor(SdvmInstInt16Xor)),
    ('Int16::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt16Lsl)),
    ('Int16::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt16Asr)),
    ('Int16::=',    sdvmBinaryPrimitiveFor(SdvmInstInt16Equals)),
    ('Int16::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt16NotEquals)),
    ('Int16::<',    sdvmBinaryPrimitiveFor(SdvmInstInt16LessThan)),
    ('Int16::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt16LessOrEquals)),
    ('Int16::>',    sdvmBinaryPrimitiveFor(SdvmInstInt16GreaterThan)),
    ('Int16::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt16GreaterOrEquals)),
    ('Int16::min:', sdvmBinaryPrimitiveFor(SdvmInstInt16Min)),
    ('Int16::max:', sdvmBinaryPrimitiveFor(SdvmInstInt16Max)),

    ('UInt16::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Add)),
    ('UInt16::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Sub)),
    ('UInt16::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Mul)),
    ('UInt16:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt16UDiv)),
    ('UInt16::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt16URem)),
    ('UInt16::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt16And)),
    ('UInt16::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Or)),
    ('UInt16::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Xor)),
    ('UInt16::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsl)),
    ('UInt16::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsr)),
    ('UInt16::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Equals)),
    ('UInt16::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16NotEquals)),
    ('UInt16::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt16LessThan)),
    ('UInt16::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16LessOrEquals)),
    ('UInt16::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterThan)),
    ('UInt16::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterOrEquals)),
    ('UInt16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Min)),
    ('UInt16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Max)),

    ('Char16::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Add)),
    ('Char16::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Sub)),
    ('Char16::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Mul)),
    ('Char16:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt16UDiv)),
    ('Char16::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt16URem)),
    ('Char16::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt16And)),
    ('Char16::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Or)),
    ('Char16::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Xor)),
    ('Char16::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsl)),
    ('Char16::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsr)),
    ('Char16::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Equals)),
    ('Char16::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16NotEquals)),
    ('Char16::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt16LessThan)),
    ('Char16::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16LessOrEquals)),
    ('Char16::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterThan)),
    ('Char16::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterOrEquals)),
    ('Char16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Min)),
    ('Char16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Max)),

    ('Int32::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32Add)),
    ('Int32::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32Sub)),
    ('Int32::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32Mul)),
    ('Int32:://',   sdvmBinaryPrimitiveFor(SdvmInstInt32Div)),
    ('Int32::%',    sdvmBinaryPrimitiveFor(SdvmInstInt32Rem)),
    ('Int32::&',    sdvmBinaryPrimitiveFor(SdvmInstInt32And)),
    ('Int32::|',    sdvmBinaryPrimitiveFor(SdvmInstInt32Or)),
    ('Int32::^',    sdvmBinaryPrimitiveFor(SdvmInstInt32Xor)),
    ('Int32::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt32Lsl)),
    ('Int32::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt32Asr)),
    ('Int32::=',    sdvmBinaryPrimitiveFor(SdvmInstInt32Equals)),
    ('Int32::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt32NotEquals)),
    ('Int32::<',    sdvmBinaryPrimitiveFor(SdvmInstInt32LessThan)),
    ('Int32::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt32LessOrEquals)),
    ('Int32::>',    sdvmBinaryPrimitiveFor(SdvmInstInt32GreaterThan)),
    ('Int32::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt32GreaterOrEquals)),
    ('Int32::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32Min)),
    ('Int32::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32Max)),

    ('UInt32::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Add)),
    ('UInt32::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Sub)),
    ('UInt32::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Mul)),
    ('UInt32:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt32UDiv)),
    ('UInt32::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt32URem)),
    ('UInt32::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt32And)),
    ('UInt32::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Or)),
    ('UInt32::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Xor)),
    ('UInt32::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsl)),
    ('UInt32::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsr)),
    ('UInt32::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Equals)),
    ('UInt32::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32NotEquals)),
    ('UInt32::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt32LessThan)),
    ('UInt32::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32LessOrEquals)),
    ('UInt32::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterThan)),
    ('UInt32::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterOrEquals)),
    ('UInt32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Min)),
    ('UInt32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Max)),

    ('Char32::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Add)),
    ('Char32::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Sub)),
    ('Char32::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Mul)),
    ('Char32:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt32UDiv)),
    ('Char32::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt32URem)),
    ('Char32::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt32And)),
    ('Char32::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Or)),
    ('Char32::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Xor)),
    ('Char32::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsl)),
    ('Char32::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsr)),
    ('Char32::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Equals)),
    ('Char32::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32NotEquals)),
    ('Char32::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt32LessThan)),
    ('Char32::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32LessOrEquals)),
    ('Char32::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterThan)),
    ('Char32::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterOrEquals)),
    ('Char32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Min)),
    ('Char32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Max)),

    ('Int64::+',    sdvmBinaryPrimitiveFor(SdvmInstInt64Add)),
    ('Int64::-',    sdvmBinaryPrimitiveFor(SdvmInstInt64Sub)),
    ('Int64::*',    sdvmBinaryPrimitiveFor(SdvmInstInt64Mul)),
    ('Int64:://',   sdvmBinaryPrimitiveFor(SdvmInstInt64Div)),
    ('Int64::%',    sdvmBinaryPrimitiveFor(SdvmInstInt64Rem)),
    ('Int64::&',    sdvmBinaryPrimitiveFor(SdvmInstInt64And)),
    ('Int64::|',    sdvmBinaryPrimitiveFor(SdvmInstInt64Or)),
    ('Int64::^',    sdvmBinaryPrimitiveFor(SdvmInstInt64Xor)),
    ('Int64::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt64Lsl)),
    ('Int64::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt64Asr)),
    ('Int64::=',    sdvmBinaryPrimitiveFor(SdvmInstInt64Equals)),
    ('Int64::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt64NotEquals)),
    ('Int64::<',    sdvmBinaryPrimitiveFor(SdvmInstInt64LessThan)),
    ('Int64::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt64LessOrEquals)),
    ('Int64::>',    sdvmBinaryPrimitiveFor(SdvmInstInt64GreaterThan)),
    ('Int64::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt64GreaterOrEquals)),
    ('Int64::min:', sdvmBinaryPrimitiveFor(SdvmInstInt64Min)),
    ('Int64::max:', sdvmBinaryPrimitiveFor(SdvmInstInt64Max)),

    ('UInt64::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Add)),
    ('UInt64::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Sub)),
    ('UInt64::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Mul)),
    ('UInt64:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt64UDiv)),
    ('UInt64::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt64URem)),
    ('UInt64::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt64And)),
    ('UInt64::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Or)),
    ('UInt64::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Xor)),
    ('UInt64::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt64Lsl)),
    ('UInt64::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt64Lsr)),
    ('UInt64::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Equals)),
    ('UInt64::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64NotEquals)),
    ('UInt64::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt64LessThan)),
    ('UInt64::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64LessOrEquals)),
    ('UInt64::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt64GreaterThan)),
    ('UInt64::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64GreaterOrEquals)),
    ('UInt64::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt64Min)),
    ('UInt64::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt64Max)),

    ('Float32::+',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Add)),
    ('Float32::-',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Sub)),
    ('Float32::*',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Mul)),
    ('Float32::/',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Div)),
    ('Float32::sqrt',      sdvmUnaryPrimitiveFor(SdvmInstFloat32Sqrt)),
    ('Float32::=',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Equals)),
    ('Float32::~=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32NotEquals)),
    ('Float32::<',        sdvmBinaryPrimitiveFor(SdvmInstFloat32LessThan)),
    ('Float32::<=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32LessOrEquals)),
    ('Float32::>',        sdvmBinaryPrimitiveFor(SdvmInstFloat32GreaterThan)),
    ('Float32::>=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32GreaterOrEquals)),
    ('Float32::min:',     sdvmBinaryPrimitiveFor(SdvmInstFloat32Min)),
    ('Float32::max:',     sdvmBinaryPrimitiveFor(SdvmInstFloat32Max)),
    ('Float32::rounded',   sdvmUnaryPrimitiveFor(SdvmInstFloat32Round)),
    ('Float32::floor',     sdvmUnaryPrimitiveFor(SdvmInstFloat32Floor)),
    ('Float32::ceil',      sdvmUnaryPrimitiveFor(SdvmInstFloat32Ceil)),
    ('Float32::truncated', sdvmUnaryPrimitiveFor(SdvmInstFloat32Truncate)),

    ('Float64::+',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Add)),
    ('Float64::-',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Sub)),
    ('Float64::*',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Mul)),
    ('Float64::/',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Div)),
    ('Float64::sqrt',      sdvmUnaryPrimitiveFor(SdvmInstFloat64Sqrt)),
    ('Float64::=',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Equals)),
    ('Float64::~=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64NotEquals)),
    ('Float64::<',        sdvmBinaryPrimitiveFor(SdvmInstFloat64LessThan)),
    ('Float64::<=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64LessOrEquals)),
    ('Float64::>',        sdvmBinaryPrimitiveFor(SdvmInstFloat64GreaterThan)),
    ('Float64::>=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64GreaterOrEquals)),
    ('Float64::min:',     sdvmBinaryPrimitiveFor(SdvmInstFloat64Min)),
    ('Float64::max:',     sdvmBinaryPrimitiveFor(SdvmInstFloat64Max)),
    ('Float64::rounded',   sdvmUnaryPrimitiveFor(SdvmInstFloat64Round)),
    ('Float64::floor',     sdvmUnaryPrimitiveFor(SdvmInstFloat64Floor)),
    ('Float64::ceil',      sdvmUnaryPrimitiveFor(SdvmInstFloat64Ceil)),
    ('Float64::truncated', sdvmUnaryPrimitiveFor(SdvmInstFloat64Truncate)),

    ## Primitive vector float instructions.
    ('Float32x2::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Add)),
    ('Float32x2::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Sub)),
    ('Float32x2::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Mul)),
    ('Float32x2::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Div)),
    ('Float32x2::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Sqrt)),
    ('Float32x2::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Min)),
    ('Float32x2::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Max)),
    ('Float32x2::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Round)),
    ('Float32x2::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Floor)),
    ('Float32x2::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Ceil)),
    ('Float32x2::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Truncate)),

    ('Float32x3::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Add)),
    ('Float32x3::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Sub)),
    ('Float32x3::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Mul)),
    ('Float32x3::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Div)),
    ('Float32x3::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Sqrt)),
    ('Float32x3::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Min)),
    ('Float32x3::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Max)),
    ('Float32x3::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Round)),
    ('Float32x3::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Floor)),
    ('Float32x3::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Ceil)),
    ('Float32x3::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Truncate)),

    ('Float32x4::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Add)),
    ('Float32x4::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Sub)),
    ('Float32x4::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Mul)),
    ('Float32x4::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Div)),
    ('Float32x4::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Sqrt)),
    ('Float32x4::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Min)),
    ('Float32x4::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Max)),
    ('Float32x4::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Round)),
    ('Float32x4::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Floor)),
    ('Float32x4::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Ceil)),
    ('Float32x4::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Truncate)),

    ('Float64x2::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Add)),
    ('Float64x2::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Sub)),
    ('Float64x2::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Mul)),
    ('Float64x2::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Div)),
    ('Float64x2::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Sqrt)),
    ('Float64x2::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Min)),
    ('Float64x2::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Max)),
    ('Float64x2::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Round)),
    ('Float64x2::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Floor)),
    ('Float64x2::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Ceil)),
    ('Float64x2::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Truncate)),

    ('Float64x3::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Add)),
    ('Float64x3::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Sub)),
    ('Float64x3::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Mul)),
    ('Float64x3::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Div)),
    ('Float64x3::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Sqrt)),
    ('Float64x3::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Min)),
    ('Float64x3::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Max)),
    ('Float64x3::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Round)),
    ('Float64x3::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Floor)),
    ('Float64x3::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Ceil)),
    ('Float64x3::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Truncate)),

    ('Float64x4::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Add)),
    ('Float64x4::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Sub)),
    ('Float64x4::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Mul)),
    ('Float64x4::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Div)),
    ('Float64x4::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Sqrt)),
    ('Float64x4::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Min)),
    ('Float64x4::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Max)),
    ('Float64x4::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Round)),
    ('Float64x4::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Floor)),
    ('Float64x4::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Ceil)),
    ('Float64x4::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Truncate)),

    ## Primitive vector integer instructions.
    ('Int32x2::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Add)),
    ('Int32x2::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Sub)),
    ('Int32x2::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Mul)),
    ('Int32x2::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x2Min)),
    ('Int32x2::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x2Max)),

    ('Int32x3::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Add)),
    ('Int32x3::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Sub)),
    ('Int32x3::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Mul)),
    ('Int32x3::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Min)),
    ('Int32x3::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Max)),

    ('Int32x4::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Add)),
    ('Int32x4::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Sub)),
    ('Int32x4::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Mul)),
    ('Int32x4::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Min)),
    ('Int32x4::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Max)),

    ('UInt32x2::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Add)),
    ('UInt32x2::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Sub)),
    ('UInt32x2::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Mul)),
    ('UInt32x2::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Min)),
    ('UInt32x2::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Max)),

    ('UInt32x3::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Add)),
    ('UInt32x3::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Sub)),
    ('UInt32x3::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Mul)),
    ('UInt32x3::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Min)),
    ('UInt32x3::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Max)),

    ('UInt32x4::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Add)),
    ('UInt32x4::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Sub)),
    ('UInt32x4::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Mul)),
    ('UInt32x4::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Min)),
    ('UInt32x4::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Max)),

    ## Casting instruction table.
    ('Int8::asInt8',    yourselfTranslator),
    ('Int8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int16)),
    ('Int8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int32)),
    ('Int8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int64)),
    ('Int8::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt8_Bitcast_UInt8)),
    ('Int8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt16)),
    ('Int8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt32)),
    ('Int8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt64)),
    ('Int8::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt8_Bitcast_UInt8)),
    ('Int8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt16)),
    ('Int8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt32)),
    ('Int8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt8_IntegerToFloat_Float32)),
    ('Int8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt8_IntegerToFloat_Float64)),

    ('UInt8::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt8_Bitcast_Int8)),
    ('UInt8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int16)),
    ('UInt8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int32)),
    ('UInt8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int64)),
    ('UInt8::asUInt8',   yourselfTranslator),
    ('UInt8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
    ('UInt8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
    ('UInt8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt64)),
    ('UInt8::asChar8',   yourselfTranslator),
    ('UInt8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
    ('UInt8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
    ('UInt8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float32)),
    ('UInt8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float64)),

    ('Char8::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt8_Bitcast_Int8)),
    ('Char8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int16)),
    ('Char8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int32)),
    ('Char8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int64)),
    ('Char8::asUInt8',   yourselfTranslator),
    ('Char8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
    ('Char8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
    ('Char8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt64)),
    ('Char8::asChar8',   yourselfTranslator),
    ('Char8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
    ('Char8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
    ('Char8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float32)),
    ('Char8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float64)),

    ('Int16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_Int8)),
    ('Int16::asInt16',   yourselfTranslator),
    ('Int16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt16_SignExtend_Int32)),
    ('Int16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt16_SignExtend_Int64)),
    ('Int16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_UInt8)),
    ('Int16::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt16_Bitcast_UInt16)),
    ('Int16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt32)),
    ('Int16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt64)),
    ('Int16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_UInt8)),
    ('Int16::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt16_Bitcast_UInt16)),
    ('Int16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt32)),
    ('Int16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt16_IntegerToFloat_Float32)),
    ('Int16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt16_IntegerToFloat_Float64)),

    ('UInt16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_Int8)),
    ('UInt16::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Bitcast_Int16)),
    ('UInt16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int32)),
    ('UInt16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int64)),
    ('UInt16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
    ('UInt16::asUInt16',  yourselfTranslator),
    ('UInt16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
    ('UInt16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt64)),
    ('UInt16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
    ('UInt16::asChar16',  yourselfTranslator),
    ('UInt16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
    ('UInt16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float32)),
    ('UInt16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float64)),

    ('Char16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_Int8)),
    ('Char16::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Bitcast_Int16)),
    ('Char16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int32)),
    ('Char16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int64)),
    ('Char16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
    ('Char16::asUInt16',  yourselfTranslator),
    ('Char16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
    ('Char16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt64)),
    ('Char16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
    ('Char16::asChar16',  yourselfTranslator),
    ('Char16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
    ('Char16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float32)),
    ('Char16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float64)),

    ('Int32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_Int8)),
    ('Int32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_Int16)),
    ('Int32::asInt32',   yourselfTranslator),
    ('Int32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt32_SignExtend_Int64)),
    ('Int32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt8)),
    ('Int32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt16)),
    ('Int32::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Bitcast_UInt32)),
    ('Int32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64)),
    ('Int32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt8)),
    ('Int32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt16)),
    ('Int32::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Bitcast_UInt32)),
    ('Int32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt32_IntegerToFloat_Float32)),
    ('Int32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt32_IntegerToFloat_Float64)),

    ('UInt32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int8)),
    ('UInt32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int16)),
    ('UInt32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Bitcast_Int32)),
    ('UInt32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_Int64)),
    ('UInt32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
    ('UInt32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
    ('UInt32::asUInt32',  yourselfTranslator),
    ('UInt32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_UInt64)),
    ('UInt32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
    ('UInt32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
    ('UInt32::asChar32',  yourselfTranslator),
    ('UInt32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float32)),
    ('UInt32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float64)),

    ('Char32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int8)),
    ('Char32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int16)),
    ('Char32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Bitcast_Int32)),
    ('Char32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_Int64)),
    ('Char32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
    ('Char32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
    ('Char32::asUInt32',  yourselfTranslator),
    ('Char32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_UInt64)),
    ('Char32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
    ('Char32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
    ('Char32::asChar32',  yourselfTranslator),
    ('Char32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float32)),
    ('Char32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float64)),

    ('Int64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int8)),
    ('Int64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int16)),
    ('Int64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int32)),
    ('Int64::asInt64',   yourselfTranslator),
    ('Int64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt8)),
    ('Int64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt16)),
    ('Int64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt32)),
    ('Int64::asUInt64',  yourselfTranslator),
    ('Int64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt8)),
    ('Int64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt16)),
    ('Int64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt32)),
    ('Int64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt64_IntegerToFloat_Float32)),
    ('Int64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt64_IntegerToFloat_Float64)),

    ('UInt64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int8)),
    ('UInt64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int16)),
    ('UInt64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int32)),
    ('UInt64::asInt64',   yourselfTranslator),
    ('UInt64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt8)),
    ('UInt64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt16)),
    ('UInt64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt32)),
    ('UInt64::asUInt64',  yourselfTranslator),
    ('UInt64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt8)),
    ('UInt64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt16)),
    ('UInt64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt32)),
    ('UInt64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt64_IntegerToFloat_Float32)),
    ('UInt64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt64_IntegerToFloat_Float64)),

    ('Float32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int8)),
    ('Float32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int16)),
    ('Float32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int32)),
    ('Float32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int64)),
    ('Float32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt8)),
    ('Float32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt16)),
    ('Float32::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt32)),
    ('Float32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt64)),
    ('Float32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt8)),
    ('Float32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt16)),
    ('Float32::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt32)),
    ('Float32::asFloat32', yourselfTranslator),
    ('Float32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatExtend_Float64)),

    ('Float64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int8)),
    ('Float64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int16)),
    ('Float64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int32)),
    ('Float64::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int64)),
    ('Float64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt8)),
    ('Float64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt16)),
    ('Float64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt32)),
    ('Float64::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt64)),
    ('Float64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt8)),
    ('Float64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt16)),
    ('Float64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt32)),
    ('Float64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstFloat64_Truncate_Float32)),
    ('Float64::asFloat64', yourselfTranslator),

    ('Int32::asSize',        pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64))),
    ('Int32::asUIntPointer', pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64))),
    ('Int32::asIntPointer',  pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_SignExtend_Int64))),
]:
    name, translator = primitiveDef
    PrimitiveFunctionTranslators[name] = translator