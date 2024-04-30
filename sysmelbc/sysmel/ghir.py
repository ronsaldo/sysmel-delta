from abc import ABC, abstractmethod

from .value import *
from .environment import *
from .ast import *

class GHIRContext:
    def __init__(self) -> None:
        self.constantValues = dict()
        self.simpleFunctionTypes = dict()
        self.dictionaryTypes = dict()
        self.productTypes = dict()
        self.sumTypes = dict()
        self.decoratedTypes = dict()
        self.arrayTypes = dict()
        self.pointerTypes = dict()
        self.refTypes = dict()
        self.tempRefTypes = dict()
        self.universeTypes = dict()

    def getConstantValue(self, value: TypedValue):
        if value in self.constantValues:
            return self.constantValues[value]
        
        constantValue = GHIRConstantValue(self, None, value)
        self.constantValues[value] = constantValue
        return constantValue
    
    def getFunctionType(self, type, argumentTypes, isVariadic: bool, resultType, callingConventionName: str = None):
        hashKey = (type, tuple(argumentTypes), isVariadic, resultType, callingConventionName)
        if hashKey in self.simpleFunctionTypes:
            return self.simpleFunctionTypes[hashKey]
        
        simpleFunctionType = GHIRSimpleFunctionType(self, None, type, argumentTypes, isVariadic, resultType, callingConventionName)
        self.simpleFunctionTypes[hashKey] = simpleFunctionType
        return simpleFunctionType

    def getDictionaryType(self, type, keyType, valueType):
        hashKey = (type, keyType, valueType)
        if hashKey in self.dictionaryTypes:
            return self.dictionaryTypes[hashKey]
        
        dictionaryType = GHIRDictionaryType(self, None, type, keyType, valueType)
        self.dictionaryTypes[hashKey] = dictionaryType
        return dictionaryType
    
    def getProductType(self, type, elements):
        hashKey = (type, tuple(elements))
        if hashKey in self.productTypes:
            return self.productTypes[hashKey]
        
        productType = GHIRProductType(self, None, type, elements)
        self.productTypes[hashKey] = productType
        return productType

    def getSumType(self, type, elements):
        hashKey = (type, tuple(elements))
        if hashKey in self.sumTypes:
            return self.sumTypes[hashKey]
        
        sumType = GHIRSumType(self, None, type, elements)
        self.sumTypes[hashKey] = sumType
        return sumType

    def getDecoratedType(self, type, baseType, decorations):
        hashKey = (type, baseType, decorations)
        if hashKey in self.decoratedTypes:
            return self.decoratedTypes[hashKey]
        
        decoratedType = GHIRDecoratedType(self, None, type, baseType, decorations)
        self.decoratedTypes[hashKey] = decoratedType
        return decoratedType

    def getArrayType(self, type, elementType, size):
        hashKey = (type, elementType, size)
        if hashKey in self.arrayTypes:
            return self.arrayTypes[hashKey]
        
        arrayType = GHIRArrayType(self, None, type, elementType, size)
        self.arrayTypes[hashKey] = arrayType
        return arrayType

    def getPointerType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.pointerTypes:
            return self.pointerTypes[hashKey]
        
        pointerType = GHIRPointerType(self, None, type, baseType)
        self.pointerTypes[hashKey] = pointerType
        return pointerType
    
    def getReferenceType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.refTypes:
            return self.refTypes[hashKey]
        
        refType = GHIRReferenceType(self, None, type, baseType)
        self.refTypes[hashKey] = refType
        return refType
    
    def getTemporaryReferenceType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.tempRefTypes:
            return self.tempRefTypes[hashKey]
        
        tempRefType = GHIRTemporaryReferenceType(self, None, type, baseType)
        self.tempRefTypes[hashKey] = tempRefType
        return tempRefType
    
    def getUniverse(self, index):
        if index in self.universeTypes:
            return self.universeTypes[index]
        
        universe = GHIRTypeUniverse(self, index)
        self.universeTypes[index] = universe
        return universe
    
class GHIRVisitor(ABC):
    @abstractmethod
    def visitAllocaMutableWithValueExpression(self, value):
        pass

    @abstractmethod
    def visitConstantValue(self, value):
        pass

    @abstractmethod
    def visitPrimitiveFunction(self, value):
        pass

    @abstractmethod
    def visitCurryingFunction(self, value):
        pass

    @abstractmethod
    def visitCurriedFunction(self, value):
        pass

    @abstractmethod
    def visitCaptureBindingValue(self, value):
        pass

    @abstractmethod
    def visitArgumentBindingValue(self, value):
        pass

    @abstractmethod
    def visitSimpleFunctionType(self, value):
        pass

    @abstractmethod
    def visitFunctionalDefinitionValue(self, value):
        pass

    @abstractmethod
    def visitLambdaValue(self, value):
        pass

    @abstractmethod
    def visitPiValue(self, value):
        pass

    @abstractmethod
    def visitSigmaValue(self, value):
        pass

    @abstractmethod
    def visitArrayType(self, value):
        pass

    @abstractmethod
    def visitDecoratedType(self, value):
        pass

    @abstractmethod
    def visitPointerType(self, value):
        pass

    @abstractmethod
    def visitReferenceType(self, value):
        pass

    @abstractmethod
    def visitTemporaryReferenceType(self, value):
        pass

    @abstractmethod
    def visitDictionaryType(self, value):
        pass

    @abstractmethod
    def visitProductType(self, value):
        pass

    @abstractmethod
    def visitSumType(self, value):
        pass

    @abstractmethod
    def visitSequenceExpression(self, value):
        pass

    @abstractmethod
    def visitArraySubscriptAtExpression(self, value):
        pass

    @abstractmethod
    def visitPointerLikeLoadExpression(self, value):
        pass

    @abstractmethod
    def visitPointerLikeStoreExpression(self, value):
        pass

    @abstractmethod
    def visitPointerLikeReinterpretExpression(self, value):
        pass

    @abstractmethod
    def visitPointerLikeSubscriptAtExpression(self, value):
        pass

    @abstractmethod
    def visitIfExpression(self, value):
        pass

    @abstractmethod
    def visitBreakExpression(self, value):
        pass

    @abstractmethod
    def visitContinueExpression(self, value):
        pass

    @abstractmethod
    def visitDoWhileExpression(self, value):
        pass

    @abstractmethod
    def visitWhileExpression(self, value):
        pass

    @abstractmethod
    def visitMakeDictionaryExpression(self, value):
        pass

    @abstractmethod
    def visitMakeTupleExpression(self, value):
        pass

    @abstractmethod
    def visitModifiedTupleExpression(self, value):
        pass

    @abstractmethod
    def visitTupleAtExpression(self, value):
        pass

    @abstractmethod
    def visitInjectSumExpression(self, value):
        pass

    @abstractmethod
    def visitApplicationValue(self, value):
        pass

    @abstractmethod
    def visitModule(self, value):
        pass

