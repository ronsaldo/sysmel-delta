from .value import *
from .ast import *

class AbstractEnvironment(ABC):
    @abstractmethod
    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        pass

    def isLexicalEnvironment(self) -> bool:
        return False
    
    def withBaseType(self, baseType: BaseType, sourcePosition: SourcePosition = None):
        assert baseType.name is not None
        return ChildEnvironmentWithBinding(self, SymbolValueBinding(sourcePosition, Symbol.intern(baseType.name), baseType))

    def withUnitTypeValue(self, unitTypeValue: UnitTypeValue, sourcePosition: SourcePosition = None):
        assert unitTypeValue.name is not None
        return ChildEnvironmentWithBinding(self, SymbolValueBinding(sourcePosition, Symbol.intern(unitTypeValue.name), unitTypeValue))

    def withPrimitiveFunction(self, primitiveFunction, sourcePosition: SourcePosition = None):
        assert primitiveFunction.name is not None
        return ChildEnvironmentWithBinding(self, SymbolValueBinding(sourcePosition, primitiveFunction.name, primitiveFunction))

    def withSymbolBinding(self, symbolBinding: SymbolBinding):
        return ChildEnvironmentWithBinding(self, symbolBinding)

    def withSymbolValueBinding(self, symbol: Symbol, value: TypedValue, sourcePosition: SourcePosition = None):
        return ChildEnvironmentWithBinding(self, SymbolValueBinding(sourcePosition, symbol, value))

class EmptyEnvironment(AbstractEnvironment):
    Singleton = None

    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        return None

    def lookSymbolBindingListRecursively(self, symbol: Symbol) -> list[Symbol]:
        return []

    @classmethod
    def getSingleton(cls):
        if cls.Singleton is None:
            cls.Singleton = cls()
        return cls.Singleton

class ChildEnvironment(AbstractEnvironment):
    def __init__(self, parent: AbstractEnvironment) -> None:
        self.parent = parent

    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        return None
    
    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return binding

        if self.parent is not None:
            return self.parent.lookSymbolRecursively(symbol)
        return None

    def lookSymbolBindingListRecursively(self, symbol: Symbol) -> list[Symbol]:
        parentResult = []
        if self.parent is not None:
            parentResult = self.parent.lookSymbolBindingListRecursively(symbol)

        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return [binding] + parentResult
        else:
            return parentResult

class ChildEnvironmentWithBinding(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, binding: SymbolBinding) -> None:
        super().__init__(parent)
        self.binding = binding

    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        if symbol == self.binding.name:
            return self.binding
        return None

class LexicalEnvironment(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent)
        self.sourcePosition = sourcePosition
    
    def isLexicalEnvironment(self) -> bool:
        return True

class FunctionalActivationEnvironment:
    def __init__(self, parent = None):
        self.parent = parent
        self.bindingValues = dict()

    def setBindingValue(self, binding: SymbolBinding, value: TypedValue):
        self.bindingValues[binding] = value

    def lookBindingValueAt(self, binding: SymbolBinding, sourcePosition: SourcePosition) -> TypedValue:
        if binding in self.bindingValues:
            return self.bindingValues[binding]
        
        if self.parent is None:
            raise Exception('%s: Binding for %s does not have an active value.' % (str(sourcePosition), repr(binding.name)))
        return self.parent.lookBindingValueAt(binding, sourcePosition)
    
class FunctionalValue(TypedValue):
    def __init__(self, type: TypedValue, environment: FunctionalActivationEnvironment, argumentBinding: SymbolArgumentBinding, body) -> None:
        self.type = type
        self.environment = environment
        self.argumentBinding = argumentBinding
        self.body = body

    def isPurelyFunctional(self) -> bool:
        return True

    def isFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

class LambdaValue(FunctionalValue):
    def toJson(self):
        return {'lambda': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}

class PiValue(FunctionalValue):
    def getType(self):
        return self.type

    def toJson(self):
        return {'forAll': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}
    
    def isPi(self) -> bool:
        return True
    
class PrimitiveFunction(TypedValue):
    def __init__(self, type: TypedValue, value, name: Symbol = None) -> None:
        self.type = type
        self.name = name
        self.value = value

    def isFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

    def toJson(self):
        return {'primitive': str(self.name), 'type': self.type.toJson()}

    def __call__(self, *argument) -> TypedValue:
        return self.value(*argument)

