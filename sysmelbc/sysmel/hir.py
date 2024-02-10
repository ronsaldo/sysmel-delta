from abc import ABC, abstractmethod
from .value import *
from .environment import *
from .ast import *

class HIRContext:
    def __init__(self) -> None:
        self.constantValues = dict()

    def getConstantValue(self, value: TypedValue):
        if value in self.constantValues:
            return self.constantValues[value]
        
        constantValue = HIRConstantValue(self, value)
        self.constantValues[value] = constantValue
        return constantValue

class HIRValue:
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    @abstractmethod
    def getType(self):
        pass

    def fullPrintString(self) -> str:
        return str(self)

class HIRConstantValue(HIRValue):
    def __init__(self, context: HIRContext, value: TypedValue) -> None:
        super().__init__(context)
        self.value = value
        self.type = None

    def getType(self) -> HIRValue:
        if self.type is None:
            self.type = self.context.getConstantValue(self.value.getType())
        return self.type

    def __str__(self) -> str:
        return 'constant ' + self.value.prettyPrint()

class HIRFunctionalDefinition:
    def __init__(self, context: HIRContext) -> None:
        self.context = context
        self.captures: list[HIRFunctionalCaptureValue] = []
        self.arguments: list[HIRFunctionalArgumentValue] = []
        self.firstBasicBlock: HIRBasicBlock = None
        self.lastBasicBlock: HIRBasicBlock = None

    def addBasicBlock(self, basicBlock, position = None):
        assert basicBlock.parent is None
        assert basicBlock.previous is None
        assert basicBlock.next is None

        basicBlock.next = position
        basicBlock.previous = None
        if basicBlock.next is not None:
            basicBlock.previous = basicBlock.next.previous

        if basicBlock.next is not None:
            basicBlock.next.previous = basicBlock
        else:
            self.lastBasicBlock = basicBlock

        if basicBlock.previous is not None:
            basicBlock.previous.next = basicBlock
        else:
            self.firstBasicBlock = basicBlock

    def addBasicBlockAfter(self, basicBlock, position = None):
        assert basicBlock.parent is None
        assert basicBlock.previous is None
        assert basicBlock.next is None

        basicBlock.previous = position
        basicBlock.next = None
        if basicBlock.next is not None:
            basicBlock.next = basicBlock.previous.next

        if basicBlock.next is not None:
            basicBlock.next.previous = basicBlock
        else:
            self.lastBasicBlock = basicBlock

        if basicBlock.previous is not None:
            basicBlock.previous.next = basicBlock
        else:
            self.firstBasicBlock = basicBlock

    def basicBlocks(self):
        position = self.firstBasicBlock
        while position is not None:
            nextPosition = position.next
            yield position
            position = nextPosition

    def fullPrintString(self) -> str:
        result = 'captures ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += capture.fullPrintString()

        result += '] arguments ['
        isFirst = True
        for argument in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += argument.fullPrintString()
        result += '] {\n'
        for basicBlock in self.basicBlocks():
            result += basicBlock.fullPrintString()
        result += '}'
        return result

class HIRLocalValue(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None) -> None:
        super().__init__(context)
        self.type = type
        self.name = name

class HIRFunctionalCaptureValue(HIRLocalValue):
    pass

class HIRFunctionalArgumentValue(HIRLocalValue):
    pass

class HIRBasicBlock(HIRLocalValue):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, None, name)
        self.parent: HIRFunctionalDefinition = None
        self.previous: HIRBasicBlock = None
        self.next: HIRBasicBlock = None
        self.firstInstruction: HIRInstruction = None
        self.lastInstruction: HIRInstruction = None

    def addInstruction(self, instruction, position = None):
        assert instruction.parent is None
        assert instruction.previous is None
        assert instruction.next is None

        instruction.next = position
        instruction.previous = None
        if instruction.next is not None:
            instruction.previous = instruction.next.previous

        if instruction.next is not None:
            instruction.next.previous = instruction
        else:
            self.lastInstruction = instruction

        if instruction.previous is not None:
            instruction.previous.next = instruction
        else:
            self.firstInstruction = instruction

    def instructions(self):
        position = self.firstInstruction
        while position is not None:
            nextPosition = position.next
            yield position
            position = nextPosition

    def fullPrintString(self) -> str:
        result = self.name
        result += ":\n"
        for instruction in self.instructions():
            result += '    '
            result += instruction.fullPrintString()
            result += '\n'
        return result
    
    def isLastTerminator(self) -> bool:
        return self.lastInstruction is not None and self.lastInstruction.isTerminator()

class HIRInstruction(HIRLocalValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context, type)
        self.parent: HIRBasicBlock = None
        self.previous: HIRInstruction = None
        self.next: HIRInstruction = None

    def isTerminator(self) -> bool:
        return False

class HIRTerminatorInstruction(HIRInstruction):
    def isTerminator(self) -> bool:
        return True

class HIRReturnInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, value: HIRValue) -> None:
        super().__init__(context, None)
        self.value = value

    def fullPrintString(self) -> str:
        return 'return ' + str(self.value)
    
class HIRBuilder:
    def __init__(self, context: HIRContext) -> None:
        self.context = context
        self.insertionBlock: HIRBasicBlock = None
        self.insertionPoint: HIRInstruction = None

    def newBasicBlock(self, name: str = None) -> HIRBasicBlock:
        return HIRBasicBlock(self.context, name)

    def beginBasicBlockHere(self, basicBlock: HIRBasicBlock):
        self.insertionBlock = basicBlock
        self.insertionPoint = None

    def newBasicBlockHere(self, name: str = None) -> HIRBasicBlock:
        basicBlock = self.newBasicBlock(name)
        self.beginBasicBlockHere(basicBlock)
        return basicBlock
    
    def addInstruction(self, instruction: HIRInstruction) -> HIRInstruction:
        self.insertionBlock.addInstruction(instruction, self.insertionPoint)
        return instruction
    
    def isLastTerminator(self) -> bool:
        return self.insertionBlock is not None and self.insertionBlock.isLastTerminator()
    
    def returnValue(self, value: HIRValue) -> HIRInstruction:
        return self.addInstruction(HIRReturnInstruction(self.context, value))

