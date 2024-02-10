from abc import ABC, abstractmethod
from .value import *
from .environment import *
from .ast import *

class GHIRContext:
    def __init__(self) -> None:
        self.constantValues = dict()

    def getConstantValue(self, value: TypedValue):
        if value in self.constantValues:
            return self.constantValues[value]
        
        constantValue = GHIRConstantValue(self, value)
        self.constantValues[value] = constantValue
        return constantValue

class GHIRValue(ABC):
    def __init__(self, context: GHIRContext) -> None:
        self.context = context

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
        return self.type

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := constant %s' % (valueName, self.value.prettyPrint()))

class GHIRLocalBindingValue(GHIRValue):
    def __init__(self, context: GHIRContext, type: GHIRValue, name: str = None) -> None:
        super().__init__(context)
        self.type = type
        self.name = name

    def getType(self) -> GHIRValue:
        return self.type

class GHIRCaptureBindingValue(GHIRLocalBindingValue):
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := capture %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRArgumentBindingValue(GHIRLocalBindingValue):
    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        graphPrinter.printLine('%s := argument %s' % (valueName, graphPrinter.printValue(self.type)))

class GHIRFunctionalDefinitionValue(GHIRValue):
    def __init__(self, context: GHIRContext, captures: list[GHIRCaptureBindingValue] = [], arguments: list[GHIRArgumentBindingValue] = [], body: GHIRValue = None) -> None:
        super().__init__(context)
        self.captures = captures
        self.arguments = arguments
        self.body = body
        
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

class GHIRLambdaValue(GHIRFunctionalValue):
    def getFunctionalValueKindName(self) -> str:
        return 'lambda'

class GHIRPiValue(GHIRFunctionalValue):
    def getFunctionalValueKindName(self) -> str:
        return 'pi'

class GHIRSigmaValue(GHIRFunctionalValue):
    def getFunctionalValueKindName(self) -> str:
        return 'sigma'

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

class GHIRModule(GHIRValue):
    def __init__(self, context: GHIRContext) -> None:
        self.context = context
        self.entryPoint: GHIRValue = None

    def getType(self) -> GHIRValue:
        return None

    def fullPrintGraph(self, graphPrinter: GHIRGraphPrinter, valueName: str):
        if self.entryPoint is not None:
            graphPrinter.printLine('module entryPoint: %s' % graphPrinter.printValue(self.entryPoint))
  
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
        return translatedValue

    def visitPiValue(self, value: PiValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRPiValue(self.context, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue

    def visitSigmaValue(self, value: SigmaValue):
        type = self.translateValue(value.getType())
        translatedValue = GHIRSigmaValue(self.context, type)
        self.translatedValueDictionary[value] = translatedValue
        translatedValue.definition = self.translateFunctionalValueDefinition(value)
        return translatedValue
    
    def translateFunctionalValueDefinition(self, functionalValue: FunctionalValue) -> GHIRFunctionalDefinitionValue:
        captures = list(map(self.translateCaptureBinding, functionalValue.captureBindings))
        argument = self.translateArgumentBinding(functionalValue.argumentBinding)
        body = self.translateExpression(functionalValue.body)
        return GHIRFunctionalDefinitionValue(self.context, captures, [argument], body)
    
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
        assert False

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        assert False

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.translateExpression(node.functional)
        argument = self.translateExpression(node.argument)
        type = self.translateExpression(node.type)
        return GHIRApplicationValue(self.context, type, functional, [argument])

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
        assert False

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode) -> TypedValue:
        assert False

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode) -> TypedValue:
        assert False

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        assert False

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        assert False

    def optionalSymbolToString(self, symbol: Symbol) -> str | None:
        if symbol is None: return None
        return str(symbol)
