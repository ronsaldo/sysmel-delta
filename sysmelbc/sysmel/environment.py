from .value import *
from .ast import *
import os.path
import copy

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

    def withVoidTypeValue(self, unitTypeValue: VoidTypeValue, sourcePosition: SourcePosition = None):
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

    def withImplicitValueBindingSubstitutions(self, substitutions: list[tuple[SymbolImplicitValueBinding, ASTNode]]):
        result = self
        for binding, substitution in substitutions:
            result = result.withImplicitValueBindingSubstitution(binding, substitution)
        return result

    def hasSubstitutionForImplicitValueBinding(self, binding) -> bool:
        return False

    def findSubstitutionForImplicitValueBinding(self, binding) -> ASTNode:
        return None
    
    def getImplicitValueSubstitutionsUpTo(self, targetEnvironment) -> list[tuple[SymbolImplicitValueBinding, ASTNode]]:
        return []

    def isValidContextForBreak(self) -> bool:
        return False

    def isValidContextForContinue(self) -> bool:
        return False

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
        parentResult = self.parent.lookSymbolBindingListRecursively(symbol)

        binding = self.lookLocalSymbol(symbol)
        if binding is not None:
            return [binding] + parentResult
        else:
            return parentResult

    def hasSubstitutionForImplicitValueBinding(self, binding) -> bool:
        return self.parent.hasSubstitutionForImplicitValueBinding(binding)

    def findSubstitutionForImplicitValueBinding(self, binding) -> ASTNode:
        return None

    def getImplicitValueSubstitutionsUpTo(self, targetEnvironment) -> list[tuple[SymbolImplicitValueBinding, ASTNode]]:
        if self == targetEnvironment: return []
        return self.parent.getImplicitValueSubstitutionsUpTo(targetEnvironment)
    
    def isValidContextForBreak(self) -> bool:
        return self.parent.isValidContextForBreak()

    def isValidContextForContinue(self) -> bool:
        return self.parent.isValidContextForContinue()

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

