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
    def __init__(self, type: TypedValue, argumentBinding: SymbolArgumentBinding, captureBindings: list[SymbolCaptureBinding], captureBindingValues: list[TypedValue], body, sourcePosition: SourcePosition = None) -> None:
        self.type = type
        self.argumentBinding = argumentBinding
        self.captureBindings = captureBindings
        self.captureBindingValues = captureBindingValues
        self.body = body
        self.sourcePosition = sourcePosition

    def isPurelyFunctional(self) -> bool:
        return True

    def isFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

class LambdaValue(FunctionalValue):
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitLambdaValue(self)
    
    def isLambda(self) -> bool:
        return True

    def isReducibleFunctionalValue(self) -> bool:
        return True
    
    def prettyPrint(self) -> str:
        assert self.type.isPi()
        return '(:(%s)%s :: %s) :=> ...' % (self.type.argumentBinding.getTypeExpression().prettyPrint(), optionalIdentifierToString(self.type.argumentBinding.name), self.type.body.prettyPrint())

    def toJson(self):
        return {'lambda': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}

class PiValue(FunctionalValue):
    def __init__(self, type: TypedValue, argumentBinding: SymbolArgumentBinding, captureBindings: list[SymbolCaptureBinding], captureBindingValues: list[TypedValue], body, sourcePosition: SourcePosition = None, callingConvention: Symbol = None) -> None:
        super().__init__(type, argumentBinding, captureBindings, captureBindingValues, body, sourcePosition)
        self.callingConvention = callingConvention

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPiValue(self)

    def isReducibleFunctionalValue(self) -> bool:
        return True

    def getType(self):
        return self.type

    def withCallingConventionNamed(self, conventionName: Symbol):
        if self.callingConvention == conventionName:
            return self

        return PiValue(self.type, self.argumentBinding, self.captureBindings, self.captureBindingValues, self.body, self.sourcePosition, self.callingConvention)

    def toJson(self):
        return {'pi': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson(), 'callingConvention' : optionalToJson(self.callingConvention)}

    def prettyPrint(self) -> str:
        return '(:(%s)%s :: %s)' % (self.argumentBinding.getTypeExpression().prettyPrint(), optionalIdentifierToString(self.argumentBinding.name), self.body.prettyPrint())

    def isPi(self) -> bool:
        return True
    
class SigmaValue(FunctionalValue):
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitSigmaValue(self)

    def getType(self):
        return self.type

    def toJson(self):
        return {'sigma': str(self.argumentBinding.name), 'body': self.body.toJson(), 'type': self.type.toJson()}

    def prettyPrint(self) -> str:
        return '(:?(%s)%s :: %s)' % (self.type.argumentBinding.getTypeExpression().prettyPrint(), optionalIdentifierToString(self.type.argumentBinding.name), self.type.body.prettyPrint())

    def isSigma(self) -> bool:
        return True
    
class PrimitiveFunction(TypedValue):
    def __init__(self, type: TypedValue, uncurriedType: TypedValue, value, name: Symbol = None, primitiveName: Symbol = None, isMacro = False, isPure = True) -> None:
        self.type = type
        self.uncurriedType = uncurriedType
        self.name = name
        self.primitiveName = primitiveName
        self.value = value
        self.isMacro = isMacro
        self.isPure = isPure

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPrimitiveFunction(self)

    def isPurelyFunctional(self) -> bool:
        return self.isPure
    
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

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitCurriedFunctionalValue(self)

    def isPurelyFunctional(self) -> bool:
        return self.innerFunction.isPurelyFunctional()
    
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

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitCurryingFunctionalValue(self)

    def isFunctionalValue(self) -> bool:
        return True

    def isMacroValue(self) -> bool:
        return self.innerFunction.isMacroValue()
    
    def expectsMacroEvaluationContext(self) -> bool:
        return self.type.argumentType.isEquivalentTo(MacroContextType)

    def getType(self):
        return self.type

    def toJson(self):
        return {'currying': str(self.name), 'type': self.type.toJson(), 'innerFunction': self.innerFunction.toJson()}

    def __call__(self, *arguments) -> TypedValue:
        return CurriedFunctionalValue(self.innerFunction.getType(), arguments, self.innerFunction)

def optionalIdentifierToString(symbol: TypedValue) -> str:
    if symbol is None:
        return '_'
    else:
        return str(symbol)