class GHIRValue(ABC):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition) -> None:
        self.context = context
        self.sourcePosition = sourcePosition
        self.userValues = []

    def getName(self) -> str:
        return None

    @abstractmethod
    def accept(self, visitor: GHIRVisitor):
        pass

    @abstractmethod
    def getType(self):
        pass

    @abstractmethod
    def fullPrintGraph(self, graphPrinter, valueName: str):
        pass
    
    def __str__(self) -> str:
        return GHIRGraphPrinter().printGraphWithValue(self)
    
    def prettyPrint(self) -> str:
        return GHIRGraphPrinter().printGraphWithValue(self)
    
    def isCurriedFunction(self) -> bool:
        return False

    def isCurryingFunction(self) -> bool:
        return False

    def isFunctionalDefinition(self) -> bool:
        return False

    def isCaptureless(self) -> bool:
        return True
    
    def isProductType(self) -> bool:
        return False

    def isMakeTupleExpression(self) -> bool:
        return False

    def isModifiedTupleExpression(self) -> bool:
        return True
    
    def hasArgumentDependency(self) -> bool:
        return False

    @abstractmethod
    def usedValues(self):
        return []

    @abstractmethod
    def replaceUsedValueWith(self, usedValue, replacement):
        pass

    def replacedUsedValueInListWith(self, list, usedValue, replacement):
        newList = []
        for element in list:
            if element is usedValue:
                newList.append(replacement)
                replacement.registerUserValue(self)
            else:
                newList.append(element)
        return newList

    def registerUserValue(self, userValue):
        if userValue not in self.userValues:
            self.userValues.append(userValue)

    def unregisterUserValue(self, userValue):
        if userValue in self.userValues:
            self.userValues.remove(userValue)

    def registerInUsedValues(self):
        for usedValue in self.usedValues():
            usedValue.registerUserValue(self)

    def replaceWith(self, replacement):
        for usedValue in self.usedValues():
            usedValue.unregisterUserValue(self)

        for userValue in self.userValues:
            userValue.replaceUsedValueWith(replacement)
        self.userValues = []
        return replacement
    
    def getUserCount(self) -> int:
        return len(self.userValues)
    
    def simplify(self):
        return self

class GHIRGraphPrinter:
    def __init__(self) -> None:
        self.result = ""
        self.valueCount = 0
        self.valueToNameDictionary = dict()

    def printValue(self, value: GHIRValue) -> str:
        if value is None: return 'None'
        if value in self.valueToNameDictionary:
            return self.valueToNameDictionary[value]
        
        valueUserName = value.getName()
        if valueUserName is not None:
            valueName = '$%d:%s' % (self.valueCount, valueUserName)
        else:
            valueName = '$%d' % self.valueCount
        self.valueCount += 1
        self.valueToNameDictionary[value] = valueName
        value.fullPrintGraph(self, valueName)
        return valueName

    def printLine(self, line):
        self.result += line
        self.result += '\n'    

    def printGraphWithValue(self, value) -> str:
        self.printValue(value)
        return self.result

class GHIRConstantValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(context, sourcePosition)
        self.value = value
        self.type = None

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitConstantValue(self)

    def getType(self) -> GHIRValue:
        if self.type is None:
            self.type = self.context.getConstantValue(self.value.getType())
            self.type.registerUserValue(self)
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := constant %s' % (valueName, self.value.prettyPrint()))

    def usedValues(self):
        if self.type is not None:
            yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

class GHIRPrimitiveFunction(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, name: str, compileTimeImplementation = None, isMacro = False, isPure = False) -> None:
        super().__init__(context, sourcePosition)
        assert type is not None
        self.type = type
        self.name = name
        self.compileTimeImplementation = compileTimeImplementation
        self.isMacro = isMacro
        self.isPure = isPure
        self.registerInUsedValues()

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPrimitiveFunction(self)

    def getType(self) -> GHIRValue:
        return self.type

    def getName(self) -> str:
        return self.name
    
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        graphPrinter.printLine('%s := primitive %s : %s' % (valueName, self.name, type))

    def usedValues(self):
        yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

class GHIRCurryingFunction(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, innerFunction: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.innerFunction = innerFunction
        self.registerInUsedValues()

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitCurryingFunction(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        innerFunction = graphPrinter.printValue(self.innerFunction)
        graphPrinter.printLine('%s := currying over %s' % (valueName, innerFunction))

    def isCurryingFunction(self) -> bool:
        return True

    def usedValues(self):
        yield self.type
        yield self.innerFunction

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.innerFunction is usedValue:
            self.innerFunction = replacement
            replacement.registerUserValue(self)

class GHIRCurriedFunction(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, innerFunction: GHIRValue, partialApplications: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.innerFunction = innerFunction
        self.partialApplications = partialApplications
        self.registerInUsedValues()

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitCurriedFunction(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        innerFunction = graphPrinter.printValue(self.innerFunction)
        partialApplicationList = ''
        for applicationValue in self.partialApplications:
            if len(partialApplicationList) != 0:
                partialApplicationList += ', '
            partialApplicationList += graphPrinter.printValue(applicationValue)

        graphPrinter.printLine('%s := currying %s with [%s]' % (valueName, innerFunction, partialApplicationList))

    def isCurriedFunction(self) -> bool:
        return True
    
    def usedValues(self):
        yield self.type
        yield self.innerFunction
        for argument in self.partialApplications:
            yield argument

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.innerFunction is usedValue:
            self.innerFunction = replacement
            replacement.registerUserValue(self)
        self.partialApplications = self.replacedUsedValueInListWith(self.partialApplications, usedValue, replacement)

class GHIRLocalBindingValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, name: str = None) -> None:
        super().__init__(context, sourcePosition)
        assert type is not None
        self.type = type
        self.name = name

    def getType(self) -> GHIRValue:
        return self.type

    def getName(self) -> str:
        return self.name

    def usedValues(self):
        yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
                                                                    
class GHIRCaptureBindingValue(GHIRLocalBindingValue):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitCaptureBindingValue(self)

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := capture %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRArgumentBindingValue(GHIRLocalBindingValue):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitArgumentBindingValue(self)

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := argument %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRTypeUniverse(GHIRValue):
    def __init__(self, context: GHIRContext, index) -> None:    
        super().__init__(context, None)
        self.index = index

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSimpleFunctionType(self)

    def getType(self) -> GHIRValue:
        return self.context.getUniverse(self.index + 1)

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := type%d' % (valueName, self.index))

    def usedValues(self):
        yield self.type
        for argument in self.arguments:
            yield argument
        yield self.resultType

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

        self.arguments = self.replacedUsedValueInListWith(self.arguments, usedValue, replacement)
        if self.resultType is usedValue:
            self.resultType = replacement
            replacement.registerUserValue(self)

class GHIRSimpleFunctionType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, arguments: list[GHIRValue], isVariadic: bool, resultType: GHIRValue, callingConvention: str = None) -> None:    
        super().__init__(context, sourcePosition)
        self.type = type
        self.arguments = arguments
        self.isVariadic = isVariadic
        self.resultType = resultType
        self.callingConvention = callingConvention

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSimpleFunctionType(self)

    def getType(self) -> GHIRValue:
        return None

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        argumentList = ''
        for argument in self.arguments:
            if len(argumentList) != 0:
                argumentList += ', '
            argumentList += graphPrinter.printValue(argument)
        if self.isVariadic:
            argumentList += '...'

        resultType = graphPrinter.printValue(self.resultType)
        conventionName = ''
        if self.callingConvention is not None:
            conventionName = self.callingConvention + ' '
        graphPrinter.printLine('%s := functionType %s[%s] -> %s : %s' % (valueName, conventionName, argumentList, resultType, type))

    def usedValues(self):
        yield self.type
        for argument in self.arguments:
            yield argument
        yield self.resultType

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

        self.arguments = self.replacedUsedValueInListWith(self.arguments, usedValue, replacement)
        if self.resultType is usedValue:
            self.resultType = replacement
            replacement.registerUserValue(self)

class GHIRFunctionalDefinitionValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, captures: list[GHIRCaptureBindingValue] = [], arguments: list[GHIRArgumentBindingValue] = [], isVariadic = False, body: GHIRValue = None) -> None:
        super().__init__(context, sourcePosition)
        self.captures = captures
        self.arguments = arguments
        self.isVariadic = isVariadic
        self.body = body

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitFunctionalDefinitionValue(self)

    def isFunctionalDefinition(self) -> bool:
        return True

    def isCaptureless(self) -> bool:
        return len(self.captures) == 0

    def hasArgumentDependency(self) -> bool:
        for argument in self.arguments:
            if argument.getUserCount() > 0:
                return True
        return False

    def getType(self) -> GHIRValue:
        return None

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        captureList = ''
        for capture in self.captures:
            if len(captureList) != 0:
                captureList += ', '
            captureList += graphPrinter.printValue(capture)

        argumentList = ''
        for argument in self.arguments:
            if len(argumentList) != 0:
                argumentList += ', '
            argumentList += graphPrinter.printValue(argument)
        if self.isVariadic:
            argumentList += '...'

        body = graphPrinter.printValue(self.body)
        graphPrinter.printLine('%s := definition captures [%s] arguments [%s] body %s' % (valueName, captureList, argumentList, body))

    def usedValues(self):
        for capture in self.captures:
            yield capture
        for argument in self.arguments:
            yield argument
        yield self.body

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        self.captures = self.replacedUsedValueInListWith(self.captures, usedValue, replacement)
        self.arguments = self.replacedUsedValueInListWith(self.arguments, usedValue, replacement)
        if self.body is usedValue:
            self.body = replacement
            replacement.registerUserValue(self)

class GHIRFunctionalValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, definition: GHIRFunctionalDefinitionValue = None, captures: list[GHIRValue] = [], callingConvention: str = None) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.definition = definition
        self.captures = captures
        self.callingConvention = callingConvention

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        definition = graphPrinter.printValue(self.definition)
        captureList = ''
        for capture in self.captures:
            if len(captureList) != 0:
                captureList += ', '
            captureList += graphPrinter.printValue(capture)

        graphPrinter.printLine('%s := %s %s captures [%s] : %s' % (valueName, self.getFunctionalValueKindName(), definition, captureList, type))

    @abstractmethod
    def getFunctionalValueKindName(self) -> str:
        pass

    def usedValues(self):
        yield self.type
        yield self.definition
        for capture in self.captures:
            yield capture

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.definition is usedValue:
            self.definition = replacement
            replacement.registerUserValue(self)
        self.captures = self.replacedUsedValueInListWith(self.captures, usedValue, replacement)

