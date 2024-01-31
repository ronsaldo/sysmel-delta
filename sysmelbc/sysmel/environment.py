from .value import *
from .ast import *
import os.path

class AbstractEnvironment(ABC):
    @abstractmethod
    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        pass

    def lookScriptDirectory(self) -> str:
        return None

    def lookScriptName(self) -> str:
        return None
    
    def lookModule(self) -> Module:
        return None

    def lookFunctionalAnalysisEnvironment(self):
        return None

    def isLexicalEnvironment(self) -> bool:
        return False

    def isScriptEnvironment(self) -> bool:
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

    def withImplicitValueBindingSubstitution(self, binding: SymbolValueBinding, substitution: ASTNode):
        return ChildEnvironmentWithBindingSubstitution(self, binding, substitution)

    def hasSubstitutionForImplicitValueBinding(self, binding) -> bool:
        return False

    def findSubstitutionForImplicitValueBinding(self, binding) -> ASTNode | None:
        return None
    
    def getImplicitValueSubstitutionsUpTo(self, targetEnvironment) -> list[tuple[SymbolImplicitValueBinding, ASTNode]]:
        return []

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
    
    def lookFunctionalAnalysisEnvironment(self):
        return self.parent.lookScriptDirectory()

    def lookScriptDirectory(self) -> str:
        return self.parent.lookScriptDirectory()

    def lookScriptName(self) -> str:
        return self.parent.lookScriptName()
    
    def lookModule(self) -> Module:
        return self.parent.lookModule()

    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return binding

        return self.parent.lookSymbolRecursively(symbol)

    def lookSymbolBindingListRecursively(self, symbol: Symbol) -> list[Symbol]:
        parentResult = parentResult = self.parent.lookSymbolBindingListRecursively(symbol)

        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return [binding] + parentResult
        else:
            return parentResult

    def hasSubstitutionForImplicitValueBinding(self, binding) -> bool:
        return self.parent.hasSubstitutionForImplicitValueBinding(binding)

    def findSubstitutionForImplicitValueBinding(self, binding) -> ASTNode | None:
        return None

    def getImplicitValueSubstitutionsUpTo(self, targetEnvironment) -> list[tuple[SymbolImplicitValueBinding, ASTNode]]:
        if self == targetEnvironment: return []
        return self.parent.getImplicitValueSubstitutionsUpTo(targetEnvironment)

class ChildEnvironmentWithBinding(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, binding: SymbolBinding) -> None:
        super().__init__(parent)
        self.binding = binding

    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        if symbol == self.binding.name:
            return self.binding
        return None

class ChildEnvironmentWithBindingSubstitution(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, binding: SymbolBinding, substitution: ASTNode) -> None:
        super().__init__(parent)
        self.binding = binding
        self.substitution = substitution

    def getImplicitValueSubstitutionsUpTo(self, targetEnvironment) -> list[tuple[SymbolImplicitValueBinding, ASTNode]]:
        return [(self.binding, self.substitution)] + self.parent.getImplicitValueSubstitutionsUpTo(targetEnvironment)

class LexicalEnvironment(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent)
        self.sourcePosition = sourcePosition
    
    def isLexicalEnvironment(self) -> bool:
        return True

class ModuleEnvironment(ChildEnvironment):
    def __init__(self, parent: AbstractEnvironment, module: Module) -> None:
        super().__init__(parent)
        self.module = module
    
    def isModuleEnvironment(self) -> bool:
        return True
    
    def lookModule(self) -> Module:
        return self.module
    
class ScriptEnvironment(LexicalEnvironment):
    def __init__(self, parent: AbstractEnvironment, sourcePosition: SourcePosition = None, scriptDirectory = '', scriptName = 'script') -> None:
        super().__init__(parent, sourcePosition)
        self.scriptDirectory = scriptDirectory
        self.scriptName = scriptName
        self.scriptDirectoryBinding = SymbolValueBinding(sourcePosition, Symbol.intern('__SourceDirectory__'), StringValue(self.scriptDirectory))
        self.scriptNameBinding = SymbolValueBinding(sourcePosition, Symbol.intern('__SourceName__'), StringValue(self.scriptName))

    def lookScriptDirectory(self) -> str:
        return self.scriptDirectory

    def lookScriptName(self) -> str:
        return self.scriptName
        
    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        if symbol == self.scriptDirectoryBinding.name:
            return self.scriptDirectoryBinding
        if symbol == self.scriptNameBinding.name:
            return self.scriptNameBinding

        return super().lookLocalSymbol(symbol)

class FunctionalAnalysisEnvironment(LexicalEnvironment):
    def __init__(self, parent: AbstractEnvironment, argumentBinding: SymbolArgumentBinding, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.argumentBinding = argumentBinding
        self.captureBindings = []
        self.capturedBindingMap = dict()

    def lookFunctionalAnalysisEnvironment(self):
        return self

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

        return self.getOrCreateCaptureForBinding(self.parent.lookSymbolRecursively(symbol))

    def lookSymbolBindingListRecursively(self, symbol: Symbol) -> list[Symbol]:
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
    def isReducibleFunctionalValue(self) -> bool:
        return True

    def toJson(self):
        return {'lambda': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}

class PiValue(FunctionalValue):
    def isReducibleFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

    def toJson(self):
        return {'pi': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}
    
    def isPi(self) -> bool:
        return True
    
class SigmaValue(FunctionalValue):
    def getType(self):
        return self.type

    def toJson(self):
        return {'sigma': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}
    
    def isSigma(self) -> bool:
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
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, expectedType, localValue)

def letWithMacro(macroContext: MacroContext, localName: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, None, localValue)