def makeFunctionTypeFromTo(first: TypedValue, second: TypedValue, sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    return FunctionType.makeFromTo(first, second)

def makeSimpleFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 2
    if len(signature) == 2:
        return makeFunctionTypeFromTo(signature[0], signature[1], sourcePosition)
    else:
        return makeFunctionTypeFromTo(signature[0], (makeSimpleFunctionType(signature[1:], sourcePosition)), sourcePosition)

def makeUncurriedFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 1
    return UncurriedFunctionType(signature[:-1], signature[-1])

def makePrimitiveFunction(name: str, primitiveName: str, signature: list[TypedValue], function, sourcePosition: SourcePosition = EmptySourcePosition(), isMacro = False, previousArgumentTypes: list[TypedValue] = []):
    assert len(signature) >= 2
    nameSymbol = None
    if name is not None:
        nameSymbol = Symbol.intern(name)

    if len(signature) == 2:
        functionType = makeSimpleFunctionType(signature, sourcePosition)
        uncurriedFunctionType = makeUncurriedFunctionType(previousArgumentTypes + signature, sourcePosition)
        return PrimitiveFunction(functionType, uncurriedFunctionType, function, nameSymbol, Symbol.intern(primitiveName), isMacro = isMacro)
    else:
        innerFunction = makePrimitiveFunction(name, primitiveName, signature[1:], function, sourcePosition, isMacro = isMacro, previousArgumentTypes = previousArgumentTypes + [signature[0]])
        functionType = makeFunctionTypeFromTo(signature[0], innerFunction.getType(), sourcePosition)
        return CurryingFunctionalValue(functionType, innerFunction, nameSymbol)

def addPrimitiveFunctionDefinitionsToEnvironment(definitions, environment):
    for functionName, primitiveName, signature, function, extraFlags in definitions:
        isMacro = 'macro' in extraFlags
        environment = environment.withPrimitiveFunction(makePrimitiveFunction(functionName, primitiveName, signature, function, isMacro = isMacro))
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

def arrowMacro(macroContext: MacroContext, argumentType: ASTNode, resultType: ASTNode) -> ASTNode:
    return ASTFunctionTypeNode(macroContext.sourcePosition, argumentType, resultType)

def callingConventionMacro(macroContext: MacroContext, functionNode: ASTNode, conventionName: TypedValue) -> ASTNode:
    if functionNode.isFunctionalDependentTypeNode():
        return macroContext.typechecker.visitNodeForMacroExpansionOnly(functionNode).withCallingConventionNamed(conventionName)
    else:
        return macroContext.typechecker.visitNode(functionNode).withCallingConventionNamed(conventionName)

def cdeclMacro(macroContext: MacroContext, functionNode: ASTNode) -> ASTNode:
    return callingConventionMacro(macroContext, functionNode, Symbol.intern('cdecl'))

def stdcallMacro(macroContext: MacroContext, functionNode: ASTNode) -> ASTNode:
    return callingConventionMacro(macroContext, functionNode, Symbol.intern('stdcall'))

def apicallMacro(macroContext: MacroContext, functionNode: ASTNode) -> ASTNode:
    return callingConventionMacro(macroContext, functionNode, Symbol.intern('apicall'))

def thiscallMacro(macroContext: MacroContext, functionNode: ASTNode) -> ASTNode:
    return callingConventionMacro(macroContext, functionNode, Symbol.intern('thiscall'))

def vectorcallMacro(macroContext: MacroContext, functionNode: ASTNode) -> ASTNode:
    return callingConventionMacro(macroContext, functionNode, Symbol.intern('vectorcall'))

def importModuleMacro(macroContext: MacroContext, name: ASTNode) -> ASTNode:
    return ASTImportModuleNode(macroContext.sourcePosition, name)

def fromModuleImportWithType(macroContext: MacroContext, module: ASTNode, name: ASTNode, type: ASTNode) -> ASTNode:
    return ASTFromModuleImportWithTypeNode(macroContext.sourcePosition, module, name, type)

def fromExternalImportWithType(macroContext: MacroContext, externalName: ASTNode, name: ASTNode, type: ASTNode) -> ASTNode:
    return ASTFromExternalImportWithTypeNode(macroContext.sourcePosition, externalName, name, type)

def moduleExportWithMacro(macroContext: MacroContext, name: ASTNode, value: ASTNode) -> ASTNode:
    return ASTModuleExportValueNode(macroContext.sourcePosition, None, name, value)

def moduleExportExternalWithMacro(macroContext: MacroContext, name: ASTNode, externalName: ASTNode, value: ASTNode) -> ASTNode:
    return ASTModuleExportValueNode(macroContext.sourcePosition, externalName, name, value)

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
    ['let:type:with:', 'Macro::let:type:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], letTypeWithMacro, ['macro']],
    ['let:with:', 'Macro::let:with:',[MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], letWithMacro, ['macro']],
    ['let:type:mutableWith:', 'Macro::let:type:mutableWith:',[MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], letTypeMutableWithMacro, ['macro']],
    ['let:mutableWith:', 'Macro::let:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], letMutableWithMacro, ['macro']],

    ['public:type:with:', 'Macro::public:type:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], publicTypeWithMacro, ['macro']],
    ['public:with:', 'Macro::public:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], publicWithMacro, ['macro']],
    ['public:type:mutableWith:', 'Macro::public:type:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], publicTypeMutableWithMacro, ['macro']],
    ['public:mutableWith:', 'Macro::public:mutableWith:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], publicMutableWithMacro, ['macro']],

    ['loadSourceNamed:', 'Macro::loadSourceNamed:', [MacroContextType, ASTNodeType, ASTNodeType], loadSourceNamedMacro, ['macro']],

    ['importModule:', 'Macro::importModule:', [MacroContextType, ASTNodeType, ASTNodeType], importModuleMacro, ['macro']],
    ['fromModule:import:withType:', 'Macro::fromModule:import:withType:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], fromModuleImportWithType, ['macro']],
    ['fromExternal:import:withType:', 'Macro::fromModule:import:withType:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], fromExternalImportWithType, ['macro']],
    ['export:with:', 'Macro::export:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], moduleExportWithMacro, ['macro']],
    ['export:external:with:', 'Macro::export:external:with:', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType], moduleExportExternalWithMacro, ['macro']],
    ['moduleEntryPoint:', 'Macro::moduleEntryPoint:', [MacroContextType, ASTNodeType, ASTNodeType], moduleEntryPointMacro, ['macro']],

    ['=>', 'Type::=>', [MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType], arrowMacro, ['macro']],
    ['__cdecl', 'Type::__cdecl', [MacroContextType, ASTNodeType, ASTNodeType], cdeclMacro, ['macro']],
    ['__stdcall', 'Type::__stdcall', [MacroContextType, ASTNodeType, ASTNodeType], stdcallMacro, ['macro']],
    ['__apicall', 'Type::__apicall', [MacroContextType, ASTNodeType, ASTNodeType], apicallMacro, ['macro']],
    ['__thiscall', 'Type::__thiscall', [MacroContextType, ASTNodeType, ASTNodeType], thiscallMacro, ['macro']],
    ['__vectorcall', 'Type::__vectorcall', [MacroContextType, ASTNodeType, ASTNodeType], vectorcallMacro, ['macro']],

    ['const', 'Type::const', [TypeType, TypeType], DecoratedType.makeConst, []],
    ['volatile', 'Type::volatile', [TypeType, TypeType], DecoratedType.makeVolatile, []],
    ['array:', 'Type::array:', [TypeType, IntegerType, TypeType], ArrayType.makeWithElementTypeAndSize, []],
    ['pointer', 'Type::pointer', [TypeType, TypeType], PointerType.makeWithBaseType, []],
    ['ref', 'Type::ref', [TypeType, TypeType], ReferenceType.makeWithBaseType, []],
    ['tempRef', 'Type::tempRef', [TypeType, TypeType], TemporaryReferenceType.makeWithBaseType, []],
], TopLevelEnvironment)

for primitiveNumberType in NumberTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['negated', prefix + 'negated', [primitiveNumberType, primitiveNumberType], lambda x: -x, []],

        ['+', prefix + '+',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x + y, []],
        ['-', prefix + '-',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x - y, []],
        ['*', prefix + '*',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x * y, []],

        ['asInt8',  prefix + 'asInt8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), []],
        ['asInt16', prefix + 'asInt16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), []],
        ['asInt32', prefix + 'asInt32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), []],
        ['asInt64', prefix + 'asInt64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), []],

        ['asUInt8',  prefix + 'asUInt8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), []],
        ['asUInt16', prefix + 'asUInt16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), []],
        ['asUInt32', prefix + 'asUInt32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), []],
        ['asUInt64', prefix + 'asUInt64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []],

        ['asChar8',  prefix + 'asChar8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), []],
        ['asChar16', prefix + 'asChar16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), []],
        ['asChar32', prefix + 'asChar32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), []],

        ['asFloat32', prefix + 'asFloat32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), []],
        ['asFloat64', prefix + 'asFloat64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), []],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType] + PrimitiveIntegerTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['bitInvert', prefix + 'bitInvert',  [primitiveNumberType, primitiveNumberType], lambda x: ~x, []],

        ['//', prefix + '//',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.quotientWith(y), []],
        ['%', prefix + '%',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x.remainderWith(y), []],
    ], TopLevelEnvironment)

for primitiveNumberType in PrimitiveFloatTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['/', prefix + '/',  [primitiveNumberType, primitiveNumberType, primitiveNumberType], lambda x, y: x / y, []],
        ['sqrt', prefix + 'sqrt',  [primitiveNumberType, primitiveNumberType], lambda x: x.sqrt(), []],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType, Char32Type, Float64Type]:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['i8',  prefix + 'i8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), []],
        ['i16', prefix + 'i16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), []],
        ['i32', prefix + 'i32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), []],
        ['i64', prefix + 'i64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), []],

        ['u8',  prefix + 'u8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), []],
        ['u16', prefix + 'u16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), []],
        ['u32', prefix + 'u32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), []],
        ['u64', prefix + 'u64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), []],

        ['c8',  prefix + 'c8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), []],
        ['c16', prefix + 'c16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), []],
        ['c32', prefix + 'c32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), []],

        ['f32', prefix + 'f32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), []],
        ['f64', prefix + 'f64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), []],
    ], TopLevelEnvironment)

TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(FalseType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withUnitTypeValue(TrueType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeScriptAnalysisEnvironment(module: Module, sourcePosition: SourcePosition, scriptPath: str) -> LexicalEnvironment:
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ScriptEnvironment(ModuleEnvironment(TopLevelEnvironment, module), sourcePosition, scriptDirectory, scriptName)