class GHIRLambdaValue(GHIRFunctionalValue):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitLambdaValue(self)

    def getFunctionalValueKindName(self) -> str:
        return 'lambda'

class GHIRPiValue(GHIRFunctionalValue):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPiValue(self)

    def getFunctionalValueKindName(self) -> str:
        return 'pi'
    
    def simplify(self):
        if self.definition.isFunctionalDefinition() and self.definition.isCaptureless() and not self.definition.hasArgumentDependency():
            argumentTypes = list(map(lambda arg: arg.getType(), self.definition.arguments))
            resultType = self.definition.body
            simpleFunctionType = self.context.getFunctionType(self.getType(), argumentTypes, self.definition.isVariadic, resultType, self.callingConvention)
            return self.replaceWith(simpleFunctionType)
        return super().simplify()

class GHIRSigmaValue(GHIRFunctionalValue):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSigmaValue(self)

    def getFunctionalValueKindName(self) -> str:
        return 'sigma'

    def simplify(self):
        if self.definition.isFunctionalDefinition() and self.definition.isCaptureless() and not self.definition.hasArgumentDependency():
            argumentTypes = list(map(lambda arg: arg.getType(), self.definition.arguments))
            resultType = self.definition.body
            productType = self.context.getProductType(self.getType(), argumentTypes + [resultType])
            return self.replaceWith(productType)
        return super().simplify()

