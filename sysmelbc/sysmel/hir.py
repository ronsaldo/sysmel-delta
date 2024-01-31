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
    def getType():
        pass

class HIRConstantValue(HIRValue):
    def __init__(self, context: HIRContext, value: TypedValue) -> None:
        super().__init__(context)
        self.value = value
        self.type = None

    def getType(self) -> HIRValue:
        if self.type is None:
            self.type = self.context.getConstantValue(self.value.getType())
        return self.type

class HIRFunctionalValue(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context)
        self.type = type
    
    def getType(self):
        return self.type

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
        return str(self.entryPoint)

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
        hirLambda = HIRLambdaValue(self.context, lambdaType)
        self.translatedValueDictionary[lambdaValue] = hirLambda
        HIRFunctionalTranslator(self).translateLambdaInto(lambdaValue, hirLambda)
        return hirLambda

    def translatePi(self, piValue: LambdaValue):
        piType = self.translateValue(piValue.getType())
        hirPi = HIRPiValue(self.context, piType)
        self.translatedValueDictionary[piValue] = hirPi
        HIRFunctionalTranslator(self).translatePiInto(piValue, hirPi)
        return hirPi

    def translateSigma(self, piValue: LambdaValue):
        assert False


class HIRFunctionalTranslator:
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.moduleFrontend = moduleFrontend

    def translateLambdaInto(self, piValue, hirLambdaValue) -> None:
        return

    def translatePiInto(self, piValue, hirPiValue) -> None:
        return
    
    def translateSigmaInto(self, piValue, hirSigmaValue) -> None:
        return