class HIRFunctionalValue(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue, capturedValues: list[HIRValue], definition: HIRFunctionalDefinition) -> None:
        super().__init__(context)
        self.type = type
        self.capturedValues = capturedValues
        self.definition = definition
    
    def getType(self):
        return self.type

    def fullPrintString(self) -> str:
        result = self.__class__.__name__ + "["
        isFirst = True
        for capturedValue in self.capturedValues:
            if isFirst:
                isFirst = False
            else:
                result += ", "
            result += str(capturedValue)
        result += "] := "
        result += self.definition.fullPrintString()
        return result

class HIRLambdaValue(HIRFunctionalValue):
    pass

class HIRPiValue(HIRFunctionalValue):
    pass

class HIRSigmaValue(HIRFunctionalValue):
    pass

class HIRModule:
    def __init__(self, context: HIRContext) -> None:
        self.context = context
        self.entryPoint: HIRValue = None

    def prettyPrint(self) -> str:
        result = ""
        if self.entryPoint is not None:
            result += self.entryPoint.fullPrintString()
        return result

class HIRModuleFrontend:
    def __init__(self, context = HIRContext()) -> None:
        self.context = context
        self.hirModule = HIRModule(context)
        self.translatedValueDictionary = dict()

    def compileModule(self, module: Module):
        if module.entryPoint is not None:
            self.hirModule.entryPoint = self.translateValue(module.entryPoint)
        return self.hirModule

    def translateValue(self, value: TypedValue):
        if value in self.translatedValueDictionary:
            return self.translatedValueDictionary

        if value.isLambda():
            return self.translateLambda(value)
        elif value.isPi():
            return self.translatePi(value)
        elif value.isSigma():
            return self.translateSigma(value)
        else:
            return self.context.getConstantValue(value)

    def translateLambda(self, lambdaValue: LambdaValue):
        lambdaType = self.translateValue(lambdaValue.getType())
        hirLambdaDefinition = HIRFunctionalDefinition(self.context)
        hirLambda = HIRLambdaValue(self.context, lambdaType, [], hirLambdaDefinition)
        self.translatedValueDictionary[lambdaValue] = hirLambda
        HIRFunctionalTranslator(self).translateFunctionalValueInto(lambdaValue, hirLambdaDefinition)
        return hirLambda

    def translatePi(self, piValue: LambdaValue):
        piType = self.translateValue(piValue.getType())
        hirPiDefinition = HIRFunctionalDefinition(self.context)
        hirPi = HIRPiValue(self.context, piType, [], hirPiDefinition)
        self.translatedValueDictionary[piValue] = hirPi
        HIRFunctionalTranslator(self).translateFunctionalValueInto(piValue, hirPiDefinition)
        return hirPi

    def translateSigma(self, sigmaValue: LambdaValue):
        sigmaType = self.translateValue(sigmaValue.getType())
        hirSigmaDefinition = HIRFunctionalDefinition(self.context)
        hirSigma = HIRSigmaValue(self.context, sigmaType, [], hirSigmaDefinition)
        self.translatedValueDictionary[sigmaValue] = hirSigma
        HIRFunctionalTranslator(self).translateFunctionalValueInto(sigmaValue, hirSigmaDefinition)
        return hirSigma

class HIRFunctionalTranslator(ASTTypecheckedVisitor):
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.moduleFrontend = moduleFrontend
        self.hirContext = self.moduleFrontend
        self.hirBuilder = HIRBuilder(self.hirContext)
        self.bindingValueMap = dict()

    def translateFunctionalValueInto(self, functionalValue: FunctionalValue, functionalDefinition: HIRFunctionalDefinition) -> None:
        captureValues = []
        for captureBinding in functionalValue.captureBindings:
            captureType = self.visitNode(captureBinding.getTypeExpression())
            captureValue = HIRFunctionalCaptureValue(self.hirContext, captureType, optionalSymbolToString(functionalValue.argumentBinding.name))
            self.bindingValueMap[functionalValue.argumentBinding] = captureValue
            captureValues.append(captureValue)

        functionalDefinition.captures = captureValues

        argumentType = self.visitNode(functionalValue.argumentBinding.getTypeExpression())
        argumentValue = HIRFunctionalArgumentValue(self.hirContext, argumentType, optionalSymbolToString(functionalValue.argumentBinding.name))
        self.bindingValueMap[functionalValue.argumentBinding] = argumentValue
        functionalDefinition.arguments = [argumentValue]

        entryBlock = self.hirBuilder.newBasicBlockHere('entry')
        functionalDefinition.addBasicBlock(entryBlock)

        resultValue = self.visitNode(functionalValue.body)
        if not self.hirBuilder.isLastTerminator():
            self.hirBuilder.returnValue(resultValue)

    def visitNode(self, node) -> HIRValue:
        return node.accept(self)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> TypedValue:
        return self.moduleFrontend.translateValue(node.value)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        assert False

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        assert False

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        assert False

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        assert False

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        assert False

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        assert False

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        assert False

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        assert False

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        assert False

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        assert False

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return self.hirContext.translateValue(node.value)

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

def optionalSymbolToString(symbol: Symbol) -> str:
    if symbol is None: return None
    return str(symbol)
