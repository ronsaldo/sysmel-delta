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

    def exportValue(self, name: str, value: MIRConstant) -> None:
        self.exportedValues.append((name, value))

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
        for name, value in self.exportedValues:
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

        for name, value in hirModule.exportedValues:
            self.module.exportValue(name, self.translateValue(value))

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
    
    def visitFunctionType(self, type: HIRFunctionType):
        if type.callingConvention is not None:
            return self.context.callingConventionFunctionTypeMap[type.callingConvention]
        return self.context.closureType
    
    def visitConstantUnit(self, constant: HIRConstantUnit) -> MIRValue:
        return self.context.void

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

for name, translator in [
    ('Int32::+', sdvmBinaryPrimitiveFor(SdvmInstInt32Add)),
    ('Int32::-', sdvmBinaryPrimitiveFor(SdvmInstInt32Sub)),
    ('Int32::*', sdvmBinaryPrimitiveFor(SdvmInstInt32Mul)),
    ('Int32::/', sdvmBinaryPrimitiveFor(SdvmInstInt32Div))
]:
    PrimitiveFunctionTranslators[name] = translator