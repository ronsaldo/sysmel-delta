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

class HIRFunctionalDefinition:
    def __init__(self, context: HIRContext) -> None:
        self.context = context
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
        result = '{\n'
        for basicBlock in self.basicBlocks():
            result += basicBlock.fullPrintString()
        result += '}'
        return result

class HIRLocalValue(HIRValue):
    pass

class HIRBasicBlock(HIRLocalValue):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context)
        self.name = name
        self.parent: HIRFunctionalDefinition = None
        self.previous: HIRBasicBlock = None
        self.next: HIRBasicBlock = None
        self.firstInstruction: HIRInstruction = None
        self.lastInstruction: HIRInstruction = None

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
            result += instruction.fullPrintString
            result += '\n'
        return result

class HIRInstruction(HIRLocalValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.parent: HIRBasicBlock = None
        self.previous: HIRInstruction = None
        self.next: HIRInstruction = None

class HIRBuilder:
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    def newBasicBlock(self, name: str = None) -> HIRBasicBlock:
        return HIRBasicBlock(self.context, name)

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

class HIRFunctionalTranslator:
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.moduleFrontend = moduleFrontend
        self.hirContext = self.moduleFrontend
        self.hirBuilder = HIRBuilder(self.hirContext)

    def translateFunctionalValueInto(self, functionalValue: FunctionalValue, functionalDefinition: HIRFunctionalDefinition) -> None:
        entryBlock = self.hirBuilder.newBasicBlock('entry')
        functionalDefinition.addBasicBlock(entryBlock)
