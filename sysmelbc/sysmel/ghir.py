from abc import ABC, abstractmethod
from .value import *
from .environment import *
from .ast import *

class GHIRContext:
    def __init__(self) -> None:
        self.constantValues = dict()
        self.simpleFunctionTypes = dict()
        self.productTypes = dict()
        self.sumTypes = dict()
        self.decoratedTypes = dict()
        self.pointerTypes = dict()
        self.refTypes = dict()
        self.tempRefTypes = dict()
        self.universeTypes = dict()

    def getConstantValue(self, value: TypedValue):
        if value in self.constantValues:
            return self.constantValues[value]
        
        constantValue = GHIRConstantValue(self, value)
        self.constantValues[value] = constantValue
        return constantValue
    
    def getFunctionType(self, type, argumentTypes, resultType, callingConventionName: str = None):
        hashKey = (type, tuple(argumentTypes), resultType, callingConventionName)
        if hashKey in self.simpleFunctionTypes:
            return self.simpleFunctionTypes[hashKey]
        
        simpleFunctionType = GHIRSimpleFunctionType(self, type, argumentTypes, resultType, callingConventionName)
        self.simpleFunctionTypes[hashKey] = simpleFunctionType
        return simpleFunctionType

    def getProductType(self, type, elements):
        hashKey = (type, tuple(elements))
        if hashKey in self.productTypes:
            return self.productTypes[hashKey]
        
        productType = GHIRProductType(self, type, elements)
        self.productTypes[hashKey] = productType
        return productType

    def getSumType(self, type, elements):
        hashKey = (type, tuple(elements))
        if hashKey in self.sumTypes:
            return self.sumTypes[hashKey]
        
        sumType = GHIRSumType(self, type, elements)
        self.sumTypes[hashKey] = sumType
        return sumType

    def getDecoratedType(self, type, baseType, decorations):
        hashKey = (type, baseType, decorations)
        if hashKey in self.decoratedTypes:
            return self.decoratedTypes[hashKey]
        
        decoratedType = GHIRDecoratedType(self, type, baseType, decorations)
        self.decoratedTypes[hashKey] = decoratedType
        return decoratedType

    def getPointerType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.pointerTypes:
            return self.pointerTypes[hashKey]
        
        pointerType = GHIRPointerType(self, type, baseType)
        self.pointerTypes[hashKey] = pointerType
        return pointerType
    
    def getReferenceType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.refTypes:
            return self.refTypes[hashKey]
        
        refType = GHIRReferenceType(self, type, baseType)
        self.refTypes[hashKey] = refType
        return refType
    
    def getTemporaryReferenceType(self, type, baseType):
        hashKey = (type, baseType)
        if hashKey in self.tempRefTypes:
            return self.tempRefTypes[hashKey]
        
        tempRefType = GHIRTemporaryReferenceType(self, type, baseType)
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
    def visitProductType(self, value):
        pass

    @abstractmethod
    def visitSumType(self, value):
        pass

    @abstractmethod
    def visitSequence(self, value):
        pass

    @abstractmethod
    def visitMakeTupleExpression(self, value):
        pass

    @abstractmethod
    def visitApplicationValue(self, value):
        pass

    @abstractmethod
    def visitModule(self, value):
        pass

class GHIRValue(ABC):
    def __init__(self, context: GHIRContext) -> None:
        self.context = context
        self.userValues = []

    def getName(self) -> str | None:
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

    def registerInUsedValues(self):
        for usedValue in self.usedValues():
            usedValue.registerUserValue(self)

    def replaceWith(self, replacement):
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

    def printValue(self, value: GHIRValue | None) -> str:
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
    def __init__(self, context: GHIRContext, value: TypedValue) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, name: str, compileTimeImplementation = None) -> None:
        super().__init__(context)
        assert type is not None
        self.type = type
        self.name = name
        self.compileTimeImplementation = compileTimeImplementation
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
    def __init__(self, context: GHIRContext, type: GHIRValue, innerFunction: GHIRValue) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, innerFunction: GHIRValue, partialApplications: list[GHIRValue]) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, name: str = None) -> None:
        super().__init__(context)
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
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, arguments: list[GHIRValue], resultType: GHIRValue, callingConvention: str | None = None) -> None:    
        super().__init__(context)
        self.type = type
        self.arguments = arguments
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
    def __init__(self, context: GHIRContext, captures: list[GHIRCaptureBindingValue] = [], arguments: list[GHIRArgumentBindingValue] = [], body: GHIRValue = None) -> None:
        super().__init__(context)
        self.captures = captures
        self.arguments = arguments
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
    def __init__(self, context: GHIRContext, type: GHIRValue, definition: GHIRFunctionalDefinitionValue = None, captures: list[GHIRValue] = [], callingConvention: str = None) -> None:
        super().__init__(context)
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
            simpleFunctionType = self.context.getFunctionType(self.getType(), argumentTypes, resultType, self.callingConvention)
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