def letTypeMutableWithMacro(macroContext: MacroContext, localName: ASTNode, expectedType: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, expectedType, localValue, isMutable = True)

def letMutableWithMacro(macroContext: MacroContext, localName: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, None, localValue, isMutable = True)

def publicTypeWithMacro(macroContext: MacroContext, localName: ASTNode, expectedType: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, expectedType, localValue, isPublic = True)

def publicWithMacro(macroContext: MacroContext, localName: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, None, localValue, isPublic = True)

def publicTypeMutableWithMacro(macroContext: MacroContext, localName: ASTNode, expectedType: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, expectedType, localValue, isMutable = True, isPublic = True)

def publicMutableWithMacro(macroContext: MacroContext, localName: ASTNode, localValue: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, localName, None, localValue, isMutable = True, isPublic = True)

def moduleEntryPointMacro(macroContext: MacroContext, entryPointValue: ASTNode) -> ASTNode:
    return ASTModuleEntryPointNode(macroContext.sourcePosition, entryPointValue)

def loadSourceNamedMacro(macroContext: MacroContext, sourceName: ASTNode) -> ASTNode:
    from .parser import parseFileNamed
    sourceNameStringValue, errorNode = macroContext.typechecker.evaluateString(sourceName)
    if errorNode is not None:
        return errorNode
    
    sourceNameString = sourceNameStringValue.value
    module = macroContext.lexicalEnvironment.lookModule()
    scriptDirectory = macroContext.lexicalEnvironment.lookScriptDirectory()
    scriptPath = os.path.join(scriptDirectory, sourceNameString)
    
    try:
        sourceAST = parseFileNamed(scriptPath)
        scriptEnvironment = makeScriptAnalysisEnvironment(module, sourceAST.sourcePosition, scriptPath)
        return macroContext.typechecker.loadSourceASTWithEnvironment(sourceAST, scriptEnvironment, macroContext.sourcePosition)
    except FileNotFoundError:
        return ASTErrorNode(macroContext.sourcePosition, 'Failed to find source file "%s".' % sourceNameString)

## Boolean :: False | True.
FalseType = UnitTypeClass("False", "false")
TrueType = UnitTypeClass("True", "true")
BooleanType = SumType.makeNamedWithVariantTypes("Boolean", [FalseType, TrueType])

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
for baseType in [
        AbsurdType, UnitType,
        IntegerType, StringType, FalseType, TrueType, BooleanType,
        Int8Type, Int16Type, Int32Type, Int64Type,
        UInt8Type, UInt16Type, UInt32Type, UInt64Type,
        Char8Type, Char16Type, Char32Type,
        Float32Type, Float64Type,
        ASTNodeType, 
    ]:
    TopLevelEnvironment = TopLevelEnvironment.withBaseType(baseType)
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(UnitType.getSingleton())

TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
    ['let:type:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], letTypeWithMacro, ['macro']],
    ['let:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], letWithMacro, ['macro']],
    ['let:type:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], letTypeMutableWithMacro, ['macro']],
    ['let:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], letMutableWithMacro, ['macro']],

    ['public:type:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], publicTypeWithMacro, ['macro']],
    ['public:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], publicWithMacro, ['macro']],
    ['public:type:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], publicTypeMutableWithMacro, ['macro']],
    ['public:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], publicMutableWithMacro, ['macro']],

    ['loadSourceNamed:', [MacroContextType, ASTNodeType, ASTNodeType], loadSourceNamedMacro, ['macro']],
    ['moduleEntryPoint:', [MacroContextType, ASTNodeType, ASTNodeType], moduleEntryPointMacro, ['macro']],

    ['const', [TypeType, TypeType], DecoratedType.makeConst, []],
    ['volatile', [TypeType, TypeType], DecoratedType.makeVolatile, []],
    ['array:', [TypeType, IntegerType, TypeType], ArrayType.makeWithElementTypeAndSize, []],
    ['pointer', [TypeType, TypeType], PointerType.makeWithBaseType, []],
    ['ref', [TypeType, TypeType], ReferenceType.makeWithBaseType, []],
    ['tempRef', [TypeType, TypeType], TemporaryReferenceType.makeWithBaseType, []],
], TopLevelEnvironment)

for primitiveNumberType in NumberTypes:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['negated',  [primitiveNumberType, primitiveNumberType], lambda x: -x, []],

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
        ['asUInt64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []],

        ['asChar8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), []],
        ['asChar16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), []],
        ['asChar32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), []],

        ['asFloat32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), []],
        ['asFloat64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), []],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType] + PrimitiveIntegerTypes:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['bitInvert',  [primitiveNumberType, primitiveNumberType], lambda x: ~x, []],

        ['//',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.quotientWith(y), []],
        ['%',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.remainderWith(y), []],
    ], TopLevelEnvironment)

for primitiveNumberType in PrimitiveFloatTypes:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['/',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x / y, []],
        ['sqrt',  [primitiveNumberType, primitiveNumberType], lambda x: x.sqrt(), []],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType, Char32Type, Float64Type]:
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['i8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), []],
        ['i16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), []],
        ['i32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), []],
        ['i64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), []],

        ['u8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), []],
        ['u16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), []],
        ['u32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), []],
        ['u64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []],

        ['c8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), []],
        ['c16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), []],
        ['c32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), []],

        ['f32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), []],
        ['f64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), []],
    ], TopLevelEnvironment)

TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(FalseType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(TrueType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeScriptAnalysisEnvironment(module: Module, sourcePosition: SourcePosition, scriptPath: str) -> LexicalEnvironment:
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ScriptEnvironment(ModuleEnvironment(TopLevelEnvironment, module), sourcePosition, scriptDirectory, scriptName)
