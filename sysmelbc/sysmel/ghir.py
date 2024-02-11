from abc import ABC, abstractmethod
from .value import *
from .environment import *
from .ast import *

class GHIRContext:
    def __init__(self) -> None:
        self.constantValues = dict()
        self.simpleFunctionTypes = dict()

    def getConstantValue(self, value: TypedValue):
        if value in self.constantValues:
            return self.constantValues[value]
        
        constantValue = GHIRConstantValue(self, value)
        self.constantValues[value] = constantValue
        return constantValue
    
    def getSimpleFunctionType(self, type, argumentTypes, resultType):
        hashKey = (type, tuple(argumentTypes), resultType)
        if hashKey in self.simpleFunctionTypes:
            return self.simpleFunctionTypes[hashKey]
        
        simpleFunctionType = GHIRSimpleFunctionType(self, type, argumentTypes, resultType)
        self.simpleFunctionTypes[hashKey] = simpleFunctionType
        return simpleFunctionType
        

class GHIRValue(ABC):
    def __init__(self, context: GHIRContext) -> None:
        self.context = context
        self.userValues = []

    def getName(self) -> str | None:
        return None

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
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := capture %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRArgumentBindingValue(GHIRLocalBindingValue):
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := argument %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRSimpleFunctionType(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, arguments: list[GHIRValue], resultType: GHIRValue) -> None:    
        super().__init__(context)
        self.type = type
        self.arguments = arguments
        self.resultType = resultType

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
        graphPrinter.printLine('%s := functionType [%s] -> %s : %s' % (valueName, argumentList, resultType, type))

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
    def __init__(self, context: GHIRContext, type: GHIRValue, definition: GHIRFunctionalDefinitionValue = None, captures: list[GHIRValue] = []) -> None:
        super().__init__(context)
        self.type = type
        self.definition = definition
        self.captures = captures

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
    def getFunctionalValueKindName(self) -> str:
        return 'lambda'

class GHIRPiValue(GHIRFunctionalValue):
    def getFunctionalValueKindName(self) -> str:
        return 'pi'
    
    def simplify(self):
        if self.definition.isFunctionalDefinition() and self.definition.isCaptureless() and not self.definition.hasArgumentDependency():
            argumentTypes = list(map(lambda arg: arg.getType(), self.definition.arguments))
            resultType = self.definition.body
            simpleFunctionType = self.context.getSimpleFunctionType(self.getType(), argumentTypes, resultType)
            return self.replaceWith(simpleFunctionType)
        return super().simplify()

class GHIRSigmaValue(GHIRFunctionalValue):
    def getFunctionalValueKindName(self) -> str:
        return 'sigma'

class GHIRProductType(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, elements: list[GHIRValue]) -> None:
        super().__init__(context)
        self.type = type
        self.elements = elements

    def getType(self) -> GHIRValue:
        return self.type

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

class GHIRSequence(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, expressions: list[GHIRValue]) -> None:
        super().__init__(context)
        self.type = type
        self.expressions = expressions

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

    def getType(self) -> GHIRValue:
        return self.type

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

class GHIRApplicationValue(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, functional: GHIRValue, arguments: list[GHIRValue]) -> None:
        super().__init__(context)
        self.type = type
        self.functional = functional
        self.arguments = arguments

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

class GHIRModule(GHIRValue):
    def __init__(self, context: GHIRContext) -> None:
        self.context = context
        self.entryPoint: GHIRValue = None

    def getType(self) -> GHIRValue:
        return None

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
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
        self.hirModule = GHIRModule(context)
        self.translatedValueDictionary = dict()
        self.translatedBindingValueDictionary = dict()

    def compileModule(self, module: Module):
        if module.entryPoint is not None:
            self.hirModule.entryPoint = self.translateValue(module.entryPoint)
        return self.hirModule

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

    def visitLambdaValue(self, value: LambdaValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRLambdaValue(self.context, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

    def visitPiValue(self, value: PiValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRPiValue(self.context, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue.simplify()

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

    def translateFunctionalValueDefinition(self, functionalValue: FunctionalValue) -> GHIRFunctionalDefinitionValue:
        captures = list(map(self.translateCaptureBinding, functionalValue.captureBindings))
        argument = self.translateArgumentBinding(functionalValue.argumentBinding)
        body = self.translateExpression(functionalValue.body)
        return GHIRFunctionalDefinitionValue(self.context, captures, [argument], body).simplify()
    
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
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression), node.elements)
        return GHIRProductType(self.context, type, elements).simplify()

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression), node.elements)
        return GHIRSumType(self.context, type, elements).simplify()

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.translateExpression(node.functional)
        argument = self.translateExpression(node.argument)
        type = self.translateExpression(node.type)
        return GHIRApplicationValue(self.context, type, functional, [argument]).simplify()

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        assert False

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        assert False

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        assert False

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        assert False

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.translatedBindingValueDictionary[node.binding]

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        assert False

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
        expressions = list(map(self.translateExpression), node.elements)
        return GHIRSequence(self.context, type, expressions).simplify()

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        type = self.translateExpression(node.type)
        elements = list(map(self.translateExpression), node.elements)
        return GHIRMakeTupleExpression(self.context, type, elements).simplify()

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        assert False

    def optionalSymbolToString(self, symbol: Symbol) -> str | None:
        if symbol is None: return None
        return symbol.value