class ChildEnvironmentBreakAndContinue(ChildEnvironment):
    def isValidContextForBreak(self) -> bool:
        return True

    def isValidContextForContinue(self) -> bool:
        return True

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
        self.scriptDirectoryBinding = SymbolValueBinding(sourcePosition, Symbol.intern('__SourceDirectory__'), makeStringValue(self.scriptDirectory))
        self.scriptNameBinding = SymbolValueBinding(sourcePosition, Symbol.intern('__SourceName__'), makeStringValue(self.scriptName))

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
    def __init__(self, parent: AbstractEnvironment, arguments: list[SymbolArgumentBinding], sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.arguments = arguments
        self.argumentBindingMap = dict()

        self.captureBindings = []
        self.capturedBindingMap = dict()
        for argument in arguments:
            if argument.name is not None:
                self.argumentBindingMap[argument.name] = argument

    def postCopy(self):
        self.arguments = list(self.arguments)
        self.argumentBindingMap = dict(self.argumentBindingMap)

        self.captureBindings = list(self.captureBindings)
        self.capturedBindingMap = dict(self.capturedBindingMap)
        return self

    def withArgumentBinding(self, newBinding: SymbolArgumentBinding):
        result = copy.copy(self)
        result.postCopy()
        result.arguments.append(newBinding)
        if newBinding.name is not None:
            result.argumentBindingMap[newBinding.name] = newBinding
        return result

    def lookFunctionalAnalysisEnvironment(self):
        return self

    def lookLocalSymbol(self, symbol: Symbol) -> SymbolBinding:
        if symbol in self.argumentBindingMap:
            return self.argumentBindingMap[symbol]
        return None
    
    def getOrCreateCaptureForBinding(self, binding: SymbolBinding) -> SymbolBinding:
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
    def __init__(self, type: TypedValue, argumentBindings: list[SymbolArgumentBinding], isVariadic: bool, captureBindings: list[SymbolCaptureBinding], captureBindingValues: list[TypedValue], body, sourcePosition: SourcePosition = None) -> None:
        self.type = type
        self.argumentBindings = argumentBindings
        self.isVariadic = isVariadic
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
        result = '('
        for argument in self.argumentBindings:
            if len(result) != 1:
                result += ', '
            result += ':(%s)%s' % (argument.getTypeExpression().prettyPrint(), optionalIdentifierToString(argument.name))

        result += ' :: %s) :=> ...' % self.type.body.prettyPrint()
        return result

    def toJson(self):
        return {'lambda': list(map(lambda n: n.toJson(), self.argumentBindings)), 'body': self.body.toJson(), 'type': self.type.toJson()}

class PiValue(FunctionalValue):
    def __init__(self, type: TypedValue, argumentBindings: list[SymbolArgumentBinding], isVariadic: bool, captureBindings: list[SymbolCaptureBinding], captureBindingValues: list[TypedValue], body, sourcePosition: SourcePosition = None, callingConvention: Symbol = None) -> None:
        super().__init__(type, argumentBindings, isVariadic, captureBindings, captureBindingValues, body, sourcePosition)
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

        return PiValue(self.type, self.argumentBindings, self.isVariadic, self.captureBindings, self.captureBindingValues, self.body, self.sourcePosition, conventionName)

    def toJson(self):
        return {'pi': list(map(lambda n: n.toJson(), self.argumentBindings)), 'body': self.body.toJson(), 'type': self.type.toJson(), 'callingConvention' : optionalToJson(self.callingConvention)}

    def prettyPrint(self) -> str:
        result = '('
        for argument in self.argumentBindings:
            if len(result) != 1:
                result += ', '
            result += ':(%s)%s' % (argument.getTypeExpression().prettyPrint(), optionalIdentifierToString(argument.name))

        result += ' :: %s)' % self.body.prettyPrint()
        return result
    
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
        result = '('
        for argument in self.argumentBindings:
            if len(result) != 1:
                result += ', :(%s)%s' % (argument.getTypeExpression().prettyPrint(), optionalIdentifierToString(argument.name))
            else:
                result += ':?(%s)%s' % (argument.getTypeExpression().prettyPrint(), optionalIdentifierToString(argument.name))

        result += ' :: %s) :=> ...' % self.body.prettyPrint()
        return result
    def isSigma(self) -> bool:
        return True
    
class PrimitiveFunction(TypedValue):
    def __init__(self, type: TypedValue, value, name: Symbol = None, primitiveName: Symbol = None, isMacro = False, isPure = False) -> None:
        self.type = type
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
    
    def prettyPrint(self) -> str:
        return self.primitiveName.prettyPrint()

    def expectsMacroEvaluationContext(self) -> bool:
        argumentType = self.type.argumentType
        return argumentType.isProductType() and argumentType.elementTypes[0].isEquivalentTo(MacroContextType)
    
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

def parseSimpleTypeSignature(signature) -> TypedValue:
    if isinstance(signature, tuple):
        return ProductType.makeWithElementTypes(list(signature))
    return signature

def makeSimpleFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 2
    if len(signature) == 2:
        return makeFunctionTypeFromTo(parseSimpleTypeSignature(signature[0]), signature[1], sourcePosition)
    else:
        return makeFunctionTypeFromTo(parseSimpleTypeSignature(signature[0]), (makeSimpleFunctionType(signature[1:], sourcePosition)), sourcePosition)

def makeUncurriedFunctionType(signature: list[TypedValue], sourcePosition: SourcePosition = EmptySourcePosition()) -> PiValue:
    assert len(signature) >= 1
    return UncurriedFunctionType(signature[:-1], signature[-1])

def makePrimitiveFunction(name: str, primitiveName: str, signature: list[TypedValue], function, sourcePosition: SourcePosition = EmptySourcePosition(), isMacro = False, isPure = False):
    assert len(signature) >= 2
    nameSymbol = None
    if name is not None:
        nameSymbol = Symbol.intern(name)

    if len(signature) == 2:
        functionType = makeSimpleFunctionType(signature, sourcePosition)
        return PrimitiveFunction(functionType, function, nameSymbol, Symbol.intern(primitiveName), isMacro = isMacro, isPure = isPure)
    else:
        innerFunction = makePrimitiveFunction(name, primitiveName, signature[1:], function, sourcePosition, isMacro = isMacro, isPure = isPure)
        functionType = makeFunctionTypeFromTo(signature[0], innerFunction.getType(), sourcePosition)
        return CurryingFunctionalValue(functionType, innerFunction, nameSymbol)

def addPrimitiveFunctionDefinitionsToEnvironment(definitions, environment):
    for functionName, primitiveName, signature, function, extraFlags in definitions:
        isMacro = 'macro' in extraFlags
        isPure = 'pure' in extraFlags
        environment = environment.withPrimitiveFunction(makePrimitiveFunction(functionName, primitiveName, signature, function, isMacro = isMacro, isPure = isPure))
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

def ifThenMacro(macroContext: MacroContext, condition: ASTNode, trueExpression: ASTNode) -> ASTNode:
    return ASTIfNode(macroContext.sourcePosition, condition, trueExpression, None)

def ifThenElseMacro(macroContext: MacroContext, condition: ASTNode, trueExpression: ASTNode, falseExpression: ASTNode) -> ASTNode:
    return ASTIfNode(macroContext.sourcePosition, condition, trueExpression, falseExpression)

def whileDoMacro(macroContext: MacroContext, condition: ASTNode, bodyExpression: ASTNode) -> ASTNode:
    return ASTWhileNode(macroContext.sourcePosition, condition, bodyExpression, None)

def whileDoContinueWithMacro(macroContext: MacroContext, condition: ASTNode, bodyExpression: ASTNode, continueExpression: ASTNode) -> ASTNode:
    return ASTWhileNode(macroContext.sourcePosition, condition, bodyExpression, continueExpression)

def doWhileMacro(macroContext: MacroContext, bodyExpression: ASTNode, condition: ASTNode) -> ASTNode:
    return ASTDoWhileNode(macroContext.sourcePosition, bodyExpression, condition, None)

def doWhileContinueWithMacro(macroContext: MacroContext, bodyExpression: ASTNode, condition: ASTNode, continueExpression: ASTNode) -> ASTNode:
    return ASTDoWhileNode(macroContext.sourcePosition, bodyExpression, condition, continueExpression)

def arrowMacro(macroContext: MacroContext, argumentType: ASTNode, resultType: ASTNode) -> ASTNode:
    return ASTFunctionTypeNode(macroContext.sourcePosition, argumentType, resultType)

def callingConventionMacro(macroContext: MacroContext, functionNode: ASTNode, conventionName: TypedValue) -> ASTNode:
    if functionNode.isFunctionalDependentTypeNode():
        return macroContext.typechecker.visitNodeForMacroExpansionOnly(functionNode).withCallingConventionNamed(conventionName)
    else:
        return macroContext.typechecker.visitNode(functionNode).withCallingConventionNamed(conventionName)

def formNamedRecordWithFieldsMacro(macroContext: MacroContext, name: ASTNode, fields: ASTNode) -> ASTNode:
    keyAndFields, errorNode = macroContext.typechecker.expandAndUnpackDictionaryNodeWithElements(fields)
    if errorNode is not None:
        return ASTFormRecordTypeNode(macroContext.sourcePosition, name, [None], [errorNode])

    fieldNames = []
    fieldTypes = []
    for fieldName, type in keyAndFields:
        fieldNames.append(fieldName)
        fieldTypes.append(type)

    return ASTFormRecordTypeNode(macroContext.sourcePosition, name, fieldNames, fieldTypes)

def formRecordWithFieldsMacro(macroContext: MacroContext, fields: ASTNode) -> ASTNode:
    return formNamedRecordWithFieldsMacro(macroContext, None, fields)

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
    return fromModuleImportAsWithType(macroContext, module, name, name, type)

def fromModuleImportAsWithType(macroContext: MacroContext, module: ASTNode, name: ASTNode, importedName: ASTNode, type: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, importedName, None, 
        ASTFromModuleImportWithTypeNode(macroContext.sourcePosition, module, name, type)
    )

def fromExternalImportWithType(macroContext: MacroContext, externalName: ASTNode, name: ASTNode, type: ASTNode) -> ASTNode:
    return fromExternalImportAsWithType(macroContext, externalName, name, name, type)

def fromExternalImportAsWithType(macroContext: MacroContext, externalName: ASTNode, name: ASTNode, importedName: ASTNode, type: ASTNode) -> ASTNode:
    return ASTBindingDefinitionNode(macroContext.sourcePosition, importedName, None, 
        ASTFromExternalImportWithTypeNode(macroContext.sourcePosition, externalName, name, type)
    )

def moduleExportWithMacro(macroContext: MacroContext, name: ASTNode, value: ASTNode) -> ASTNode:
    return ASTModuleExportValueNode(macroContext.sourcePosition, None, name, value)

def moduleExportMacro(macroContext: MacroContext, value: ASTNode) -> ASTNode:
    if value.isSequenceNode():
        return ASTSequenceNode(macroContext.sourcePosition, list(map(lambda n: moduleExportMacro(macroContext, n), value.elements)))

    return ASTModuleExportValueNode(macroContext.sourcePosition, None, value.parseAsExportedNameSymbol(), value)

def moduleExternalExportWithMacro(macroContext: MacroContext, externalName: ASTNode, name: ASTNode, value: ASTNode) -> ASTNode:
    return ASTModuleExportValueNode(macroContext.sourcePosition, externalName, name, value)

def moduleExternalExportMacro(macroContext: MacroContext, externalName: ASTNode, value: ASTNode) -> ASTNode:
    if value.isSequenceNode():
        return ASTSequenceNode(macroContext.sourcePosition, list(map(lambda n: moduleExternalExportWithMacro(macroContext, externalName, n), value.elements)))
    return ASTModuleExportValueNode(macroContext.sourcePosition, externalName, value.parseAsExportedNameSymbol(), value)

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

def formMutableTypeMacro(macroContext: MacroContext, baseType: ASTNode):
    return ASTFormDecoratedTypeNode(macroContext.sourcePosition, baseType, DecoratedType.Mutable)

def formVolatileTypeMacro(macroContext: MacroContext, baseType: ASTNode):
    return ASTFormDecoratedTypeNode(macroContext.sourcePosition, baseType, DecoratedType.Volatile)

def formArrayTypeMacro(macroContext: MacroContext, elementType: ASTNode, size: ASTNode):
    return ASTFormArrayTypeNode(macroContext.sourcePosition, elementType, size)

def formPointerTypeMacro(macroContext: MacroContext, baseType: ASTNode):
    return ASTFormPointerTypeNode(macroContext.sourcePosition, baseType)

def formReferenceTypeMacro(macroContext: MacroContext, baseType: ASTNode):
    return ASTFormReferenceTypeNode(macroContext.sourcePosition, baseType)

def formTemporaryReferenceTypeMacro(macroContext: MacroContext, baseType: ASTNode):
    return ASTFormTemporaryReferenceTypeNode(macroContext.sourcePosition, baseType)

def pointerLikeLoadMacro(macroContext: MacroContext, pointer: ASTTypedNode):
    return ASTPointerLikeLoadNode(macroContext.sourcePosition, pointer)

def pointerLikeStoreMacro(macroContext: MacroContext, pointer: ASTTypedNode, value: ASTNode):
    return ASTPointerLikeStoreNode(macroContext.sourcePosition, pointer, value, False)

def pointerLikeAsPointerMacro(macroContext: MacroContext, pointer: ASTTypedNode):
    baseType = pointer.type.getBaseTypeExpressionAt(macroContext.sourcePosition)
    pointerType = ASTFormPointerTypeNode(macroContext.sourcePosition, baseType)
    return ASTPointerLikeReinterpretToNode(macroContext.sourcePosition, pointer, pointerType)

def pointerLikeAsRefMacro(macroContext: MacroContext, pointer: ASTTypedNode):
    baseType = pointer.type.getBaseTypeExpressionAt(macroContext.sourcePosition)
    referenceType = ASTFormReferenceTypeNode(macroContext.sourcePosition, baseType)
    return ASTPointerLikeReinterpretToNode(macroContext.sourcePosition, pointer, referenceType)

def pointerLikeAtMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTPointerLikeLoadNode(macroContext.sourcePosition, ASTPointerLikeSubscriptAtNode(macroContext.sourcePosition, pointer, False))

def pointerLikeAtPutMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode, value: ASTNode):
    return ASTPointerLikeStoreNode(macroContext.sourcePosition, ASTPointerLikeSubscriptAtNode(macroContext.sourcePosition, pointer, index, False), value, False)

def pointerLikeSubscriptAtMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTPointerLikeSubscriptAtNode(macroContext.sourcePosition, pointer, index, True)

def pointerLikePlusMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTPointerLikeSubscriptAtNode(macroContext.sourcePosition, pointer, index, False)

def referenceLikeAssignmentMacro(macroContext: MacroContext, reference: ASTTypedNode, value: ASTNode):
    return ASTPointerLikeStoreNode(macroContext.sourcePosition, reference, value, True)

def arrayAtMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTArraySubscriptAtNode(macroContext.sourcePosition, pointer, index, False, False)

def arraySubscriptAtMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTArraySubscriptAtNode(macroContext.sourcePosition, pointer, index, True, False)

def arrayPlusMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTArraySubscriptAtNode(macroContext.sourcePosition, pointer, index, False, True)

def arrayAtPutMacro(macroContext: MacroContext, pointer: ASTTypedNode, index: ASTNode):
    return ASTPointerLikeStoreNode(macroContext.sourcePosition, pointer, index, True)

def formSumPairMacro(macroContext: MacroContext, left: ASTTypedNode, right: ASTNode):
    return ASTFormSumTypeNode(macroContext.sourcePosition, [left, right])

ArrayTypeMacros = {}
for name, expander in [
    ('at:', arrayAtMacro),
    ('at:put:', arrayAtPutMacro),
    ('+', arrayPlusMacro),
    ('[]:', arraySubscriptAtMacro),
]:
    ArrayTypeMacros[Symbol.intern(name)] = expander