class CurriedFunctionalValue(TypedValue):
    def __init__(self, type: TypedValue, arguments: tuple[TypedValue], innerFunction: TypedValue) -> None:
        self.type = type
        self.arguments = arguments
        self.innerFunction = innerFunction

    def isFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

    def toJson(self):
        return {'curried': list(map(lambda a: a.toJson(), self.arguments)), 'type': self.type.toJson(), 'innerFunction': self.innerFunction.toJson()}

    def __call__(self, *arguments) -> TypedValue:
        return self.innerFunction(*self.arguments, *arguments)
    
class CurryingFunctionalValue(TypedValue):
    def __init__(self, type: TypedValue, innerFunction: TypedValue, name: Symbol = None) -> None:
        self.type = type
        self.name = name
        self.innerFunction = innerFunction

    def isFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

    def toJson(self):
        return {'currying': str(self.name), 'type': self.type.toJson(), 'innerFunction': self.innerFunction.toJson()}

    def __call__(self, *arguments) -> TypedValue:
        return CurriedFunctionalValue(self.innerFunction.getType(), arguments, self.innerFunction)

def makeFunctionTypeFromTo(first: TypedValue, second: TypedValue, sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    return PiValue(first.getType(), None, SymbolArgumentBinding(None, None, ASTLiteralTypeNode(sourcePosition, first)), ASTLiteralTypeNode(sourcePosition, second))

def makeSimpleFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 2
    if len(signature) == 2:
        return makeFunctionTypeFromTo(signature[0], signature[1], sourcePosition)
    else:
        return makeFunctionTypeFromTo(signature[0], (makeSimpleFunctionType(signature[1:], sourcePosition)), sourcePosition)

def makePrimitiveFunction(name: str, signature: list[TypedValue], function, sourcePosition: SourcePosition = EmptySourcePosition()):
    assert len(signature) >= 2
    nameSymbol = None
    if name is not None:
        nameSymbol = Symbol.intern(name)

    if len(signature) == 2:
        functionType = makeSimpleFunctionType(signature)
        return PrimitiveFunction(functionType, function, nameSymbol)
    else:
        innerFunction = makePrimitiveFunction(nameSymbol, signature[1:], function, sourcePosition)
        functionType = makeFunctionTypeFromTo(signature[0], innerFunction.getType(), sourcePosition)
        return CurryingFunctionalValue(functionType, innerFunction, nameSymbol)

def addPrimitiveFunctionDefinitionsToEnvironment(definitions, environment):
    for functionName, signature, function in definitions:
        environment = environment.withPrimitiveFunction(makePrimitiveFunction(functionName, signature, function))
    return environment

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withBaseType(AbsurdType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(UnitType)
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(UnitType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withBaseType(NatType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(IntegerType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(FloatType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(CharacterType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(StringType)
TopLevelEnvironment = TopLevelEnvironment.withBaseType(ASTNodeType)

TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
    ['+', [NatType, NatType, NatType],             lambda x, y: x + y],
    ['+', [IntegerType, IntegerType, IntegerType], lambda x, y: x + y],
    ['+', [FloatType, FloatType, FloatType],       lambda x, y: x + y],

    ['-', [NatType, NatType, NatType],             lambda x, y: x - y],
    ['-', [IntegerType, IntegerType, IntegerType], lambda x, y: x - y],
    ['-', [FloatType, FloatType, FloatType],       lambda x, y: x - y],

    ['*', [NatType, NatType, NatType],             lambda x, y: x * y],
    ['*', [IntegerType, IntegerType, IntegerType], lambda x, y: x * y],
    ['*', [FloatType, FloatType, FloatType],       lambda x, y: x * y],

    ['//', [NatType, NatType, NatType],             lambda x, y: x.quotientWith(y)],
    ['//', [IntegerType, IntegerType, IntegerType], lambda x, y: x.quotientWith(y)],
    ['/', [FloatType, FloatType, FloatType],        lambda x, y: x / y],

    ['%', [NatType, NatType, NatType],             lambda x, y: x.remainderWith(y)],
    ['%', [IntegerType, IntegerType, IntegerType], lambda x, y: x.remainderWith(y)],
], TopLevelEnvironment)

## Boolean :: False | True.
FalseType = UnitTypeClass("False", "false")
TrueType = UnitTypeClass("True", "true")
BooleanType = SumType.makeWithVariantTypes([FalseType, TrueType])
TopLevelEnvironment = TopLevelEnvironment.withBaseType(FalseType)
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(FalseType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withBaseType(TrueType)
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(TrueType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeDefaultEvaluationEnvironment() -> LexicalEnvironment:
    return LexicalEnvironment(TopLevelEnvironment)