class GHIRDictionaryType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, keyType: GHIRValue, valueType: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.keyType = keyType
        self.valueType = valueType

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitDictionaryType(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isDictionaryType(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        keyType = graphPrinter.printValue(self.keyType)
        valueType = graphPrinter.printValue(self.valueType)

        graphPrinter.printLine('%s := dictionaryType %s -> %s : %s' % (valueName, keyType, valueType, type))

    def usedValues(self):
        yield self.type
        yield self.keyType
        yield self.valueType

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.keyType is usedValue:
            self.keyType = replacement
            replacement.registerUserValue(self)
        if self.valueType is usedValue:
            self.valueType = replacement
            replacement.registerUserValue(self)

class GHIRProductType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.elements = elements

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitProductType(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isProductType(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        elementList = ''
        for element in self.elements:
            if len(elementList) != 0:
                elementList += ', '
            elementList += graphPrinter.printValue(element)

        graphPrinter.printLine('%s := productType [%s] : %s' % (valueName, elementList, type))

    def usedValues(self):
        yield self.type
        for element in self.elements:
            yield element

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        self.elements = self.replacedUsedValueInListWith(self.elements, usedValue, replacement)

class GHIRRecordType(GHIRProductType):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, name: str, elements: list[GHIRValue], fieldNames: list[str]) -> None:
        super().__init__(context, sourcePosition, type, elements)
        self.name = name
        self.fieldNames = fieldNames

class GHIRSumType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.elements = elements

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSumType(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        elementList = ''
        for element in self.elements:
            if len(elementList) != 0:
                elementList += ', '
            elementList += graphPrinter.printValue(element)

        graphPrinter.printLine('%s := sumType [%s] : %s' % (valueName, elementList, type))

    def usedValues(self):
        yield self.type
        for element in self.elements:
            yield element

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        self.elements = self.replacedUsedValueInListWith(self.elements, usedValue, replacement)

class GHIRArrayType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, elementType: GHIRValue, size: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.elementType = elementType
        self.size = size

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitArrayType(self)
    
    def getType(self) -> GHIRValue:
        return self.type

    def usedValues(self):
        yield self.type
        yield self.elementType
        yield self.size

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.elementType is usedValue:
            self.elementType = replacement
            replacement.registerUserValue(self)

        if self.size is usedValue:
            self.size = replacement
            replacement.registerUserValue(self)

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        elementType = graphPrinter.printValue(self.elementType)
        size = graphPrinter.printValue(self.size)
        graphPrinter.printLine('%s := array %s size %s : %s' % (valueName, size, elementType, type))

class GHIRDerivedType(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, baseType: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.baseType = baseType

    def getType(self) -> GHIRValue:
        return self.type

    def usedValues(self):
        yield self.type
        yield self.baseType

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.baseType is usedValue:
            self.baseType = replacement
            replacement.registerUserValue(self)

class GHIRDecoratedType(GHIRDerivedType):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, baseType: GHIRValue, decorations: int) -> None:
        super().__init__(context, sourcePosition, type, baseType)
        self.decorations = decorations

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitDecoratedType(self)
    
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        baseType = graphPrinter.printValue(self.baseType)
        graphPrinter.printLine('%s := decorated %s with %d : %s' % (valueName, baseType, self.decorations, type))

class GHIRPointerType(GHIRDerivedType):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPointerType(self)
    
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        baseType = graphPrinter.printValue(self.baseType)
        graphPrinter.printLine('%s := pointer %s : %s' % (valueName, baseType, type))

class GHIRReferenceType(GHIRDerivedType):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitReferenceType(self)
    
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        baseType = graphPrinter.printValue(self.baseType)
        graphPrinter.printLine('%s := ref %s : %s' % (valueName, baseType, type))

class GHIRTemporaryReferenceType(GHIRDerivedType):
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitTemporaryReferenceType(self)
    
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        baseType = graphPrinter.printValue(self.baseType)
        graphPrinter.printLine('%s := tempRef %s : %s' % (valueName, baseType, type))

class GHIRSequence(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, expressions: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.expressions = expressions

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSequenceExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        expressionList = ''
        for expression in self.expressions:
            if len(expressionList) != 0:
                expressionList += ', '
            expressionList += graphPrinter.printValue(expression)

        graphPrinter.printLine('%s := sequence [%s] : %s' % (valueName, expressionList, type))

    def usedValues(self):
        yield self.type
        for expression in self.expressions:
            yield expression

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        self.expressions = self.replacedUsedValueInListWith(self.expressions, usedValue, replacement)

class GHIRIfExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, condition: GHIRValue, trueExpression: GHIRValue, falseExpression: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.condition = condition
        self.trueExpression = trueExpression
        self.falseExpression = falseExpression

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitIfExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isIfExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        condition = graphPrinter.printValue(self.condition)
        trueExpression = graphPrinter.printValue(self.trueExpression)
        falseExpression = graphPrinter.printValue(self.falseExpression)
        graphPrinter.printLine('%s := if: %s then: %s else: %s : %s' % (valueName, condition, trueExpression, falseExpression, type))

    def usedValues(self):
        yield self.type
        yield self.condition
        yield self.trueExpression
        yield self.falseExpression

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.condition is usedValue:
            self.condition = replacement
            replacement.registerUserValue(self)
        if self.trueExpression is usedValue:
            self.trueExpression = replacement
            replacement.registerUserValue(self)
        if self.falseExpression is usedValue:
            self.falseExpression = replacement
            replacement.registerUserValue(self)

class GHIRBreakExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue):
        super().__init__(context, sourcePosition)
        self.type = type

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitBreakExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isBreakExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        graphPrinter.printLine('%s := break : %s' % (valueName, type))

    def usedValues(self):
        yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

class GHIRContinueExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue):
        super().__init__(context, sourcePosition)
        self.type = type

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitContinueExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isContinueExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        graphPrinter.printLine('%s := continue : %s' % (valueName, type))

    def usedValues(self):
        yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

class GHIRDoWhileExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, bodyExpression: GHIRValue, condition: GHIRValue, continueExpression: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.bodyExpression = bodyExpression
        self.condition = condition
        self.continueExpression = continueExpression

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitDoWhileExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isDoWhileExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        bodyExpression = graphPrinter.printValue(self.bodyExpression)
        condition = graphPrinter.printValue(self.condition)
        continueExpression = graphPrinter.printValue(self.continueExpression)
        graphPrinter.printLine('%s := do: %s while: %s continueWith: %s : %s' % (valueName, bodyExpression, condition, continueExpression, type))

    def usedValues(self):
        yield self.type
        yield self.bodyExpression
        yield self.condition
        yield self.continueExpression

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.bodyExpression is usedValue:
            self.bodyExpression = replacement
            replacement.registerUserValue(self)
        if self.condition is usedValue:
            self.condition = replacement
            replacement.registerUserValue(self)
        if self.continueExpression is usedValue:
            self.continueExpression = replacement
            replacement.registerUserValue(self)

class GHIRWhileExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, condition: GHIRValue, bodyExpression: GHIRValue, continueExpression: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.condition = condition
        self.bodyExpression = bodyExpression
        self.continueExpression = continueExpression

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitWhileExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isWhileExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        condition = graphPrinter.printValue(self.condition)
        bodyExpression = graphPrinter.printValue(self.bodyExpression)
        continueExpression = graphPrinter.printValue(self.continueExpression)
        graphPrinter.printLine('%s := while: %s do: %s continueWith: %s : %s' % (valueName, condition, bodyExpression, continueExpression, type))

    def usedValues(self):
        yield self.type
        yield self.condition
        yield self.bodyExpression
        yield self.continueExpression

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.condition is usedValue:
            self.condition = replacement
            replacement.registerUserValue(self)
        if self.bodyExpression is usedValue:
            self.bodyExpression = replacement
            replacement.registerUserValue(self)
        if self.continueExpression is usedValue:
            self.continueExpression = replacement
            replacement.registerUserValue(self)

class GHIRAllocaMutableWithValueExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, valueType: GHIRValue, initialValue: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.valueType = valueType
        self.initialValue = initialValue

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitAllocaMutableWithValueExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isAllocaMutableWithValueExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        valueType = graphPrinter.printValue(self.valueType)
        initialValue = graphPrinter.printValue(self.initialValue)
        graphPrinter.printLine('%s := alloca %s with %s : %s' % (valueName, valueType, initialValue, type))

    def usedValues(self):
        yield self.type
        yield self.valueType
        yield self.initialValue

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.valueType is usedValue:
            self.valueType = replacement
            replacement.registerUserValue(self)
        if self.initialValue is usedValue:
            self.initialValue = replacement
            replacement.registerUserValue(self)

class GHIRArraySubscriptAtExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, array: GHIRValue, index: GHIRValue, loadResult: bool) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.array = array
        self.index = index
        self.loadResult = loadResult

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitArraySubscriptAtExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isArraySubscriptAtLoadExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        array = graphPrinter.printValue(self.array)
        index = graphPrinter.printValue(self.index)
        if self.loadResult:
            graphPrinter.printLine('%s := array %s loadAt %s : %s' % (valueName, array, index, type))
        else:
            graphPrinter.printLine('%s := array %s at %s : %s' % (valueName, array, index, type))

    def usedValues(self):
        yield self.type
        yield self.array
        yield self.index

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.array is usedValue:
            self.array = replacement
            replacement.registerUserValue(self)
        if self.index is usedValue:
            self.index = replacement
            replacement.registerUserValue(self)

class GHIRPointerLikeLoadExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, pointer: GHIRValue, isVolatile: bool = False) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.pointer = pointer
        self.isVolatile = isVolatile

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPointerLikeLoadExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isPointerLikeLoadExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        pointer = graphPrinter.printValue(self.pointer)
        if self.isVolatile:
            graphPrinter.printLine('%s := volatile load %s : %s' % (valueName, pointer, type))
        else:
            graphPrinter.printLine('%s := load %s : %s' % (valueName, pointer, type))

    def usedValues(self):
        yield self.type
        yield self.pointer

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.pointer is usedValue:
            self.pointer = replacement
            replacement.registerUserValue(self)

class GHIRPointerLikeStoreExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, pointer: GHIRValue, value: GHIRValue, isVolatile: bool = False) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.pointer = pointer
        self.value = value
        self.isVolatile = isVolatile

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPointerLikeStoreExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isPointerLikeStoreExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        pointer = graphPrinter.printValue(self.pointer)
        value = graphPrinter.printValue(self.value)
        if self.isVolatile:
            graphPrinter.printLine('%s := volatile store %s in %s : %s' % (valueName, value, pointer, type))
        else:
            graphPrinter.printLine('%s := store %s in %s : %s' % (valueName, value, pointer, type))

    def usedValues(self):
        yield self.type
        yield self.pointer
        yield self.value

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.pointer is usedValue:
            self.pointer = replacement
            replacement.registerUserValue(self)
        if self.value is usedValue:
            self.value = replacement
            replacement.registerUserValue(self)

class GHIRPointerLikeReinterpretExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, pointer: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.pointer = pointer

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPointerLikeReinterpretExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isPointerLikeReinterpretExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        pointer = graphPrinter.printValue(self.pointer)
        graphPrinter.printLine('%s := pointerLikeReinterpret %s : %s' % (valueName, pointer, type))

    def usedValues(self):
        yield self.type
        yield self.pointer

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.pointer is usedValue:
            self.pointer = replacement
            replacement.registerUserValue(self)

class GHIRPointerLikeSubscriptAtExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, pointer: GHIRValue, index: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.pointer = pointer
        self.index = index

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitPointerLikeSubscriptAtExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isPointerLikeSubscriptAtLoadExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        pointer = graphPrinter.printValue(self.pointer)
        index = graphPrinter.printValue(self.index)
        graphPrinter.printLine('%s := pointer %s at %s : %s' % (valueName, pointer, index, type))

    def usedValues(self):
        yield self.type
        yield self.pointer
        yield self.index

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.pointer is usedValue:
            self.pointer = replacement
            replacement.registerUserValue(self)
        if self.index is usedValue:
            self.index = replacement
            replacement.registerUserValue(self)

class GHIRMakeDictionaryExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.elements = elements

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitMakeDictionaryExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isMakeDictionaryExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        elementList = ''
        for element in self.elements:
            if len(elementList) != 0:
                elementList += ', '
            elementList += graphPrinter.printValue(element)

        graphPrinter.printLine('%s := makeDictionary [%s] : %s' % (valueName, elementList, type))

    def usedValues(self):
        yield self.type
        for element in self.elements:
            yield element

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        self.elements = self.replacedUsedValueInListWith(self.elements, usedValue, replacement)

class GHIRMakeTupleExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.elements = elements
        self.registerInUsedValues()

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitMakeTupleExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isMakeTupleExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        elementList = ''
        for element in self.elements:
            if len(elementList) != 0:
                elementList += ', '
            elementList += graphPrinter.printValue(element)

        graphPrinter.printLine('%s := makeTuple [%s] : %s' % (valueName, elementList, type))

    def usedValues(self):
        yield self.type
        for element in self.elements:
            yield element

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        self.elements = self.replacedUsedValueInListWith(self.elements, usedValue, replacement)

class GHIRModifiedTupleExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, baseTuple: GHIRValue, elements: list[GHIRValue], elementIndices: list[int]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.baseTuple = baseTuple
        self.elements = elements
        self.elementIndices = elementIndices

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitModifiedTupleExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isModifiedTupleExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        baseTuple = graphPrinter.printValue(self.baseTuple)
        elementList = ''
        for i in range(len(self.elements)):
            element = self.elements[i]
            elementIndex = self.elementIndices[i]
            if len(elementList) != 0:
                elementList += ', '
            elementList += str(elementIndex)
            elementList += ': '
            elementList += graphPrinter.printValue(element)

        graphPrinter.printLine('%s := modifiedTuple %s [%s] : %s' % (valueName, baseTuple, elementList, type))

    def usedValues(self):
        yield self.type
        yield self.baseTuple
        for element in self.elements:
            yield element

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.baseTuple is usedValue:
            self.baseTuple = replacement
            replacement.registerUserValue(self)
        self.elements = self.replacedUsedValueInListWith(self.elements, usedValue, replacement)

class GHIRTupleAtExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, tuple: GHIRValue, index: int, loadResult: bool) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.tuple = tuple
        self.index = index
        self.loadResult = loadResult

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitTupleAtExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        tuple = graphPrinter.printValue(self.tuple)
        if self.loadResult:
            graphPrinter.printLine('%s := tuple %s loadAt %d : %s' % (valueName, tuple, self.index, type))
        else:
            graphPrinter.printLine('%s := tuple %s at %d : %s' % (valueName, tuple, self.index, type))

    def usedValues(self):
        yield self.type
        yield self.tuple

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.tuple is usedValue:
            self.tuple = replacement
            replacement.registerUserValue(self)

    def simplify(self):
        if self.loadResult:
            tupleExpression = self.tuple
            while tupleExpression.isMakeTupleExpression() or tupleExpression.isModifiedTupleExpression():
                if tupleExpression.isMakeTupleExpression():
                    element = tupleExpression.elements[self.index]
                    return self.replaceWith(element)
                else: 
                    assert tupleExpression.isModifiedTupleExpression()
                    if self.index in tupleExpression.elementIndices:
                        modifiedElementIndex = tupleExpression.elementIndices.index(self.index)
                        modifiedElement = tupleExpression.elements[modifiedElementIndex]
                        return self.replaceWith(modifiedElement)
                tupleExpression = tupleExpression.tuple
        return super().simplify()
    
class GHIRInjectSumExpression(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, variantIndex: int, value: GHIRValue) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.variantIndex = variantIndex
        self.value = value
        self.registerInUsedValues()

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitInjectSumExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def isInjectSumExpression(self) -> bool:
        return True

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        value = graphPrinter.printValue(self.type)
        graphPrinter.printLine('%s := injectSumAt %d with %s : %s' % (valueName, self.variantIndex, value, type))

    def usedValues(self):
        yield self.type
        yield self.value

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)

class GHIRApplicationValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, functional: GHIRValue, arguments: list[GHIRValue]) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.functional = functional
        self.arguments = arguments

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitApplicationValue(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        functional = graphPrinter.printValue(self.functional)
        argumentList = ''
        for argument in self.arguments:
            if len(argumentList) != 0:
                argumentList += ', '
            argumentList += graphPrinter.printValue(argument)

        graphPrinter.printLine('%s := apply %s [%s] : %s' % (valueName, functional, argumentList, type))

    def simplify(self):
        if len(self.arguments) == 0: return self
        if len(self.arguments) == 1:
            singleArgument = self.arguments[0]
            if singleArgument.isMakeTupleExpression():
                unpackedApplication = GHIRApplicationValue(self.context, self.sourcePosition, self.type, self.functional, singleArgument.elements)
                return self.replaceWith(unpackedApplication)

        if self.functional.isCurryingFunction():
            curryingFunction: GHIRCurryingFunction = self.functional
            curriedApplication = GHIRCurriedFunction(self.context, self.sourcePosition, self.type, curryingFunction.innerFunction, self.arguments)
            return self.replaceWith(curriedApplication.simplify())
        elif self.functional.isCurriedFunction():
            curriedApplication: GHIRCurriedFunction = self.functional
            uncurriedApplication = GHIRApplicationValue(self.context, self.sourcePosition, self.type, curriedApplication.innerFunction, curriedApplication.partialApplications + self.arguments)
            return self.replaceWith(uncurriedApplication.simplify())
        return self

    def usedValues(self):
        yield self.type
        yield self.functional
        for argument in self.arguments:
            yield argument

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            replacement.registerUserValue(self)
        if self.functional is usedValue:
            self.functional = replacement
            replacement.registerUserValue(self)
        self.arguments = self.replacedUsedValueInListWith(self.arguments, usedValue, replacement)

class GHIRImportedModule(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, name: str) -> None:
        super().__init__(context, sourcePosition)
        self.name = name

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitImportedModule(self)

    def getType(self) -> GHIRValue:
        return None

    def importValueWithType(self, name: str, type: GHIRValue):
        return GHIRImportedModuleValue(self.context, self, type, name)

    def usedValues(self):
        return []

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        pass
            
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := importedModule "%s"' % (valueName, self.name))

class GHIRImportedModuleValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, module: GHIRImportedModule, type: GHIRValue, name: str) -> None:
        super().__init__(context, sourcePosition)
        self.module = module
        self.type = type
        self.name = name
    
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitImportedModuleValue(self)

    def getType(self) -> GHIRValue:
        return None

    def usedValues(self):
        yield self.type
        yield self.module

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.module is usedValue:
            self.module = replacement
        if self.type is usedValue:
            self.type = replacement
            
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := from %s import %s : %s' % (valueName, graphPrinter.printValue(self.module), self.name, graphPrinter.printValue(self.type)))

class GHIRImportedExternalValue(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition, type: GHIRValue, externalName: str, name: str) -> None:
        super().__init__(context, sourcePosition)
        self.type = type
        self.externalName = externalName
        self.name = name
    
    def accept(self, visitor: GHIRVisitor):
        return visitor.visitImportedExternalValue(self)

    def getType(self) -> GHIRValue:
        return None

    def usedValues(self):
        yield self.type

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.type is usedValue:
            self.type = replacement
            
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := from external %s import %s : %s' % (valueName, self.externalName, self.name, graphPrinter.printValue(self.type)))

class GHIRModule(GHIRValue):
    def __init__(self, context: GHIRContext, sourcePosition: SourcePosition) -> None:
        self.context = context
        self.sourcePosition = sourcePosition
        self.exportedValues: list[tuple[str, GHIRValue]] = []
        self.entryPoint: GHIRValue = None
        self.name = ''

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitModule(self)

    def getType(self) -> GHIRValue:
        return None
    
    def exportValue(self, name: str, value: GHIRValue, externalName: str = None):
        self.exportedValues.append((name, value, externalName))

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        for name, value, externalName in self.exportedValues:
            if externalName is not None:
                graphPrinter.printLine('export "%s" external %s value: %s' % (name, externalName, graphPrinter.printValue(value)))
            else:
                graphPrinter.printLine('export "%s" value: %s' % (name, graphPrinter.printValue(value)))
        if self.entryPoint is not None:
            graphPrinter.printLine('module entryPoint: %s' % graphPrinter.printValue(self.entryPoint))
  
    def usedValues(self):
        if self.entryPoint is not None:
            yield self.entryPoint

    def replaceUsedValueWith(self, usedValue: GHIRValue, replacement: GHIRValue):
        if self.entryPoint is usedValue:
            self.entryPoint = replacement
            replacement.registerUserValue(self)

