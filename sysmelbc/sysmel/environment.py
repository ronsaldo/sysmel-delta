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
    
class FunctionalAnalysisEnvironment(LexicalEnvironment):
    def __init__(self, parent: AbstractEnvironment, argumentBinding: SymbolArgumentBinding, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.argumentBinding = argumentBinding
        self.captureBindings = []
        self.capturedBindingMap = dict()

    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        if self.argumentBinding is not None and symbol == self.argumentBinding.name:
            return self.argumentBinding
        return None
    
    def getOrCreateCaptureForBinding(self, binding: SymbolBinding | None) -> SymbolBinding | None:
        if binding is None: return binding
        if binding.isValueBinding(): return binding
        if binding in self.capturedBindingMap:
            return self.capturedBindingMap[binding]
        
        capturedBinding = SymbolCaptureBinding(binding.sourcePosition, binding.name, binding)
        self.capturedBindingMap[binding] = capturedBinding
        self.captureBindings.append(capturedBinding)
        return capturedBinding

    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return binding

        if self.parent is not None:
            return self.getOrCreateCaptureForBinding(self.parent.lookSymbolRecursively(symbol))
        return None

    def lookSymbolBindingListRecursively(self, symbol: Symbol) -> list[Symbol]:
        parentResult = []
        if self.parent is not None:
            parentResult = list(map(self.getOrCreateCaptureForBinding, self.parent.lookSymbolBindingListRecursively(symbol)))

        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return [binding] + parentResult
        else:
            return parentResult
        
class FunctionalActivationEnvironment:
    def __init__(self):
        self.bindingValues = dict()

    def setBindingValue(self, binding: SymbolBinding, value: TypedValue):
        self.bindingValues[binding] = value

    def lookBindingValueAt(self, binding: SymbolBinding, sourcePosition: SourcePosition) -> TypedValue:
        if binding in self.bindingValues:
            return self.bindingValues[binding]
        
        raise Exception('%s: Binding for %s does not have an active value.' % (str(sourcePosition), repr(binding.name)))
    
class FunctionalValue(TypedValue):
    def __init__(self, type: TypedValue, argumentBinding: SymbolArgumentBinding, captureBindings: list[SymbolCaptureBinding], captureBindingValues: list[TypedValue], body) -> None:
        self.type = type
        self.argumentBinding = argumentBinding
        self.captureBindings = captureBindings
        self.captureBindingValues = captureBindingValues
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
    def __init__(self, type: TypedValue, value, name: Symbol = None, isMacro = False) -> None:
        self.type = type
        self.name = name
        self.value = value
        self.isMacro = isMacro

    def isFunctionalValue(self) -> bool:
        return True

    def isMacroValue(self) -> bool:
        return self.isMacro

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

    def isMacroValue(self) -> bool:
        return self.innerFunction.isMacroValue()

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

    def isMacroValue(self) -> bool:
        return self.innerFunction.isMacroValue()
    
    def expectsMacroEvaluationContext(self) -> bool:
        return self.type.argumentBinding.hasTypeOf(MacroContextType)

    def getType(self):
        return self.type

    def toJson(self):
        return {'currying': str(self.name), 'type': self.type.toJson(), 'innerFunction': self.innerFunction.toJson()}

    def __call__(self, *arguments) -> TypedValue:
        return CurriedFunctionalValue(self.innerFunction.getType(), arguments, self.innerFunction)

def makeFunctionTypeFromTo(first: TypedValue, second: TypedValue, sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    return PiValue(first.getType(), SymbolArgumentBinding(None, None, ASTLiteralTypeNode(sourcePosition, first)), [], [], ASTLiteralTypeNode(sourcePosition, second))

def makeSimpleFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 2
    if len(signature) == 2:
        return makeFunctionTypeFromTo(signature[0], signature[1], sourcePosition)
    else:
        return makeFunctionTypeFromTo(signature[0], (makeSimpleFunctionType(signature[1:], sourcePosition)), sourcePosition)

def makePrimitiveFunction(name: str, signature: list[TypedValue], function, sourcePosition: SourcePosition = EmptySourcePosition(), isMacro = False):
    assert len(signature) >= 2
    nameSymbol = None
    if name is not None:
        nameSymbol = Symbol.intern(name)

    if len(signature) == 2:
        functionType = makeSimpleFunctionType(signature)
        return PrimitiveFunction(functionType, function, nameSymbol, isMacro = isMacro)
    else:
        innerFunction = makePrimitiveFunction(nameSymbol, signature[1:], function, sourcePosition, isMacro = isMacro)
        functionType = makeFunctionTypeFromTo(signature[0], innerFunction.getType(), sourcePosition)
        return CurryingFunctionalValue(functionType, innerFunction, nameSymbol)

def addPrimitiveFunctionDefinitionsToEnvironment(definitions, environment):
    for functionName, signature, function, extraFlags in definitions:
        isMacro = 'macro' in extraFlags
        environment = environment.withPrimitiveFunction(makePrimitiveFunction(functionName, signature, function, isMacro = isMacro))
    return environment

def letTypeWithMacro(macroContext: MacroContext, localName: ASTNode, expectedType: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTLocalDefinitionNode(macroContext.sourcePosition, localName, expectedType, localValue)

def letWithMacro(macroContext: MacroContext, localName: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTLocalDefinitionNode(macroContext.sourcePosition, localName, None, localValue)

## Boolean :: False | True.
FalseType = UnitTypeClass("False", "false")
TrueType = UnitTypeClass("True", "true")
BooleanType = SumType.makeNamedWithVariantTypes("Boolean", [FalseType, TrueType])

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
for baseType in [
        AbsurdType, UnitType,
        IntegerType, CharacterType, StringType, FalseType, TrueType, BooleanType,
        Int8Type, Int16Type, Int32Type, Int64Type,
        UInt8Type, UInt16Type, UInt32Type, UInt64Type,
        ASTNodeType, 
    ]:
    TopLevelEnvironment = TopLevelEnvironment.withBaseType(baseType)
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(UnitType.getSingleton())

TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
    ['let:type:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], letTypeWithMacro, ['macro']],
    ['let:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], letWithMacro, ['macro']],

    ['const', [TypeType, TypeType], DecoratedType.makeConst, []],
    ['volatile', [TypeType, TypeType], DecoratedType.makeVolatile, []],
    ['array:', [TypeType, IntegerType, TypeType], ArrayType.makeWithElementTypeAndSize, []],
    ['pointer', [TypeType, TypeType], PointerType.makeWithBaseType, []],
    ['ref', [TypeType, TypeType], ReferenceType.makeWithBaseType, []],
    ['tempRef', [TypeType, TypeType], TemporaryReferenceType.makeWithBaseType, []],
], TopLevelEnvironment)

for primitiveNumberType in [IntegerType, FloatType] + PrimitiveIntegerTypes:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['+',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x + y, []],
        ['-',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x - y, []],
        ['*',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x * y, []],

        ['asInt8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), []],
        ['asInt16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), []],
        ['asInt32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), []],
        ['asInt64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), []],

        ['asUInt8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), []],
        ['asUInt16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), []],
        ['asUInt32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), []],
        ['asUInt64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []]
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType] + PrimitiveIntegerTypes:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['//',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.quotientWith(y), []],
        ['%',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.remainderWith(y), []],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType, CharacterType, FloatType]:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['i8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), []],
        ['i16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), []],
        ['i32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), []],
        ['i64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), []],
        ['u8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), []],
        ['u16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), []],
        ['u32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), []],
        ['u64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []]
    ], TopLevelEnvironment)

TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(FalseType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(TrueType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeDefaultEvaluationEnvironment() -> LexicalEnvironment:
    return LexicalEnvironment(TopLevelEnvironment)