PointerTypeMacros = {}
for name, expander in [
    ('load', pointerLikeLoadMacro),
    ('store:', pointerLikeStoreMacro),
    ('at:', pointerLikeAtMacro),
    ('at:put:', pointerLikeAtPutMacro),
    ('[]:', pointerLikeSubscriptAtMacro),
    ('+', pointerLikePlusMacro),
    ('_', pointerLikeAsRefMacro),
]:
    PointerTypeMacros[Symbol.intern(name)] = expander

ReferenceLikeTypeMacros = {}
for name, expander in [
    ('__refLoad__', pointerLikeLoadMacro),
    ('__refStore__:', pointerLikeStoreMacro),
    ('address', pointerLikeAsPointerMacro),
    (':=', referenceLikeAssignmentMacro),
]:
    ReferenceLikeTypeMacros[Symbol.intern(name)] = expander

TypeMacros = {}
for name, expander in [
    ('mutable', formMutableTypeMacro),
    ('volatile', formVolatileTypeMacro),
    ('array:', formArrayTypeMacro),
    ('[]:', formArrayTypeMacro),
    ('pointer', formPointerTypeMacro),
    ('ref', formReferenceTypeMacro),
    ('tempRef', formTemporaryReferenceTypeMacro),
    ('|', formSumPairMacro),
]:
    TypeMacros[Symbol.intern(name)] = expander

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
for baseType in [
        AbortType, VoidType, AnyType,
        CVarArgType,
        IntegerType, StringType, FalseType, TrueType, BooleanType,
        Int8Type, Int16Type, Int32Type, Int64Type,
        UInt8Type, UInt16Type, UInt32Type, UInt64Type,
        SizeType, SignedSizeType, UIntPointerType, IntPointerType,
        Char8Type, Char16Type, Char32Type,
        Float32Type, Float64Type,

        Float32x2Type, Float32x3Type, Float32x4Type,
        Float64x2Type, Float64x3Type, Float64x4Type,
        Int32x2Type, Int32x3Type, Int32x4Type,
        UInt32x2Type, UInt32x3Type, UInt32x4Type,

        ASTNodeType, 
    ]:
    TopLevelEnvironment = TopLevelEnvironment.withBaseType(baseType)