class GHIRProductType(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context)
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

class GHIRSumType(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context)
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

class GHIRDerivedType(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, baseType: GHIRValue) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, baseType: GHIRValue, decorations: int) -> None:
        super().__init__(context, type, baseType)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, expressions: list[GHIRValue]) -> None:
        super().__init__(context)
        self.type = type
        self.expressions = expressions

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitSequence(self)

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

class GHIRMakeTupleExpression(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context)
        self.type = type
        self.elements = elements

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

class GHIRTupleAtExpression(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, tuple: GHIRValue, index: int) -> None:
        super().__init__(context)
        self.type = type
        self.tuple = tuple
        self.index = index

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitTupleAtExpression(self)

    def getType(self) -> GHIRValue:
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        type = graphPrinter.printValue(self.type)
        tuple = graphPrinter.printValue(self.tuple)
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

class GHIRApplicationValue(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, functional: GHIRValue, arguments: list[GHIRValue]) -> None:
        super().__init__(context)
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
                unpackedApplication = GHIRApplicationValue(self.context, self.type, self.functional, singleArgument.elements)
                return self.replaceWith(unpackedApplication)

        if self.functional.isCurryingFunction():
            curryingFunction: GHIRCurryingFunction = self.functional
            curriedApplication = GHIRCurriedFunction(self.context, self.type, curryingFunction.innerFunction, self.arguments)
            return self.replaceWith(curriedApplication.simplify())
        elif self.functional.isCurriedFunction():
            curriedApplication: GHIRCurriedFunction = self.functional
            uncurriedApplication = GHIRApplicationValue(self.context, self.type, curriedApplication.innerFunction, curriedApplication.partialApplications + self.arguments)
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
    def __init__(self, context: GHIRContext, name: str) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, module: GHIRImportedModule, type: GHIRValue, name: str) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext, type: GHIRValue, externalName: str, name: str) -> None:
        super().__init__(context)
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
    def __init__(self, context: GHIRContext) -> None:
        self.context = context
        self.exportedValues: list[tuple[str, GHIRValue]] = []
        self.entryPoint: GHIRValue = None
        self.name = ''

    def accept(self, visitor: GHIRVisitor):
        return visitor.visitModule(self)

    def getType(self) -> GHIRValue:
        return None
    
    def exportValue(self, name: str, value: GHIRValue, externalName: str | None = None):
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
        self.ghirModule = GHIRModule(context)
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

    def visitUnitTypeValue(self, value):
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
        translatedValue = GHIRLambdaValue(self.context, type)
        if value.type.callingConvention is not None:
            translatedValue.callingConvention = value.type.callingConvention.value
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

    def visitPiValue(self, value: PiValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRPiValue(self.context, type)
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

        return self.context.getFunctionType(type, [argumentType], resultType, conventionName)

    def visitSigmaValue(self, value: SigmaValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRSigmaValue(self.context, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

    def visitPrimitiveFunction(self, value: PrimitiveFunction):
        type = self.translateValue(value.uncurriedType)
        return GHIRPrimitiveFunction(self.context, type, self.optionalSymbolToString(value.primitiveName), value.value)

    def visitCurriedFunctionalValue(self, value: CurriedFunctionalValue):
        type = self.translateValue(value.type)
        innerFunction = self.translateValue(value.innerFunction)
        arguments = list(map(lambda arg: self.translateValue(arg), list(value.arguments)))
        return GHIRCurriedFunction(self.context, type, innerFunction, arguments).simplify()

    def visitCurryingFunctionalValue(self, value:  CurryingFunctionalValue):
        innerFunction = self.translateValue(value.innerFunction)
        type = self.translateValue(value.type)
        return GHIRCurryingFunction(self.context, type, innerFunction).simplify()

    def visitProductType(self, value: ProductType):
        type = self.translateValue(value.getType())
        elementTypes = list(map(self.translateValue, value.elementTypes))
        return self.context.getProductType(type, elementTypes)
    
    def visitUncurriedFunctionType(self, value: UncurriedFunctionType):
        type = self.translateValue(value.getType())
        argumentTypes = list(map(self.translateValue, value.argumentTypes))
        resultType = self.translateValue(value.resultType)
        return self.context.getFunctionType(type, argumentTypes, resultType)

    def visitRecordType(self, value):
        assert False

    def visitSumType(self, value):
        type = self.translateValue(value.getType())
        elementTypes = list(map(self.translateValue, value.elementTypes))
        return self.context.getSumType(type, elementTypes)

    def visitDecoratedType(self, value: DecoratedType):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        return self.context.getDecoratedType(type, baseType, value.decorations)

    def visitArrayType(self, value: ArrayType):
        type = self.translateValue(value.getType())
        baseType = self.translateValue(value.baseType)
        size = IntegerValue(value.size)
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
        return GHIRFunctionalDefinitionValue(self.context, captures, arguments, body).simplify()
    
    def visitImportedModuleValue(self, value: ImportedModuleValue):
        type: GHIRValue = self.translateValue(value.type)
        module: GHIRImportedModule = self.translateValue(value.module)
        name: str = value.name.value
        return module.importValueWithType(name, type)
    
    def visitImportedExternalValue(self, value: ImportedExternalValue):
        type: GHIRValue = self.translateValue(value.type)
        externalName: str = value.externalName.value
        name: str = value.name.value
        return GHIRImportedExternalValue(self.context, type, externalName, name)

    def visitImportedModule(self, value: ImportedModule):
        return GHIRImportedModule(self.context, value.name.value)

    def translateCaptureBinding(self, binding: SymbolCaptureBinding) -> GHIRCaptureBindingValue:
        type = self.translateExpression(binding.getTypeExpression())
        bindingValue = GHIRCaptureBindingValue(self.context, type, self.optionalSymbolToString(binding.name))
        self.translatedBindingValueDictionary[binding] = bindingValue
        return bindingValue

    def translateArgumentBinding(self, binding: SymbolArgumentBinding) -> GHIRArgumentBindingValue:
        type = self.translateExpression(binding.getTypeExpression())
        bindingValue = GHIRArgumentBindingValue(self.context, type, self.optionalSymbolToString(binding.name))
        self.translatedBindingValueDictionary[binding] = bindingValue
        return bindingValue

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> TypedValue:
        return self.translateValue(node.value)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        assert False

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elements = list(map(self.translateExpression, node.elementTypes))
        return GHIRProductType(self.context, type, elements).simplify()

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        type = self.context.getUniverse(node.computeTypeUniverseIndex())
        elements = list(map(self.translateExpression, node.elementTypes))
        return GHIRSumType(self.context, type, elements).simplify()
    
    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
        assert False

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.translateExpression(node.functional)
        argument = self.translateExpression(node.argument)
        type = self.translateExpression(node.type)
        return GHIRApplicationValue(self.context, type, functional, [argument]).simplify()

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
        argumentBinding = self.translateArgumentBinding(node.argumentBinding)
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, captureBindings, [argumentBinding], body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRPiValue(self.context, type, functionDefinition, capturedValues).simplify()

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        type = self.translateExpression(node.type)
        captureBindings = list(map(self.translateCaptureBinding, node.captureBindings))
        argumentBinding = self.translateArgumentBinding(node.argumentBinding)
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, captureBindings, [argumentBinding], body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRSigmaValue(self.context, type, functionDefinition, capturedValues).simplify()

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.translatedBindingValueDictionary[node.binding]

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.translateExpression(node.type)
        captureBindings = list(map(self.translateCaptureBinding, node.captureBindings))
        argumentBinding = self.translateArgumentBinding(node.argumentBinding)
        body = self.translateExpression(node.body)
        functionDefinition = GHIRFunctionalDefinitionValue(self.context, captureBindings, [argumentBinding], body).simplify()
        capturedValues = list(map(lambda capture: self.translatedBindingValueDictionary[capture.capturedBinding], node.captureBindings))
        return GHIRLambdaValue(self.context, type, functionDefinition, capturedValues).simplify()

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
        return GHIRSequence(self.context, type, expressions).simplify()

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression, node.elements))
        return GHIRMakeTupleExpression(self.context, type, elements).simplify()

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode) -> TypedValue:
        type = self.translateExpression(node.type)
        tuple = self.translateExpression(node.tuple)
        return GHIRTupleAtExpression(self.context, type, tuple, node.index).simplify()

    def visitTypedFromModuleImportNode(self, node):
        assert False

    def visitTypedFromExternalImportWithTypeNode(self, node):
        assert False

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        assert False

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        assert False

    def optionalSymbolToString(self, symbol: Symbol) -> str | None:
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

    def visitSequence(self, value: GHIRSequence):
        for expression in value.expressions:
            if self.checkValue(expression):
                return True
        return False

    def visitMakeTupleExpression(self, value: GHIRMakeTupleExpression):
        for element in value.elements:
            if self.checkValue(element):
                return True
        return False

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
