from .hir import *
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
        self.voidType = MIRVoidType(self, 'Void', 0, 1)
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

    def isVoidType(self) -> bool:
        return False
    
    def isClosureType(self) -> bool:
        return False
    
    def isFunctionType(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.name

class MIRVoidType(MIRType):
    def isVoidType(self) -> bool:
        return True

class MIRBooleanType(MIRType):
    pass

class MIRUnsignedIntegerType(MIRType):
    pass

class MIRSignedIntegerType(MIRType):
    pass

class MIRFloatingPointType(MIRType):
    pass

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
    def __init__(self, context: MIRContext) -> None:
        self.context = context

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

    def hasVoidType(self) -> bool:
        return self.getType().isVoidType()

    def hasNotVoidType(self) -> bool:
        return not self.getType().isVoidType()

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
            for successor in basicBlock.successorBlocks():
                visit(successor)
            visitedList.append(basicBlock)

        for basicBlock in self.basicBlocks():
            visit(basicBlock)

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
    def __init__(self, context: MIRContext, type: MIRType, name: str = None) -> None:
        super().__init__(context)
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
    def __init__(self, context: MIRContext, name: str = None) -> None:
        super().__init__(context, context.basicBlockType, name)
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

class MIRLoadInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, type: MIRValue, pointer: MIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.pointer = pointer

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitLoadInstruction(self)

    def fullPrintString(self) -> str:
        return '%s := load %s' % (str(self), str(self.pointer))

class MIRStoreInstruction(MIRInstruction):
    def __init__(self, context: MIRContext, pointer: MIRValue, value: MIRValue, name: str = None) -> None:
        super().__init__(context, context.voidType, name)
        self.pointer = pointer
        self.value = value

    def accept(self, visitor: MIRValueVisitor):
        return visitor.visitStoreInstruction(self)

    def fullPrintString(self) -> str:
        return 'store %s value %s(' % (str(self.pointer), str(self.value))

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
        self.basicBlock = None

    def newBasicBlock(self, name: str):
        return MIRBasicBlock(self.context, name)

    def beginBasicBlock(self, basicBlock: HIRBasicBlock) -> HIRBasicBlock:
        self.function.addBasicBlock(basicBlock)
        self.basicBlock = basicBlock
        return basicBlock

    def beginNewBasicBlock(self, name: str) -> HIRBasicBlock:
        return self.beginBasicBlock(self.newBasicBlock(name))
    
    def isLastTerminator(self) -> bool:
        return self.basicBlock is not None and self.basicBlock.lastInstruction is not None and self.basicBlock.lastInstruction.isTerminatorInstruction()
    
    def addInstruction(self, instruction: MIRInstruction) -> HIRValue:
        self.basicBlock.addInstruction(instruction)
        return instruction
    
    def call(self, resultType: MIRType, function: MIRValue, arguments: list[HIRValue]) -> MIRInstruction:
        return self.addInstruction(MIRCallInstruction(self.context, resultType, function, arguments))
    
    def returnValue(self, value: MIRValue) -> MIRInstruction:
        return self.addInstruction(MIRReturnInstruction(self.context, value))

    def load(self, type: MIRType, pointer: MIRValue) -> MIRLoadInstruction:
        return self.addInstruction(MIRLoadInstruction(self.context, type, pointer))

    def store(self, pointer: MIRValue, value: MIRValue) -> MIRLoadInstruction:
        return self.addInstruction(MIRStoreInstruction(self.context, pointer, value))

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
            (hirContext.unitType,  mirContext.voidType),
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
    
    def visitConstantUnit(self, constant: HIRConstantUnit) -> MIRValue:
        return self.context.void
    
    def visitConstantStringData(self, constant: HIRConstantStringData) -> MIRValue:
        return MIRConstantStringData(self.translateType(constant.getType()), constant.value, constant.nullTerminated)

    def visitConstantPrimitiveInteger(self, constant: HIRConstantPrimitiveInteger) -> MIRValue:
        return MIRConstantInteger(self.translateType(constant.getType()), constant.value)

    def visitFunctionalDefinitionValue(self, functional: HIRFunctionalDefinition) -> MIRValue:
        mirFunction = MIRFunction(self.context, functional.name)
        self.translatedValueDictionary[functional] = mirFunction
        return mirFunction

    def visitFunctionalDefinitionValue(self, functional: HIRFunctionalDefinition) -> MIRValue:
        mirFunction = MIRFunction(self.context, functional.name)
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
        mirArgument = MIRArgument(self.context, self.translateType(hirArgument.getType()), hirArgument.name)
        if mirArgument.hasVoidType():
            self.translatedValueDictionary[mirArgument] = self.context.void
            return

        self.translatedValueDictionary[hirArgument] = mirArgument
        self.function.arguments.append(mirArgument)

    def translateCapture(self, hirCapture: HIRFunctionalCaptureValue):
        mirCapture = MIRCapture(self.context, self.translateType(hirCapture.getType()), hirCapture.name)
        if mirCapture.hasVoidType():
            self.translatedValueDictionary[hirCapture] = self.context.void
            return

        self.translatedValueDictionary[hirCapture] = mirCapture
        self.function.captures.append(mirCapture)

    def translateBasicBlocksOf(self, functional: HIRFunctionalDefinition):
        for hirBasicBlock in functional.basicBlocks():
            mirBasicBlock = MIRBasicBlock(self.context, hirBasicBlock.name)
            self.translatedValueDictionary[hirBasicBlock] = mirBasicBlock

        for hirBasicBlock in functional.basicBlocksInReversePostOrder():
            mirBasicBlock: MIRBasicBlock = self.translatedValueDictionary[hirBasicBlock]
            self.builder.beginBasicBlock(mirBasicBlock)
            self.translateBasicBlock(hirBasicBlock, mirBasicBlock)

    def translateBasicBlock(self, hirBasicBlock: HIRBasicBlock, mirBasicBlock: MIRBasicBlock):
        for instruction in hirBasicBlock.instructions():
            self.translateInstruction(instruction)

    def translateInstruction(self, hirInstruction: HIRInstruction):
        assert hirInstruction not in self.translatedValueDictionary
        translatedValue = hirInstruction.accept(self)
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
        arguments = list(filter(lambda x: x.hasNotVoidType(), map(self.translateValue, hirInstruction.arguments)))
        return self.builder.call(resultType, functional, arguments)
    
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
    ('UInt8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8UMin)),
    ('UInt8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8UMax)),

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
    ('Char8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8UMin)),
    ('Char8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8UMax)),

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
    ('UInt16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16UMin)),
    ('UInt16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16UMax)),

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
    ('Char16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16UMin)),
    ('Char16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16UMax)),

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
    ('Int32::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32UMin)),
    ('Int32::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32UMax)),

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
    ('UInt32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32UMin)),
    ('UInt32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32UMax)),

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
    ('Char32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32UMin)),
    ('Char32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32UMax)),

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
    ('Int64::min:', sdvmBinaryPrimitiveFor(SdvmInstInt64UMin)),
    ('Int64::max:', sdvmBinaryPrimitiveFor(SdvmInstInt64UMax)),

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
    ('UInt64::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt64UMin)),
    ('UInt64::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt64UMax)),

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
    ('Int8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt8_SignedToFloat_Float32)),
    ('Int8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt8_SignedToFloat_Float64)),

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
    ('UInt8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_UnsignedToFloat_Float32)),
    ('UInt8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_UnsignedToFloat_Float64)),

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
    ('Char8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_UnsignedToFloat_Float32)),
    ('Char8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_UnsignedToFloat_Float64)),

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
    ('Int16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt16_SignedToFloat_Float32)),
    ('Int16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt16_SignedToFloat_Float64)),

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
    ('UInt16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_UnsignedToFloat_Float32)),
    ('UInt16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_UnsignedToFloat_Float64)),

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
    ('Char16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_UnsignedToFloat_Float32)),
    ('Char16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_UnsignedToFloat_Float64)),

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
    ('Int32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt32_SignedToFloat_Float32)),
    ('Int32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt32_SignedToFloat_Float64)),

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
    ('UInt32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_UnsignedToFloat_Float32)),
    ('UInt32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_UnsignedToFloat_Float64)),

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
    ('Char32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_UnsignedToFloat_Float32)),
    ('Char32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_UnsignedToFloat_Float64)),

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
    ('Int64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt64_SignedToFloat_Float32)),
    ('Int64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt64_SignedToFloat_Float64)),

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
    ('UInt64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt64_UnsignedToFloat_Float32)),
    ('UInt64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt64_UnsignedToFloat_Float64)),

    ('Float32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToSigned_Int8)),
    ('Float32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToSigned_Int16)),
    ('Float32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToSigned_Int32)),
    ('Float32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToSigned_Int64)),
    ('Float32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt8)),
    ('Float32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt16)),
    ('Float32::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt32)),
    ('Float32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt64)),
    ('Float32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt8)),
    ('Float32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt16)),
    ('Float32::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToUnsigned_UInt32)),
    ('Float32::asFloat32', yourselfTranslator),
    ('Float32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatExtend_Float64)),

    ('Float64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToSigned_Int8)),
    ('Float64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToSigned_Int16)),
    ('Float64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToSigned_Int32)),
    ('Float64::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToSigned_Int64)),
    ('Float64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt8)),
    ('Float64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt16)),
    ('Float64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt32)),
    ('Float64::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt64)),
    ('Float64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt8)),
    ('Float64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt16)),
    ('Float64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToUnsigned_UInt32)),
    ('Float64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstFloat64_Truncate_Float32)),
    ('Float64::asFloat64', yourselfTranslator),
]:
    name, translator = primitiveDef
    PrimitiveFunctionTranslators[name] = translator