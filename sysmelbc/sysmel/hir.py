from abc import ABC, abstractmethod
from .ghir import *

class HIRContext:
    def __init__(self, pointerSize: int = 8) -> None:
        self.typeUniverses = dict()
        self.pointerSize = pointerSize
        self.pointerAlignment = pointerSize
        self.gcPointerSize = pointerSize*2
        self.gcPointerAlignment = pointerSize

        self.anySize = self.gcPointerSize
        self.anyAlignment = self.gcPointerAlignment
        self.functionTypeSize = self.gcPointerSize
        self.functionTypeAlignment = self.gcPointerAlignment
        self.anyType = HIRAnyType(self, 'Any', self.anySize, self.anyAlignment)
        self.booleanType = HIRPrimitiveBooleanType(self, 'Boolean', 1, 1)
        self.unitType = HIRUnitType(self, 'Unit', 0, 1)
        self.int8Type   = HIRPrimitiveIntegerType(self, 'Int8',   True, 1, 1)
        self.int16Type  = HIRPrimitiveIntegerType(self, 'Int16',  True, 2, 2)
        self.int32Type  = HIRPrimitiveIntegerType(self, 'Int32',  True, 4, 4)
        self.int64Type  = HIRPrimitiveIntegerType(self, 'Int64',  True, 8, 8)
        self.uint8Type  = HIRPrimitiveIntegerType(self, 'UInt8',  False, 1, 1)
        self.uint16Type = HIRPrimitiveIntegerType(self, 'UInt16', False, 2, 2)
        self.uint32Type = HIRPrimitiveIntegerType(self, 'UInt32', False, 4, 4)
        self.uint64Type = HIRPrimitiveIntegerType(self, 'UInt64', False, 8, 8)
        self.float32Type = HIRPrimitiveFloatType(self, 'Float32', 4, 4)
        self.float64Type = HIRPrimitiveFloatType(self, 'Float64', 8, 8)
        self.basicBlockType = HIRBasicBlockType(self, 'BasicBlock', pointerSize, pointerSize)
        self.functionalDefinitionType = HIRFunctionalDefinitionType(self, 'FunctionalDefinition', pointerSize, pointerSize)

    def getTypeUniverse(self, index):
        if index not in self.typeUniverses:
            self.typeUniverses[index] = HIRTypeUniverse(self, index)
        return self.typeUniverses[index]

