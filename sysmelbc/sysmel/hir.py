from abc import ABC, abstractmethod
from .ghir import *

class HIRContext:
    def __init__(self) -> None:
        pass

class HIRValue(ABC):
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    @abstractmethod
    def getType(self):
        pass

class HIRConstant(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context)
        self.type = type

    def getType(self):
        return self.type

class HIRFunctionalDefinition(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context, type)
        self.firstBasicBlock: HIRBasicBlock = None
        self.lastBasicBlock: HIRBasicBlock = None

    def fullPrintString(self) -> str:
        result = ''
        return result

class HIRFunctionalLocalValue(HIRValue):
    pass

class HIRBasicBlock(HIRFunctionalLocalValue):
    pass

class HIRInstruction(HIRFunctionalLocalValue):
    pass

class HIRConstantLambda(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRConstant, captures: list[HIRConstant], definition: HIRFunctionalDefinition) -> None:
        super().__init__(context, type)
        self.captures = captures
        self.definition = definition

class HIRModule(HIRValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.entryPoint: HIRValue = None
        self.functionalDefinitions = []

    def getType(self):
        return None

    def prettyPrint(self) -> str:
        result = ''
        if self.entryPoint is not None:
            result += 'entryPoint: %s\n' % str(self.entryPoint)

        for functionalDefinition in self.functionalDefinitions:
            result += functionalDefinition.fullPrintString()
        return result

class HIRModuleFrontend:
    def __init__(self) -> None:
        self.context = HIRContext()
        self.module = HIRModule(self.context)
        self.translatedValueDictionary = dict()

    def compileGraphModule(self, graphModule: GHIRModule) -> HIRModule:
        if graphModule.entryPoint is not None:
            self.entryPoint = self.translateGraphValue(graphModule.entryPoint)
        return self.module
    
    def translateGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        if graphValue in self.translatedValueDictionary:
            return self.translatedValueDictionary[graphValue]
        
        translatedValue = graphValue.accept(self)
        self.translatedValueDictionary[graphValue] = translatedValue
        return translatedValue
    
    def visitLambdaValue(self, graphValue: GHIRLambdaValue) -> HIRValue:
        definition = self.translateGraphValue(graphValue.definition)
        captures = list(map(self.translateGraphValue, graphValue.captures))
        return HIRConstantLambda(self.context, None, captures, definition)

    def visitFunctionalDefinitionValue(self, graphValue: GHIRFunctionalDefinitionValue) -> HIRValue:
        hirDefinition = HIRFunctionalDefinition(self.context, None)
        self.translatedValueDictionary[graphValue] = hirDefinition
        self.module.functionalDefinitions.append(hirDefinition)
        return hirDefinition