TopLevelEnvironment = TopLevelEnvironment.withVoidTypeValue(VoidType.getSingleton())

TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
    ['let:type:with:', 'Macro::let:type:with:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], letTypeWithMacro, ['macro']],
    ['let:with:', 'Macro::let:with:',[(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], letWithMacro, ['macro']],
    ['let:type:mutableWith:', 'Macro::let:type:mutableWith:',[(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], letTypeMutableWithMacro, ['macro']],
    ['let:mutableWith:', 'Macro::let:mutableWith:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], letMutableWithMacro, ['macro']],

    ['public:type:with:', 'Macro::public:type:with:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], publicTypeWithMacro, ['macro']],
    ['public:with:', 'Macro::public:with:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], publicWithMacro, ['macro']],
    ['public:type:mutableWith:', 'Macro::public:type:mutableWith:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], publicTypeMutableWithMacro, ['macro']],
    ['public:mutableWith:', 'Macro::public:mutableWith:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], publicMutableWithMacro, ['macro']],

    ['if:then:', 'Macro::if:then:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], ifThenMacro, ['macro']],
    ['if:then:else:', 'Macro::if:then:else:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], ifThenElseMacro, ['macro']],
    ['while:do:', 'Macro::while:do:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], whileDoMacro, ['macro']],
    ['while:do:continueWith:', 'Macro::while:do:continueWith:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], whileDoContinueWithMacro, ['macro']],
    ['do:while:', 'Macro::do:while:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], doWhileMacro, ['macro']],
    ['do:while:continueWith:', 'Macro::do:while:continueWith:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], doWhileContinueWithMacro, ['macro']],

    ['loadSourceNamed:', 'Macro::loadSourceNamed:', [(MacroContextType, ASTNodeType), ASTNodeType], loadSourceNamedMacro, ['macro']],

    ['importModule:', 'Macro::importModule:', [(MacroContextType, ASTNodeType), ASTNodeType], importModuleMacro, ['macro']],
    ['fromModule:import:withType:', 'Macro::fromModule:import:withType:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], fromModuleImportWithType, ['macro']],
    ['fromModule:import:as:withType:', 'Macro::fromModule:import:withType:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], fromModuleImportAsWithType, ['macro']],
    ['fromExternal:import:withType:', 'Macro::fromModule:import:withType:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], fromExternalImportWithType, ['macro']],
    ['fromExternal:import:as:withType:', 'Macro::fromModule:import:withType:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], fromExternalImportAsWithType, ['macro']],
    ['export:with:', 'Macro::export:with:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], moduleExportWithMacro, ['macro']],
    ['export:', 'Macro::export:', [(MacroContextType, ASTNodeType), ASTNodeType], moduleExportMacro, ['macro']],
    ['external:export:with:', 'Macro::external:export:with:', [(MacroContextType, ASTNodeType, ASTNodeType, ASTNodeType), ASTNodeType], moduleExternalExportWithMacro, ['macro']],
    ['external:export:', 'Macro::external:export:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], moduleExternalExportMacro, ['macro']],
    ['moduleEntryPoint:', 'Macro::moduleEntryPoint:', [(MacroContextType, ASTNodeType), ASTNodeType], moduleEntryPointMacro, ['macro']],

    ['=>', 'Type::=>', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], arrowMacro, ['macro']],
    ['RecordWithFields:', 'Type::RecordWithFields:', [(MacroContextType, ASTNodeType), ASTNodeType], formRecordWithFieldsMacro, ['macro']],
    ['Record:withFields:', 'Type::Record:withFields:', [(MacroContextType, ASTNodeType, ASTNodeType), ASTNodeType], formNamedRecordWithFieldsMacro, ['macro']],

    ['__cdecl', 'Type::__cdecl', [(MacroContextType, ASTNodeType), ASTNodeType], cdeclMacro, ['macro']],
    ['__stdcall', 'Type::__stdcall', [(MacroContextType, ASTNodeType), ASTNodeType], stdcallMacro, ['macro']],
    ['__apicall', 'Type::__apicall', [(MacroContextType, ASTNodeType), ASTNodeType], apicallMacro, ['macro']],
    ['__thiscall', 'Type::__thiscall', [(MacroContextType, ASTNodeType), ASTNodeType], thiscallMacro, ['macro']],
    ['__vectorcall', 'Type::__vectorcall', [(MacroContextType, ASTNodeType), ASTNodeType], vectorcallMacro, ['macro']],
], TopLevelEnvironment)

for primitiveNumberType in NumberTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['negated', prefix + 'negated', [primitiveNumberType, primitiveNumberType], lambda x: -x, ['pure']],

        ['+', prefix + '+',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x + y, ['pure']],
        ['-', prefix + '-',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x - y, ['pure']],
        ['*', prefix + '*',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x * y, ['pure']],

        ['=',  prefix + '=',  [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.equals(y),          ['pure']],
        ['~=', prefix + '~=', [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.notEquals(y),       ['pure']],
        ['<',  prefix + '<',  [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.lessThan(y),        ['pure']],
        ['<=', prefix + '<=', [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.lessOrEquals(y),    ['pure']],
        ['>',  prefix + '>',  [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.greaterThan(y),     ['pure']],
        ['>=', prefix + '>=', [(primitiveNumberType, primitiveNumberType), BooleanType], lambda x, y: x.greaterOrEquals(y), ['pure']],

        ['min:', prefix + 'min:',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x.minWith(y), ['pure']],
        ['max:', prefix + 'max:',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x.maxWith(y), ['pure']],

        ['asInt8',  prefix + 'asInt8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), ['pure']],
        ['asInt16', prefix + 'asInt16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), ['pure']],
        ['asInt32', prefix + 'asInt32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), ['pure']],
        ['asInt64', prefix + 'asInt64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), ['pure']],

        ['asUInt8',  prefix + 'asUInt8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), ['pure']],
        ['asUInt16', prefix + 'asUInt16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), ['pure']],
        ['asUInt32', prefix + 'asUInt32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), ['pure']],
        ['asUInt64', prefix + 'asUInt64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), ['pure']],

        ['asSize',        prefix + 'asSize',        [primitiveNumberType, SizeType       ], lambda x: x.castToPrimitiveIntegerType(       SizeType), ['pure']],
        ['asSignedSize',  prefix + 'asSignedSize',  [primitiveNumberType, SignedSizeType ], lambda x: x.castToPrimitiveIntegerType( SignedSizeType), ['pure']],
        ['asUIntPointer', prefix + 'asUIntPointer', [primitiveNumberType, UIntPointerType], lambda x: x.castToPrimitiveIntegerType(UIntPointerType), ['pure']],
        ['asIntPointer',  prefix + 'asIntPointer',  [primitiveNumberType, IntPointerType ], lambda x: x.castToPrimitiveIntegerType( IntPointerType), ['pure']],

        ['asChar8',  prefix + 'asChar8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), ['pure']],
        ['asChar16', prefix + 'asChar16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), ['pure']],
        ['asChar32', prefix + 'asChar32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), ['pure']],

        ['asFloat32', prefix + 'asFloat32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), ['pure']],
        ['asFloat64', prefix + 'asFloat64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), ['pure']],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType] + PrimitiveIntegerTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['bitInvert', prefix + 'bitInvert',  [primitiveNumberType, primitiveNumberType], lambda x: ~x, ['pure']],

        ['&', prefix + '&',    [primitiveNumberType, primitiveNumberType], lambda x, y: x & y,  ['pure']],
        ['|', prefix + '|',    [primitiveNumberType, primitiveNumberType], lambda x, y: x | y,  ['pure']],
        ['^', prefix + '^',    [primitiveNumberType, primitiveNumberType], lambda x, y: x ^ y,  ['pure']],
        ['<<', prefix + '<<',  [primitiveNumberType, primitiveNumberType], lambda x, y: x << y, ['pure']],
        ['>>', prefix + '>>',  [primitiveNumberType, primitiveNumberType], lambda x, y: x >> y, ['pure']],

        ['//', prefix + '//',  [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x.quotientWith(y),  ['pure']],
        ['%', prefix + '%',    [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x.remainderWith(y), ['pure']],
    ], TopLevelEnvironment)

for primitiveNumberType in PrimitiveFloatTypes:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['/',         prefix + '/',         [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x / y, ['pure']],
        ['sqrt',      prefix + 'sqrt',      [primitiveNumberType, primitiveNumberType], lambda x: x.sqrt(),      ['pure']],
        ['rounded',   prefix + 'rounded',   [primitiveNumberType, primitiveNumberType], lambda x: x.rounded(),   ['pure']],
        ['floor',     prefix + 'floor',     [primitiveNumberType, primitiveNumberType], lambda x: x.floor(),     ['pure']],
        ['ceil',      prefix + 'ceil',      [primitiveNumberType, primitiveNumberType], lambda x: x.ceil(),      ['pure']],
        ['truncated', prefix + 'truncated', [primitiveNumberType, primitiveNumberType], lambda x: x.truncated(), ['pure']],
    ], TopLevelEnvironment)

for primitiveNumberType in [IntegerType, Char32Type, Float64Type]:
    prefix = primitiveNumberType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['i8',  prefix + 'asInt8',  [primitiveNumberType,  Int8Type], lambda x: x.castToPrimitiveIntegerType( Int8Type), ['pure']],
        ['i16', prefix + 'asInt16', [primitiveNumberType, Int16Type], lambda x: x.castToPrimitiveIntegerType(Int16Type), ['pure']],
        ['i32', prefix + 'asInt32', [primitiveNumberType, Int32Type], lambda x: x.castToPrimitiveIntegerType(Int32Type), ['pure']],
        ['i64', prefix + 'asInt64', [primitiveNumberType, Int64Type], lambda x: x.castToPrimitiveIntegerType(Int64Type), ['pure']],

        ['u8',  prefix + 'asUInt8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveIntegerType( UInt8Type), ['pure']],
        ['u16', prefix + 'asUInt16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveIntegerType(UInt16Type), ['pure']],
        ['u32', prefix + 'asUInt32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveIntegerType(UInt32Type), ['pure']],
        ['u64', prefix + 'asUInt64', [primitiveNumberType, UInt64Type], lambda x: x.castToPrimitiveIntegerType(UInt64Type), ['pure']],

        ['sz',   prefix + 'asSize',        [primitiveNumberType, SizeType       ], lambda x: x.castToPrimitiveIntegerType(       SizeType), ['pure']],
        ['ssz',  prefix + 'asSignedSize',  [primitiveNumberType, SignedSizeType ], lambda x: x.castToPrimitiveIntegerType( SignedSizeType), ['pure']],
        ['uptr', prefix + 'asUIntPointer', [primitiveNumberType, UIntPointerType], lambda x: x.castToPrimitiveIntegerType(UIntPointerType), ['pure']],
        ['iptr', prefix + 'asIntPointer',  [primitiveNumberType, IntPointerType ], lambda x: x.castToPrimitiveIntegerType( IntPointerType), ['pure']],

        ['c8',  prefix + 'asChar8',  [primitiveNumberType,  UInt8Type], lambda x: x.castToPrimitiveCharacterType( Char8Type), ['pure']],
        ['c16', prefix + 'asChar16', [primitiveNumberType, UInt16Type], lambda x: x.castToPrimitiveCharacterType(Char16Type), ['pure']],
        ['c32', prefix + 'asChar32', [primitiveNumberType, UInt32Type], lambda x: x.castToPrimitiveCharacterType(Char32Type), ['pure']],

        ['f32', prefix + 'asFloat32', [primitiveNumberType, Float32Type], lambda x: x.castToPrimitiveFloatType(Float32Type), ['pure']],
        ['f64', prefix + 'asFloat64', [primitiveNumberType, Float64Type], lambda x: x.castToPrimitiveFloatType(Float64Type), ['pure']],
    ], TopLevelEnvironment)

for primitiveVectorType in PrimitiveVectorTypes:
    prefix = primitiveVectorType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['negated', prefix + 'negated', [primitiveVectorType, primitiveVectorType], lambda x: -x, ['pure']],

        ['+', prefix + '+',  [(primitiveVectorType, primitiveVectorType), primitiveVectorType], lambda x, y: x + y, ['pure']],
        ['-', prefix + '-',  [(primitiveVectorType, primitiveVectorType), primitiveVectorType], lambda x, y: x - y, ['pure']],
        ['*', prefix + '*',  [(primitiveVectorType, primitiveVectorType), primitiveVectorType], lambda x, y: x * y, ['pure']],

        ['min:', prefix + 'min:',  [(primitiveVectorType, primitiveVectorType), primitiveVectorType], lambda x, y: x.minWith(y), ['pure']],
        ['max:', prefix + 'max:',  [(primitiveVectorType, primitiveVectorType), primitiveVectorType], lambda x, y: x.maxWith(y), ['pure']],
    ], TopLevelEnvironment)

for primitiveVectorType in PrimitiveFloatVectorTypes:
    prefix = primitiveVectorType.name + "::"
    TopLevelEnvironment = addPrimitiveFunctionDefinitionsToEnvironment([
        ['/',         prefix + '/',         [(primitiveNumberType, primitiveNumberType), primitiveNumberType], lambda x, y: x / y, ['pure']],
        ['sqrt',      prefix + 'sqrt',      [primitiveNumberType, primitiveNumberType], lambda x: x.sqrt(),      ['pure']],
        ['rounded',   prefix + 'rounded',   [primitiveNumberType, primitiveNumberType], lambda x: x.rounded(),   ['pure']],
        ['floor',     prefix + 'floor',     [primitiveNumberType, primitiveNumberType], lambda x: x.floor(),     ['pure']],
        ['ceil',      prefix + 'ceil',      [primitiveNumberType, primitiveNumberType], lambda x: x.ceil(),      ['pure']],
        ['truncated', prefix + 'truncated', [primitiveNumberType, primitiveNumberType], lambda x: x.truncated(), ['pure']],
    ], TopLevelEnvironment)

TopLevelEnvironment = TopLevelEnvironment.withVoidTypeValue(FalseType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withVoidTypeValue(TrueType.getSingleton())
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment = TopLevelEnvironment.withSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeScriptAnalysisEnvironment(module: Module, sourcePosition: SourcePosition, scriptPath: str) -> LexicalEnvironment:
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ScriptEnvironment(ModuleEnvironment(TopLevelEnvironment, module), sourcePosition, scriptDirectory, scriptName)