class HIRValueVisitor(ABC):
    @abstractmethod
    def visitPrimitiveType(self, value):
        pass

    @abstractmethod
    def visitFunctionType(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveFunction(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveInteger(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveFloat(self, value):
        pass

    @abstractmethod
    def visitFunctionalDefinitionValue(self, value):
        pass

    @abstractmethod
    def visitFunctionalCaptureValue(self, value):
        pass

    @abstractmethod
    def visitFunctionalArgumentValue(self, value):
        pass

    @abstractmethod
    def visitBasicBlock(self, value):
        pass

    @abstractmethod
    def visitCallInstruction(self, value):
        pass

    @abstractmethod
    def visitReturnInstruction(self, value):
        pass

    @abstractmethod
    def visitConstantLambda(self, value):
        pass

    @abstractmethod
    def visitModule(self, value):
        pass

class HIRValue(ABC):
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    @abstractmethod
    def accept(self, visitor: HIRValueVisitor):
        pass

    @abstractmethod
    def getType(self):
        pass

    def isConstantPrimitiveFunction(self) -> bool:
        return False

    def isConstantLambda(self) -> bool:
        return False

    def isFunctionalLocalValue(self) -> bool:
        return False

    def isTerminatorInstruction(self) -> bool:
        return False

class HIRTypeValue(HIRValue):
    def  __init__(self, context: HIRContext) -> None:
        super().__init__(context)

    def isType(self):
        return True

    @abstractmethod
    def getSize(self) -> int:
        pass

    @abstractmethod
    def getAlignment(self) -> int:
        pass

class HIRTypeUniverse(HIRTypeValue):
    def  __init__(self, context: HIRContext, index) -> None:
        super().__init__(context)
        self.index = index

    def getType(self):
        return self.context.getTypeUniverse(self.index + 1)

    def getSize(self) -> int:
        return self.context.anySize

    def getAlignment(self) -> int:
        return self.context.anyAlignment
    
    def __str__(self) -> str:
        if self.index == 0:
            return 'Type'
        return 'Type@%d' % self.index

class HIRCompositeType(HIRTypeValue):
    def  __init__(self, context: HIRContext, elements: list[HIRTypeValue]) -> None:
        super().__init__(context)
        self.alignment = None
        self.size = None
        self.elements = elements

    def getAlignment(self) -> int:
        return self.alignment
    
    def getSize(self) -> int:
        return self.size

    def getType(self):
        return self.context.getTypeUniverse(0)

class HIRProductType(HIRCompositeType):
    def __str__(self) -> str:
        result = '('
        isFirst = True
        for element in self.elements:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(element)
        result += ')'
        return result

class HIRPrimitiveType(HIRTypeValue):
    def  __init__(self, context: HIRContext, name: str, size: int, alignment: int) -> None:
        super().__init__(context)
        self.name = name
        self.size = size
        self.alignment = alignment

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitPrimitiveType(self)

    def getAlignment(self) -> int:
        return self.alignment
    
    def getSize(self) -> int:
        return self.size

    def getType(self):
        return self.context.getTypeUniverse(0)
    
    def __str__(self) -> str:
        return self.name

class HIRAnyType(HIRPrimitiveType):
    pass

class HIRUnitType(HIRPrimitiveType):
    pass

class HIRBasicBlockType(HIRPrimitiveType):
    pass

class HIRFunctionalDefinitionType(HIRPrimitiveType):
    pass

class HIRPrimitiveBooleanType(HIRPrimitiveType):
    pass

class HIRPrimitiveIntegerType(HIRPrimitiveType):
    def __init__(self, context: HIRContext, name: str, isSigned: bool, size: int, alignment: int) -> None:
        super().__init__(context, name, size, alignment)
        self.isSigned = isSigned

class HIRPrimitiveFloatType(HIRPrimitiveType):
    pass

class HIRFunctionType(HIRTypeValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.argumentTypes = []
        self.resultType: HIRValue = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionType(self)

    def __str__(self) -> str:
        result = '('
        isFirst = True
        for arg in self.argumentTypes:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ') -> '
        result += str(self.resultType)
        return result
    
    def getAlignment(self) -> int:
        return self.context.functionTypeAlignment
    
    def getSize(self) -> int:
        return self.context.functionTypeSize

    def getType(self):
        return self.context.getTypeUniverse(0)    

class HIRConstant(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context)
        self.type = type

    def getType(self):
        return self.type

class HIRConstantPrimitiveFunction(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue, name: str, compileTimeImplementation = None) -> None:
        super().__init__(context, type)
        self.name = name
        self.compileTimeImplementation = compileTimeImplementation

    def isConstantPrimitiveFunction(self) -> bool:
        return True

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveFunction(self)

    def __str__(self) -> str:
        return '%s <%s>' % (str(self.type), self.name)

class HIRConstantPrimitive(HIRConstant):
    pass

class HIRConstantPrimitiveInteger(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: int) -> None:
        super().__init__(context, type)
        self.value = value

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveInteger(self)

    def __str__(self) -> str:
        return '%s(%d)' % (str(self.type), self.value)

class HIRConstantPrimitiveFloat(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: float) -> None:
        super().__init__(context, type)
        self.value = value

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveFloat(self)

    def __str__(self) -> str:
        return '%s(%f)' % (str(self.type), self.value)
    
class HIRGlobalValue(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context, type)
        self.name = None
        self.globalValueIndex = 0

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (self.name, self.globalValueIndex)
        return '@%d' % self.globalValueIndex
    
    def fullPrintString(self) -> str:
        return str(self)

class HIRFunctionalDefinition(HIRGlobalValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context, context.functionalDefinitionType)
        self.captures = []
        self.arguments = []
        self.firstBasicBlock: HIRBasicBlock = None
        self.lastBasicBlock: HIRBasicBlock = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalDefinitionValue(self)

    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBasicBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBasicBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def enumerateLocalValues(self):
        index = 0
        for localValue in self.allLocalValues():
            localValue.localValueIndex = index
            index += 1

    def allLocalValues(self):
        for capture in self.captures:
            yield capture
        for argument in self.arguments:
            yield argument
        for basicBlock in self.basicBlocks():
            yield basicBlock
            for instruction in basicBlock.instructions():
                yield instruction

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

    def fullPrintString(self) -> str:
        self.enumerateLocalValues()
        result = str(self)
        result += ' := ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += capture.fullPrintString()

        result += '] ('
        isFirst = True
        for argument in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += argument.fullPrintString()

        result += ') : '
        result += str(self.type)
        result += ' {\n'
        for basicBlock in self.basicBlocks():
            result += basicBlock.fullPrintString()
        result += '}\n'
        return result

class HIRFunctionalLocalValue(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None) -> None:
        super().__init__(context)
        self.name: str = name
        self.type = type
        self.localValueIndex = 0

    def isFunctionalLocalValue(self) -> bool:
        return True
    
    def getType(self):
        return self.type

    def __str__(self) -> str:
        if self.name is not None:
            return '$%s|%d' % (self.name, self.localValueIndex)
        return '$%d' % self.localValueIndex

class HIRFunctionalCaptureValue(HIRFunctionalLocalValue):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalCaptureValue(self)
    
    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRFunctionalArgumentValue(HIRFunctionalLocalValue):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalArgumentValue(self)

    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRBasicBlock(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, context.basicBlockType, name)
        self.previousBasicBlock: HIRBasicBlock = None
        self.nextBasicBlock: HIRBasicBlock = None
        self.firstInstruction: HIRInstruction = None
        self.lastInstruction: HIRInstruction = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitBasicBlock(self)

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

    def fullPrintString(self) -> str:
        result = str(self)
        result += ':\n'
        for instruction in self.instructions():
            result += '    '
            result += instruction.fullPrintString()
            result += '\n'
        return result
    
    def successorBlocks(self):
        if self.lastInstruction is None:
            return []
        return self.lastInstruction.successorBlocks()

class HIRInstruction(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.previousInstruction: HIRInstruction = None
        self.nextInstruction: HIRInstruction = None

    def successorBlocks(self) -> list[HIRBasicBlock]:
        return []

class HIRCallInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, functional: HIRValue, arguments: list[HIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.functional = functional
        self.arguments = arguments

    def accept(self, visitor: HIRValueVisitor):
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
    
class HIRTerminatorInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, context.unitType, name)
    
    def isTerminatorInstruction(self) -> bool:
        return True

class HIRReturnInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, result: HIRValue) -> None:
        super().__init__(context)
        self.result = result

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitReturnInstruction(self)

    def fullPrintString(self) -> str:
        return 'return %s' % str(self.result)

class HIRConstantLambda(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRConstant, captures: list[HIRConstant], definition: HIRFunctionalDefinition) -> None:
        super().__init__(context, type)
        self.captures = captures
        self.definition = definition

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantLambda(self)

    def isConstantLambda(self) -> bool:
        return True

    def __str__(self) -> str:
        result = 'lambda '
        result += str(self.definition)
        result += ' captures ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(capture)
        result += '] : '
        result += str(self.type)
        return result

class HIRBuilder:
    def __init__(self, context: HIRContext, functional: HIRFunctionalDefinition) -> None:
        self.context = context
        self.functional = functional
        self.basicBlock = None
    
    def newBasicBlock(self, name: str):
        return HIRBasicBlock(self.context, name)

    def beginBasicBlock(self, basicBlock: HIRBasicBlock) -> HIRBasicBlock:
        self.functional.addBasicBlock(basicBlock)
        self.basicBlock = basicBlock
        return basicBlock

    def beginNewBasicBlock(self, name: str) -> HIRBasicBlock:
        return self.beginBasicBlock(self.newBasicBlock(name))
    
    def isLastTerminator(self) -> bool:
        return self.basicBlock is not None and self.basicBlock.lastInstruction is not None and self.basicBlock.lastInstruction.isTerminatorInstruction()
    
    def addInstruction(self, instruction: HIRInstruction) -> HIRValue:
        self.basicBlock.addInstruction(instruction)
        return instruction
    
    def call(self, resultType: HIRValue, functional: HIRValue, arguments: list[HIRValue]) -> HIRInstruction:
        return self.addInstruction(HIRCallInstruction(self.context, resultType, functional, arguments))
    
    def returnValue(self, value) -> HIRInstruction:
        return self.addInstruction(HIRReturnInstruction(self.context, value))

class HIRModule(HIRValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.entryPoint: HIRValue = None
        self.globalValues: list[HIRGlobalValue] = []

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitModule(self)

    def getType(self):
        return None
    
    def addGlobalValue(self, globalValue: HIRGlobalValue):
        self.globalValues.append(globalValue)

    def enumerateGlobalValues(self):
        index = 0
        for globalValue in self.globalValues:
            globalValue.globalValueIndex = index
            index += 1

    def prettyPrint(self) -> str:
        self.enumerateGlobalValues()

        result = ''
        if self.entryPoint is not None:
            result += 'entryPoint: %s\n' % str(self.entryPoint)

        if len(result) != 0:
            result += '\n'

        for globalValue in self.globalValues:
            result += globalValue.fullPrintString()
        return result

class HIRModuleFrontend:
    def __init__(self) -> None:
        self.context = HIRContext()
        self.module = HIRModule(self.context)
        self.translatedValueDictionary = dict()
        self.translatedConstantValueDictionary = dict()
        self.runtimeDependencyChecker = GHIRRuntimeDependencyChecker()

        for baseType, targetType in [
            (UnitType, self.context.unitType),
            (Int8Type, self.context.int8Type),
            (Int16Type, self.context.int16Type),
            (Int32Type, self.context.int32Type),
            (Int64Type, self.context.int64Type),
            (Float32Type, self.context.float32Type),
            (Float64Type, self.context.float64Type),
            (FalseType, self.context.booleanType),
            (TrueType, self.context.booleanType),
            (BooleanType, self.context.booleanType),
        ]:
            self.translatedConstantValueDictionary[baseType] = targetType

    def compileGraphModule(self, graphModule: GHIRModule) -> HIRModule:
        if graphModule.entryPoint is not None:
            self.module.entryPoint = self.translateGraphValue(graphModule.entryPoint)
        return self.module

    def translateConstantTypedValue(self, typedValue: TypedValue) -> HIRValue:
        if typedValue in self.translatedConstantValueDictionary:
            return self.translatedConstantValueDictionary[typedValue]
        
        translatedValue = typedValue.acceptTypedValueVisitor(self)
        self.translatedConstantValueDictionary[typedValue] = translatedValue
        return translatedValue

    def translateGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        if graphValue in self.translatedValueDictionary:
            return self.translatedValueDictionary[graphValue]
        
        translatedValue = graphValue.accept(self)
        self.translatedValueDictionary[graphValue] = translatedValue
        return translatedValue
    
    def visitConstantValue(self, graphValue: GHIRConstantValue) -> HIRValue:
        return self.translateConstantTypedValue(graphValue.value)
    
    def visitPrimitiveFunction(self, value: GHIRPrimitiveFunction) -> HIRValue:
        return HIRConstantPrimitiveFunction(self.context, self.translateGraphValue(value.type), value.name, value.compileTimeImplementation)
    
    def visitPrimitiveIntegerValue(self, value: PrimitiveIntegerValue) -> HIRValue:
        return HIRConstantPrimitiveInteger(self.context, self.translatedConstantValueDictionary[value.type], value.value)

    def visitProductType(self, value: GHIRProductType) -> HIRValue:
        elements = list(map(self.translateGraphValue, value.elements))
        return HIRProductType(self.context, elements)

    def visitLambdaValue(self, graphValue: GHIRLambdaValue) -> HIRValue:
        lambdaType = self.translateGraphValue(graphValue.type)
        definition = self.translateGraphValue(graphValue.definition)
        captures = list(map(self.translateGraphValue, graphValue.captures))
        return HIRConstantLambda(self.context, lambdaType, captures, definition)

    def visitFunctionalDefinitionValue(self, graphValue: GHIRFunctionalDefinitionValue) -> HIRValue:
        hirDefinition = HIRFunctionalDefinition(self.context)
        self.translatedValueDictionary[graphValue] = hirDefinition
        self.module.addGlobalValue(hirDefinition)
        HIRFunctionalDefinitionFrontend(self).translateFunctionDefinitionInto(graphValue, hirDefinition)
        return hirDefinition
    
    def visitSimpleFunctionType(self, graphValue: GHIRSimpleFunctionType) -> HIRValue:
        hirFunctionType = HIRFunctionType(self.context)
        self.translatedValueDictionary[graphValue] = hirFunctionType
        hirFunctionType.argumentTypes = list(map(self.translateGraphValue, graphValue.arguments))
        hirFunctionType.resultType = self.translateGraphValue(graphValue.resultType)
        return hirFunctionType
    
class HIRFunctionalDefinitionFrontend:
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.context = moduleFrontend.context
        self.moduleFrontend = moduleFrontend
        self.functionalDefinition: HIRFunctionalDefinition = None
        self.localBindings = dict()
        self.builder: HIRBuilder = None
    
    def translateFunctionDefinitionInto(self, graphFunctionalDefinition: GHIRFunctionalDefinitionValue, hirDefinition: HIRFunctionalDefinition):
        self.functionalDefinition = hirDefinition
        for graphCapture in graphFunctionalDefinition.captures:
            capture = HIRFunctionalCaptureValue(self.context, self.moduleFrontend.translateGraphValue(graphCapture.type))
            self.localBindings[graphCapture] = capture
            self.functionalDefinition.captures.append(capture)

        for graphArgument in graphFunctionalDefinition.arguments:
            argument = HIRFunctionalArgumentValue(self.context, self.moduleFrontend.translateGraphValue(graphArgument.type), graphArgument.name)
            self.localBindings[graphArgument] = argument
            self.functionalDefinition.arguments.append(argument)

        self.builder = HIRBuilder(self.context, self.functionalDefinition)
        self.builder.beginNewBasicBlock('entry')

        resultValue = self.translateGraphValue(graphFunctionalDefinition.body)
        if not self.builder.isLastTerminator():
            self.builder.returnValue(resultValue)

    def translateGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        if graphValue in self.localBindings:
            return self.localBindings[graphValue]
        
        if not self.moduleFrontend.runtimeDependencyChecker.checkValue(graphValue):
            return self.moduleFrontend.translateGraphValue(graphValue)

        return graphValue.accept(self)

    def visitApplicationValue(self, application: GHIRApplicationValue) -> HIRValue:
        functional = self.translateGraphValue(application.functional)
        arguments = list(map(self.translateGraphValue, application.arguments))
        resultType = self.translateGraphValue(application.type)
        return self.builder.call(resultType, functional, arguments)
