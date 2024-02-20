from abc import ABC, abstractmethod
from .ghir import *

class HIRContext:
    def __init__(self, pointerSize = 8) -> None:
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

    def getTypeUniverse(self, index):
        if index not in self.typeUniverses:
            self.typeUniverses[index] = HIRTypeUniverse(self, index)
        return self.typeUniverses[index]

class HIRValue(ABC):
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    @abstractmethod
    def getType(self):
        pass

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

class HIRPrimitiveType(HIRTypeValue):
    def  __init__(self, context: HIRContext, name: str, size: int, alignment: int) -> None:
        super().__init__(context)
        self.name = name
        self.size = size
        self.alignment = alignment

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

    def __str__(self) -> str:
        result = '('
        for arg in self.argumentTypes:
            result += str(arg)
        result += '-> '
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

class HIRConstantPrimitive(HIRConstant):
    pass

class HIRConstantPrimitiveInteger(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: int) -> None:
        super().__init__(context, type)
        self.value = value

    def __str__(self) -> str:
        return '%s(%d)' % (str(self.type), self.value)

class HIRConstantPrimitiveFloat(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: float) -> None:
        super().__init__(context, type)
        self.value = value

    def __str__(self) -> str:
        return '%s(%f)' % (str(self.type), self.value)
    
class HIRGlobalValue(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context, type)
        self.name = None
        self.globalIndex = 0

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (self.name, self.globalIndex)
        return '@%d' % self.globalIndex
    
    def fullPrintString(self) -> str:
        return str(self)

class HIRFunctionalDefinition(HIRGlobalValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context, type)
        self.captures = []
        self.arguments = []
        self.firstBasicBlock: HIRBasicBlock = None
        self.lastBasicBlock: HIRBasicBlock = None

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
    
    def getType(self):
        return self.type

    def __str__(self) -> str:
        if self.name is not None:
            return '$%s|%d' % (self.name, self.localValueIndex)
        return '$%d' % self.localValueIndex

class HIRFunctionalCaptureValue(HIRFunctionalLocalValue):
    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRFunctionalArgumentValue(HIRFunctionalLocalValue):
    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRBasicBlock(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, context.basicBlockType, name)
        self.previousBasicBlock: HIRBasicBlock = None
        self.nextBasicBlock: HIRBasicBlock = None
        self.firstInstruction: HIRInstruction = None
        self.lastInstruction: HIRInstruction = None

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

class HIRInstruction(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.previousInstruction: HIRInstruction = None
        self.nextInstruction: HIRInstruction = None

class HIRTerminatorInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, context.unitType, name)
    
    def isTerminatorInstruction(self) -> bool:
        return True

class HIRReturnInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, result: HIRValue) -> None:
        super().__init__(context)
        self.result = result

    def fullPrintString(self) -> str:
        return 'return %s' % str(self.result)

class HIRConstantLambda(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRConstant, captures: list[HIRConstant], definition: HIRFunctionalDefinition) -> None:
        super().__init__(context, type)
        self.captures = captures
        self.definition = definition

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
    
    def returnValue(self, value) -> HIRInstruction:
        return self.addInstruction(HIRReturnInstruction(self.context, value))

class HIRModule(HIRValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.entryPoint: HIRValue = None
        self.globalValues: list[HIRGlobalValue] = []

    def getType(self):
        return None
    
    def addGlobalValue(self, globalValue: HIRGlobalValue):
        self.globalValues.append(globalValue)

    def enumerateGlobalValues(self):
        index = 0
        for globalValue in self.globalValues:
            globalValue.globalIndex = index
            index += 1

    def prettyPrint(self) -> str:
        self.enumerateGlobalValues()

        result = ''
        if self.entryPoint is not None:
            result += 'entryPoint: %s\n' % str(self.entryPoint)

        for globalValue in self.globalValues:
            result += globalValue.fullPrintString()
        return result

class HIRModuleFrontend:
    def __init__(self) -> None:
        self.context = HIRContext()
        self.module = HIRModule(self.context)
        self.translatedValueDictionary = dict()
        self.translatedConstantValueDictionary = dict()

        for baseType, targetType in [
            [UnitType, self.context.unitType],
            [Int8Type, self.context.int8Type],
            [Int16Type, self.context.int16Type],
            [Int32Type, self.context.int32Type],
            [Int64Type, self.context.int64Type],
            [Float32Type, self.context.float32Type],
            [Float64Type, self.context.float64Type],
            [FalseType, self.context.booleanType],
            [TrueType, self.context.booleanType],
            [BooleanType, self.context.booleanType],
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
    
    def visitPrimitiveIntegerValue(self, value: PrimitiveIntegerValue) -> HIRValue:
        return HIRConstantPrimitiveInteger(self.context, self.translatedConstantValueDictionary[value.type], value.value)

    def visitLambdaValue(self, graphValue: GHIRLambdaValue) -> HIRValue:
        lambdaType = self.translateGraphValue(graphValue.type)
        definition = self.translateGraphValue(graphValue.definition)
        captures = list(map(self.translateGraphValue, graphValue.captures))
        return HIRConstantLambda(self.context, lambdaType, captures, definition)

    def visitFunctionalDefinitionValue(self, graphValue: GHIRFunctionalDefinitionValue) -> HIRValue:
        hirDefinition = HIRFunctionalDefinition(self.context, None)
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
            argument = HIRFunctionalCaptureValue(self.context, self.moduleFrontend.translateGraphValue(graphArgument.type))
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
        
        return self.moduleFrontend.translateGraphValue(graphValue)

        