class GHIRModuleFrontend(TypedValueVisitor, ASTTypecheckedVisitor):
    def __init__(self, context = GHIRContext()) -> None:
        self.context = context
        self.ghirModule = GHIRModule(context, None)
        self.translatedValueDictionary = dict()
        self.translatedBindingValueDictionary = dict()

    def compileModule(self, module: Module):
        if module.name is not None:
            self.ghirModule.name = module.name.value

        for name, value, externalName in module.exportedValues:
            externalNameString = None
            if externalName is not None:
                externalNameString = externalName.value
            self.ghirModule.exportValue(name.value, self.translateValue(value), externalNameString)
        if module.entryPoint is not None:
            self.ghirModule.entryPoint = self.translateValue(module.entryPoint)
        return self.ghirModule

    def translateValue(self, value: TypedValue) -> GHIRValue:
        if value in self.translatedValueDictionary:
            return self.translatedValueDictionary[value]
        
        translatedValue = value.acceptTypedValueVisitor(self)
        self.translatedValueDictionary[value] = translatedValue
        return translatedValue
    
    def translateExpression(self, expression: ASTNode) -> GHIRValue:
        return expression.accept(self)
    
    def visitGenericTypedValue(self, value: TypedValue):
        return self.context.getConstantValue(value)

    def visitVoidTypeValue(self, value):
        return self.context.getConstantValue(value)

    def visitIntegerValue(self, value):
        return self.context.getConstantValue(value)

    def visitPrimitiveIntegerValue(self, value):
        return self.context.getConstantValue(value)

    def visitPrimitiveCharacterValue(self, value):
        return self.context.getConstantValue(value)

    def visitPrimitiveFloatValue(self, value):
        return self.context.getConstantValue(value)

    def visitStringDataValue(self, value):
        return self.context.getConstantValue(value)

    def visitSymbol(self, value):
        return self.context.getConstantValue(value)

    def visitLambdaValue(self, value: LambdaValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRLambdaValue(self.context, value.sourcePosition, type)
        if value.type.callingConvention is not None:
            translatedValue.callingConvention = value.type.callingConvention.value
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

    def visitPiValue(self, value: PiValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRPiValue(self.context, value.sourcePosition, type)
        if value.callingConvention is not None:
            translatedValue.callingConvention = value.callingConvention.value
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()
    
    def visitFunctionType(self, value: FunctionType):
        type = self.translateValue(value.getType())
        argumentType = self.translateValue(value.argumentType)
        resultType = self.translateValue(value.resultType)
        conventionName = None
        if value.callingConventionName is not None:
            conventionName = value.callingConventionName.value

        if argumentType.isProductType():
            return self.context.getFunctionType(type, argumentType.elements, value.isVariadic, resultType, conventionName)
        else:
            return self.context.getFunctionType(type, [argumentType], value.isVariadic, resultType, conventionName)

    def visitSigmaValue(self, value: SigmaValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRSigmaValue(self.context, value.sourcePosition, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

    def visitProductTypeValue(self, value: ProductTypeValue):
        type = self.translateValue(value.type)
        elements = list(map(self.translateValue, value.elements))
        return GHIRMakeTupleExpression(self.context, None, type, elements).simplify()

    def visitRecordTypeValue(self, value: ProductTypeValue):
        type = self.translateValue(value.type)
        recordValue = GHIRMakeTupleExpression(self.context, None, type, [])
        self.translatedValueDictionary[value] = recordValue
        recordValue.elements = list(map(self.translateValue, value.elements))
        self.registerInUsedValues()
        return recordValue.simplify()

    def visitPrimitiveFunction(self, value: PrimitiveFunction):
        type = self.translateValue(value.type)
        return GHIRPrimitiveFunction(self.context, None, type, self.optionalSymbolToString(value.primitiveName), value.value, isMacro = value.isMacro, isPure = value.isPure)

    def visitCurriedFunctionalValue(self, value: CurriedFunctionalValue):
        type = self.translateValue(value.type)
        innerFunction = self.translateValue(value.innerFunction)
        arguments = list(map(lambda arg: self.translateValue(arg), list(value.arguments)))
        return GHIRCurriedFunction(self.context, None, type, innerFunction, arguments).simplify()

    def visitCurryingFunctionalValue(self, value:  CurryingFunctionalValue):
        innerFunction = self.translateValue(value.innerFunction)
        type = self.translateValue(value.type)
        return GHIRCurryingFunction(self.context, None, type, innerFunction).simplify()

    def visitDictionaryType(self, value: DictionaryType):
        type = self.translateValue(value.getType())
        keyType = self.translateValue(value.keyType)
        valueType = self.translateValue(value.valueType)
        return self.context.getDictionaryType(type, keyType, valueType)

    def visitProductType(self, value: ProductType):
        type = self.translateValue(value.getType())
        elementTypes = list(map(self.translateValue, value.elementTypes))
        return self.context.getProductType(type, elementTypes)
    
    def visitRecordType(self, value: RecordType):
        type = self.translateValue(value.getType())
        recordType = GHIRRecordType(self.context, None, type, value.name, [], [])
        self.translatedValueDictionary[value] = recordType
        elementTypes = list(map(self.translateValue, value.elementTypes))
        recordType.elements = elementTypes
        recordType.fieldNames = list(map(self.optionalSymbolToString, value.fields))
        return recordType.simplify()

    def visitSumType(self, value):
        type = self.translateValue(value.getType())
        variantTypes = list(map(self.translateValue, value.variantTypes))
        return self.context.getSumType(type, variantTypes)

    def visitDecoratedType(self, value: DecoratedType):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        return self.context.getDecoratedType(type, baseType, value.decorations)

    def visitArrayType(self, value: ArrayType):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        size = self.context.getConstantValue(PrimitiveIntegerValue(SizeType, value.size))
        return self.context.getArrayType(type, baseType, size)

    def visitPointerType(self, value: PointerType):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        return self.context.getPointerType(type, baseType)

    def visitReferenceType(self, value):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        return self.context.getReferenceType(type, baseType)

    def visitTemporaryReferenceType(self, value):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        return self.context.getTemporaryReferenceType(type, baseType)

    def translateFunctionalValueDefinition(self, functionalValue: FunctionalValue) -> GHIRFunctionalDefinitionValue:
        captures = list(map(self.translateCaptureBinding, functionalValue.captureBindings))
        arguments = list(map(self.translateArgumentBinding, functionalValue.argumentBindings))
        body = self.translateExpression(functionalValue.body)
        return GHIRFunctionalDefinitionValue(self.context, functionalValue.sourcePosition, captures, arguments, functionalValue.isVariadic, body).simplify()
    
    def visitImportedModuleValue(self, value: ImportedModuleValue):
        type: GHIRValue = self.translateValue(value.type)
        module: GHIRImportedModule = self.translateValue(value.module)
        name: str = value.name.value
        return module.importValueWithType(name, type)
    
    def visitImportedExternalValue(self, value: ImportedExternalValue):
        type: GHIRValue = self.translateValue(value.type)
        externalName: str = value.externalName.value
        name: str = value.name.value
        return GHIRImportedExternalValue(self.context, None, type, externalName, name)

    def visitImportedModule(self, value: ImportedModule):
        return GHIRImportedModule(self.context, None, value.name.value)

    def translateCaptureBinding(self, binding: SymbolCaptureBinding) -> GHIRCaptureBindingValue:
        type = self.translateExpression(binding.getTypeExpression())
        bindingValue = GHIRCaptureBindingValue(self.context, binding.sourcePosition, type, self.optionalSymbolToString(binding.name))
        self.translatedBindingValueDictionary[binding] = bindingValue
        return bindingValue

    def translateArgumentBinding(self, binding: SymbolArgumentBinding) -> GHIRArgumentBindingValue:
        type = self.translateExpression(binding.getTypeExpression())
        bindingValue = GHIRArgumentBindingValue(self.context, binding.sourcePosition, type, self.optionalSymbolToString(binding.name))
        self.translatedBindingValueDictionary[binding] = bindingValue
        return bindingValue
    
    def translateArgumentNode(self, node: ASTTypedArgumentNode) -> GHIRArgumentBindingValue:
        return self.translateArgumentBinding(node.binding)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> TypedValue:
        return self.translateValue(node.value)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        assert False

    def visitDecoratedTypeNode(self, node: ASTDecoratedTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        baseType = self.translateExpression(node.baseType)
        return GHIRDecoratedType(self.context, node.sourcePosition, type, baseType, node.decorations).simplify()

    def visitPointerTypeNode(self, node: ASTPointerTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        baseType = self.translateExpression(node.baseType)
        return GHIRPointerType(self.context, node.sourcePosition, type, baseType).simplify()

    def visitReferenceTypeNode(self, node: ASTReferenceTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        baseType = self.translateExpression(node.baseType)
        return GHIRReferenceType(self.context, node.sourcePosition, type, baseType).simplify()

    def visitTemporaryReferenceTypeNode(self, node: ASTTemporaryReferenceTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        baseType = self.translateExpression(node.baseType)
        return GHIRTemporaryReferenceType(self.context, node.sourcePosition, type, baseType).simplify()

    def visitArrayTypeNode(self, node: ASTArrayTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elementType = self.translateExpression(node.elementType)
        size = self.translateExpression(node.size)
        return GHIRArrayType(self.context, node.sourcePosition, type, elementType, size).simplify()

    def visitDictionaryTypeNode(self, node: ASTDictionaryTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        keyType = self.translateExpression(node.keyType)
        valueType = self.translateExpression(node.valueType)
        return GHIRDictionaryType(self.context, node.sourcePosition, type, keyType, valueType).simplify()

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elements = list(map(self.translateExpression, node.elementTypes))
        return GHIRProductType(self.context, node.sourcePosition, type, elements).simplify()
    
    def visitRecordTypeNode(self, node: ASTRecordTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elements = list(map(self.translateExpression, node.elementTypes))
        fieldNames = list(map(self.optionalSymbolToString, node.fieldNames))
        return GHIRRecordType(self.context, node.sourcePosition, type, self.optionalSymbolToString(node.name), elements, fieldNames).simplify()

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elements = list(map(self.translateExpression, node.alternativeTypes))
        return GHIRSumType(self.context, node.sourcePosition, type, elements).simplify()
    
    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
        assert False

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.translateExpression(node.functional)
        argument = self.translateExpression(node.argument)
        type = self.translateExpression(node.type)
        return GHIRApplicationValue(self.context, node.sourcePosition, type, functional, [argument]).simplify()

    def visitTypedAllocaMutableWithValueNode(self, node: ASTTypedAllocaMutableWithValueNode):
        type = self.translateExpression(node.type)
        valueType = self.translateExpression(node.valueType)
        initialValue = self.translateExpression(node.initialValue)

        return GHIRAllocaMutableWithValueExpression(self.context, node.sourcePosition, type, valueType, initialValue).simplify()

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        assert False

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        assert False

    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode) -> TypedValue:
        type = self.translateExpression(node.type)
        argumentType = self.translateExpression(node.argumentType)
        resultType = self.translateExpression(node.resultType)
        return self.context.getFunctionType(type, [argumentType], resultType)

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        type = self.translateExpression(node.type)
        captureBindings = list(map(self.translateCaptureBinding, node.captureBindings))
        argumentBindings = list(map(self.translateArgumentNode, node.arguments))
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, node.sourcePosition, captureBindings, argumentBindings, node.isVariadic, body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRPiValue(self.context, node.sourcePosition, type, functionDefinition, capturedValues).simplify()

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        type = self.translateExpression(node.type)
        captureBindings = list(map(self.translateCaptureBinding, node.captureBindings))
        argumentBindings = list(map(self.translateArgumentNode, node.arguments))
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, node.sourcePosition, captureBindings, argumentBindings, node.isVariadic, body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRSigmaValue(self.context, node.sourcePosition, type, functionDefinition, capturedValues).simplify()

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.translatedBindingValueDictionary[node.binding]

    def visitTypedIfNode(self, node: ASTTypedIfNode) -> TypedValue:
        type = self.translateExpression(node.type)
        condition = self.translateExpression(node.condition)
        trueExpression = self.translateExpression(node.trueExpression)
        falseExpression = self.translateExpression(node.falseExpression)
        return GHIRIfExpression(self.context, node.sourcePosition, type, condition, trueExpression, falseExpression).simplify()

    def visitTypedBreakNode(self, node: ASTTypedBreakNode) -> TypedValue:
        type = self.translateExpression(node.type)
        return GHIRBreakExpression(self.context, node.sourcePosition, type)

    def visitTypedContinueNode(self, node: ASTTypedContinueNode) -> TypedValue:
        type = self.translateExpression(node.type)
        return GHIRContinueExpression(self.context, node.sourcePosition, type)

    def visitTypedDoWhileNode(self, node: ASTTypedDoWhileNode) -> TypedValue:
        type = self.translateExpression(node.type)
        bodyExpression = self.translateExpression(node.bodyExpression)
        condition = self.translateExpression(node.condition)
        continueExpression = self.translateExpression(node.continueExpression)
        return GHIRDoWhileExpression(self.context, node.sourcePosition, type, bodyExpression, condition, continueExpression).simplify()

    def visitTypedWhileNode(self, node: ASTTypedWhileNode) -> TypedValue:
        type = self.translateExpression(node.type)
        condition = self.translateExpression(node.condition)
        bodyExpression = self.translateExpression(node.bodyExpression)
        continueExpression = self.translateExpression(node.continueExpression)
        return GHIRWhileExpression(self.context, node.sourcePosition, type, condition, bodyExpression, continueExpression).simplify()

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.translateExpression(node.type)
        captureBindings = list(map(self.translateCaptureBinding, node.captureBindings))
        argumentBindings = list(map(self.translateArgumentNode, node.arguments))
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, node.sourcePosition, captureBindings, argumentBindings, node.isVariadic, body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRLambdaValue(self.context, node.sourcePosition, type, functionDefinition, capturedValues).simplify()

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return self.translateValue(node.value)

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode) -> TypedValue:
        value = self.translateExpression(node.valueExpression)
        self.translatedBindingValueDictionary[node.binding] = value
        return value

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode) -> TypedValue:
        assert False

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode) -> TypedValue:
        type = self.translateExpression(node.type)
        expressions = list(map(self.translateExpression, node.elements))
        return GHIRSequence(self.context, node.sourcePosition, type, expressions).simplify()

    def visitTypedArraySubscriptAtNode(self, node: ASTTypedArraySubscriptAtNode):
        type = self.translateExpression(node.type)
        array = self.translateExpression(node.array)
        index = self.translateExpression(node.index)
        return GHIRArraySubscriptAtExpression(self.context, node.sourcePosition, type, array, index, node.loadResult)

    def visitTypedPointerLikeLoadNode(self, node: ASTTypedPointerLikeLoadNode):
        type = self.translateExpression(node.type)
        pointer = self.translateExpression(node.pointer)
        return GHIRPointerLikeLoadExpression(self.context, node.sourcePosition, type, pointer, isVolatile = node.isVolatile).simplify()

    def visitTypedPointerLikeStoreNode(self, node: ASTTypedPointerLikeStoreNode):
        type = self.translateExpression(node.type)
        pointer = self.translateExpression(node.pointer)
        value = self.translateExpression(node.value)
        store = GHIRPointerLikeStoreExpression(self.context, node.sourcePosition, self.translateValue(VoidType), pointer, value, isVolatile = node.isVolatile).simplify()
        if node.returnPointer:
            return GHIRSequence(self.context, node.sourcePosition, type, [store, pointer]).simplify()
        else:
            return GHIRSequence(self.context, node.sourcePosition, type, [store, value]).simplify()

    def visitTypedPointerLikeReinterpretToNode(self, node: ASTTypedPointerLikeReinterpretToNode):
        type = self.translateExpression(node.type)
        pointer = self.translateExpression(node.pointer)
        return GHIRPointerLikeReinterpretExpression(self.context, node.sourcePosition, type, pointer)
    
    def visitTypedPointerLikeSubscriptAtNode(self, node: ASTTypedPointerLikeSubscriptAtNode):
        type = self.translateExpression(node.type)
        pointer = self.translateExpression(node.pointer)
        index = self.translateExpression(node.index)
        return GHIRPointerLikeSubscriptAtExpression(self.context, node.sourcePosition, type, pointer, index)

    def visitTypedDictionaryNode(self, node: ASTTypedDictionaryNode) -> TypedValue:
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression, node.elements))
        return GHIRMakeDictionaryExpression(self.context, node.sourcePosition, type, elements).simplify()

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression, node.elements))
        return GHIRMakeTupleExpression(self.context, node.sourcePosition, type, elements).simplify()

    def visitTypedModifiedTupleNode(self, node: ASTTypedModifiedTupleNode) -> TypedValue:
        type = self.translateExpression(node.type)
        baseTuple = self.translateExpression(node.baseTuple)
        elements = list(map(self.translateExpression, node.elements))
        return GHIRModifiedTupleExpression(self.context, node.sourcePosition, type, baseTuple, elements, node.elementIndices).simplify()

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode) -> TypedValue:
        type = self.translateExpression(node.type)
        tuple = self.translateExpression(node.tuple)
        return GHIRTupleAtExpression(self.context, node.sourcePosition, type, tuple, node.index, node.loadResult).simplify()

    def visitTypedInjectSumNode(self, node: ASTTypedInjectSumNode) -> TypedValue:
        type = self.translateExpression(node.type)
        value = self.translateExpression(node.value)
        return GHIRInjectSumExpression(self.context, node.sourcePosition, type, node.variantIndex, value).simplify()

    def visitTypedFromModuleImportNode(self, node):
        assert False

    def visitTypedFromExternalImportWithTypeNode(self, node):
        assert False

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        assert False

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        assert False

    def optionalSymbolToString(self, symbol: Symbol) -> str:
        if symbol is None: return None
        return symbol.value

class GHIRRuntimeDependencyChecker(GHIRVisitor):
    def __init__(self) -> None:
        self.dfsState = dict()

    def checkValue(self, value: GHIRValue):
        if value in self.dfsState:
            cacheResult = self.dfsState[value]
            return cacheResult is not False

        self.dfsState[value] = None
        result = value.accept(self)
        self.dfsState[value] = result
        return result
    
    def visitAllocaMutableWithValueExpression(self, value: GHIRAllocaMutableWithValueExpression):
        return True

    def visitConstantValue(self, value: GHIRConstantValue):
        return False

    def visitPrimitiveFunction(self, value: GHIRPrimitiveFunction):
        return False

    def visitCurryingFunction(self, value: GHIRCurryingFunction):
        return self.checkValue(value.innerFunction)

    def visitCurriedFunction(self, value: GHIRCurriedFunction):
        if self.checkValue(value.innerFunction):
            return True
        
        for partialApplication in value.partialApplications:
            if self.checkValue(partialApplication):
                return True

        return False

    def visitCaptureBindingValue(self, value: GHIRCaptureBindingValue):
        return True

    def visitArgumentBindingValue(self, value: GHIRArgumentBindingValue):
        return True

    def visitSimpleFunctionType(self, value: GHIRSimpleFunctionType):
        for argument in value.arguments:
            if self.checkValue(argument):
                return True
        return self.checkValue(value.resultType)

    def visitFunctionalDefinitionValue(self, value: GHIRFunctionalDefinitionValue):
        return False

    def visitFunctionalValue(self, value: GHIRFunctionalValue):
        for capture in value.captures:
            if self.checkValue(capture):
                return True
        return self.checkValue(value.definition)

    def visitLambdaValue(self, value: GHIRLambdaValue):
        return self.visitFunctionalValue(value)

    def visitPiValue(self, value: GHIRPiValue):
        return self.visitFunctionalValue(value)

    def visitSigmaValue(self, value: GHIRSigmaValue):
        return self.visitFunctionalValue(value)

    def visitArrayType(self, value: GHIRArrayType):
        return self.checkValue(value.elementType) or self.checkValue(value.size)

    def visitDictionaryType(self, value: GHIRProductType):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitProductType(self, value: GHIRProductType):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitSumType(self, value: GHIRSumType):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitDerivedType(self, value: GHIRDerivedType):
        return self.checkValue(value.baseType)

    def visitDecoratedType(self, value: GHIRDecoratedType):
        return self.visitDerivedType(value)

    def visitPointerType(self, value: GHIRPointerType):
        return self.visitDerivedType(value)

    def visitReferenceType(self, value: GHIRReferenceType):
        return self.visitDerivedType(value)

    def visitTemporaryReferenceType(self, value: GHIRTemporaryReferenceType):
        return self.visitDerivedType(value)
    
    def visitArraySubscriptAtExpression(self, value: GHIRArraySubscriptAtExpression):
        return self.checkValue(value.array) or self.checkValue(value.index)

    def visitPointerLikeLoadExpression(self, value: GHIRPointerLikeLoadExpression):
        return True

    def visitPointerLikeStoreExpression(self, value: GHIRPointerLikeStoreExpression):
        return True

    def visitPointerLikeReinterpretExpression(self, value: GHIRPointerLikeReinterpretExpression):
        return self.checkValue(value.pointer)

    def visitPointerLikeSubscriptAtExpression(self, value: GHIRPointerLikeSubscriptAtExpression):
        return self.checkValue(value.pointer) or self.checkValue(value.index)

    def visitSequenceExpression(self, value: GHIRSequence):
        for expression in value.expressions:
            if self.checkValue(expression):
                return True
        return False

    def visitIfExpression(self, value: GHIRIfExpression):
        return self.checkValue(value.condition) or self.checkValue(value.trueExpression) or self.checkValue(value.falseExpression)
    
    def visitBreakExpression(self, value: GHIRBreakExpression):
        return True

    def visitContinueExpression(self, value: GHIRContinueExpression):
        return True

    def visitDoWhileExpression(self, value: GHIRDoWhileExpression):
        return self.checkValue(value.bodyExpression) or self.checkValue(value.condition) or self.checkValue(value.continueExpression)

    def visitWhileExpression(self, value: GHIRWhileExpression):
        return self.checkValue(value.condition) or self.checkValue(value.bodyExpression) or self.checkValue(value.continueExpression)

    def visitMakeDictionaryExpression(self, value: GHIRMakeDictionaryExpression):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitMakeTupleExpression(self, value: GHIRMakeTupleExpression):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitModifiedTupleExpression(self, value: GHIRModifiedTupleExpression):
        if self.checkValue(value.baseTuple):
            return True
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

    def visitTupleAtExpression(self, value: GHIRTupleAtExpression):
        return self.checkValue(value.tuple)

    def visitInjectSumExpression(self, value: GHIRInjectSumExpression):
        return self.checkValue(value.value)

    def visitApplicationValue(self, value: GHIRApplicationValue):
        return True

    def visitModule(self, value: GHIRModule):
        return False

    def visitImportedModule(self, value: GHIRImportedModule):
        return False

    def visitImportedModuleValue(self, value: GHIRImportedModuleValue):
        return self.checkValue(value.module) or self.checkValue(value.type)
    
    def visitImportedExternalValue(self, value: GHIRImportedExternalValue):
        return self.checkValue(value.type)
