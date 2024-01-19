from abc import ABC, abstractmethod
import json
from typing import Any

class TypedValue(ABC):
    @abstractmethod
    def getType(self):
        pass

    @abstractmethod
    def toJson(self):
        pass

    def isSubtypeOf(self, otherType) -> bool:
        return False
    
    def isTypeUniverse(self) -> bool:
        return False

    def isType(self) -> bool:
        return self.getType().isTypeUniverse()
    
    def isTypeSatisfiedBy(self, otherType) -> bool:
        return self.isSubtypeOf(otherType)

    def getTypeUniverseIndex(self) -> int:
        return 0
    
    def isPi(self) -> bool:
        return False

    def isEquivalentTo(self, other) -> bool:
        return self == other

    def isFunctionalValue(self) -> bool:
        return False

    def isPurelyFunction(self) -> bool:
        return False

class TypeUniverse(TypedValue):
    InstancedUniverses = dict()
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def toJson(self):
        if self.index == 0: return "Type"
        return "Type@%d" % self.index
    
    def getType(self):
        return self.__class__.getWithIndex(self.index + 1)

    @classmethod
    def getWithIndex(cls, index):
        if index in cls.InstancedUniverses:
            return cls.InstancedUniverses[index]
        
        universe = cls(index)
        cls.InstancedUniverses[index] = universe
        return universe

    def isType(self) -> bool:
        return True

    def isTypeUniverse(self) -> bool:
        return True

    def getTypeUniverseIndex(self) -> int:
        return self.index

TypeType = TypeUniverse.getWithIndex(0)

class BaseType(TypedValue):
    def __init__(self, name: str) -> None:
        self.name = name

    def getType(self) -> TypedValue:
        return TypeType

    def toJson(self):
        return self.name
        
    def isSubtypeOf(self, otherType: TypedValue) -> bool:
        if otherType.isTypeUniverse():
            return True
        return self == otherType

class AbsurdTypeClass(BaseType):
    pass

class UnitTypeValue(TypedValue):
    def __init__(self, type: BaseType, name: str) -> None:
        super().__init__()
        self.type = type
        self.name = name

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return self.type.isEquivalentTo(other.getType())
    
    def getType(self) -> TypedValue:
        return self.type

    def toJson(self):
        if self.name is None:
            return str(self.type) + ".value"
        return self.name
    
class UnitTypeClass(BaseType):
    def __init__(self, name: str, valueName: str) -> None:
        super().__init__(name)
        self.singleton = UnitTypeValue(self, valueName)

    def getSingleton(self) -> UnitTypeValue:
        return self.singleton

class NatTypeClass(BaseType):
    pass

class IntegerTypeClass(BaseType):
    pass

class FloatTypeClass(BaseType):
    pass

class CharacterTypeClass(BaseType):
    pass

class StringTypeClass(BaseType):
    pass

class ASTNodeTypeClass(BaseType):
    pass

AbsurdType = AbsurdTypeClass("Absurd")
UnitType = UnitTypeClass("Unit", "unit")

NatType = IntegerTypeClass("Nat")
IntegerType = IntegerTypeClass("Integer")
FloatType = FloatTypeClass("Float")
CharacterType = CharacterTypeClass("Character")
StringType = StringTypeClass("String")
ASTNodeType = ASTNodeTypeClass("ASTNode")

class NatValue(TypedValue):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def getType(self) -> TypedValue:
        return NatType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value
    
    def __add__(self, other):
        return NatValue(self.value + other.value)

    def __sub__(self, other):
        result = self.value - other.value
        if result < 0:
            raise Exception("Nat underflow")

        return NatValue(result)

    def __mul__(self, other):
        return NatValue(self.value * other.value)

    def __div__(self, other):
        return NatValue(self.value / other.value)

class IntegerValue(TypedValue):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def getType(self) -> TypedValue:
        return IntegerType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

    def __add__(self, other):
        return IntegerValue(self.value + other.value)

    def __sub__(self, other):
        return IntegerValue(self.value - other.value)

    def __mul__(self, other):
        return IntegerValue(self.value * other.value)

    def __div__(self, other):
        return IntegerValue(self.value / other.value)
    
class FloatValue(TypedValue):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def getType(self):
        return FloatType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

    def __add__(self, other):
        return FloatValue(self.value + other.value)

    def __sub__(self, other):
        return FloatValue(self.value - other.value)

    def __mul__(self, other):
        return FloatValue(self.value * other.value)

    def __div__(self, other):
        return FloatValue(self.value / other.value)
    
class CharacterValue(TypedValue):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def getType(self):
        return CharacterType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

    def __add__(self, other):
        return CharacterValue(self.value + other.value)

    def __sub__(self, other):
        return CharacterValue(self.value - other.value)

    def __mul__(self, other):
        return CharacterValue(self.value * other.value)

    def __div__(self, other):
        return CharacterValue(self.value / other.value)
    
class StringValue(TypedValue):
    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = str

    def getType(self):
        return StringType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

class ProductTypeValue(TypedValue):
    def __init__(self, type: TypedValue, elements: tuple) -> None:
        super().__init__()
        self.elements = elements
        self.type = type

    def getType(self):
        return self.type

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not self.type.isEquivalentTo(other.getType()): return False
        if len(self.elements) != len(other.elements): return False
        for i in range(len(self.elements)):
            if not self.elements[i].isEquivalentTo(other.elements[i]):
                return False

        return True

    def toJson(self):
        return {'product': list(map(lambda v: v.toJson(), self.elements))}

class ProductType(BaseType):
    ProductTypeCache = dict()

    def __init__(self, elementTypes: list[TypedValue]) -> None:
        self.elementTypes = elementTypes

    def makeWithElements(self, elements) -> ProductTypeValue:
        return ProductTypeValue(self, elements)

    def getType(self):
        return TypeType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, ProductType): return False

        if len(self.elementTypes) != len(other.elementTypes): return False
        for i in range(len(self.elementTypes)):
            if not self.elementTypes[i].isEquivalentTo(other.elementTypes[i]):
                return False

        return True

    def toJson(self):
        return {'productType': list(map(lambda v: v.toJson(), self.elementTypes))}
    
    @classmethod
    def makeWithElementTypes(cls, elementTypes: list[TypedValue]):
        productKey = tuple(elementTypes)
        if productKey in cls.ProductTypeCache:
            return cls.ProductTypeCache[productKey]

        productType = cls(productKey)
        cls.ProductTypeCache[productKey] = productType
        return productType

class RecordTypeValue(ProductTypeValue):
    def toJson(self):
        result = dict()
        for i in range(len(self.elements)):
            result[self.type.fields[i]] = self.elements[i]

        return result
    
class RecordType(ProductType):
    def __init__(self, elementTypes: list[TypedValue], fields: list[TypedValue]) -> None:
        self.elementTypes = elementTypes
        self.fields = fields

    def makeWithElements(self, elements) -> RecordTypeValue:
        return RecordTypeValue(self, elements)
    
    def toJson(self):
        return {'recordType': list(map(lambda v: v.toJson(), self.elementTypes)), 'fields' : list(map(lambda v: v.toJson(), self.fields))}

class SumTypeValue(TypedValue):
    def __init__(self, type: TypedValue, variantIndex: int, value: TypedValue) -> None:
        super().__init__()
        self.type = type
        self.variantIndex = variantIndex
        self.value = value

    def getType(self):
        return self.type

    def toJson(self):
        return {'sum': self.typeIndex, 'value': self.value.toJson}

class SumType(BaseType):
    SumTypeCache = dict()

    def __init__(self, variantTypes: list[TypedValue]) -> None:
        self.variantTypes = variantTypes

    def makeWithTypeIndexAndValue(self, variantIndex: int, value: TypedValue) -> SumTypeValue:
        return SumTypeValue(self, variantIndex, value)

    def getType(self):
        return TypeType

    def toJson(self):
        return {'sumType': list(map(lambda v: v.toJson(), self.variantTypes))}
    
    @classmethod
    def makeWithVariantTypes(cls, variantTypes: list[TypedValue]):
        key = tuple(variantTypes)
        if key in cls.SumTypeCache:
            return cls.SumTypeCache[key]

        sumType = cls(key)
        cls.SumTypeCache[key] = sumType
        return sumType
    
class SymbolTypeClass(BaseType):
    pass

SymbolType = SymbolTypeClass("Symbol")

class Symbol(TypedValue):
    InternedSymbolDictionary = dict()

    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return '#' + repr(self.value)
    
    def __str__(self) -> str:
        return '#' + repr(self.value)

    @classmethod
    def intern(cls, value: str):
        if value in cls.InternedSymbolDictionary:
            return cls.InternedSymbolDictionary[value]
        
        newSymbol = cls(value)
        cls.InternedSymbolDictionary[value] = newSymbol
        return newSymbol

    def getType(self):
        return SymbolType

    def toJson(self):
        return repr(self)

class SourceCode:
    def __init__(self, name: str, text: bytes) -> None:
        self.name = name
        self.text = text

    def __str__(self) -> str:
        return self.name

class SourcePosition:
    def __init__(self, sourceCode: SourceCode, startIndex: int, endIndex: int, startLine: int, startColumn: int, endLine: int, endColumn: int) -> None:
        self.sourceCode = sourceCode
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.startLine = startLine
        self.startColumn = startColumn
        self.endLine = endLine
        self.endColumn = endColumn

    def getValue(self) -> bytes:
        return self.sourceCode.text[self.startIndex : self.endIndex]
    
    def getStringValue(self) -> str:
        return self.getValue().decode('utf-8')
    
    def until(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.startIndex,
                self.startLine, self.startColumn,
                endSourcePosition.startLine, endSourcePosition.startColumn)

    def to(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.endIndex,
                self.startLine, self.startColumn,
                endSourcePosition.endLine, endSourcePosition.endColumn)

    def __str__(self) -> str:
        return '%s:%d.%d-%d.%d' % (self.sourceCode, self.startLine, self.startColumn, self.endLine, self.endColumn)

class EmptySourcePosition:
    def __str__(self) -> str:
        return '<no position>'

class ASTNode(TypedValue):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

    def getType(self):
        return ASTNodeType
    
    def prettyPrint(self) -> str:
        return json.dumps(self.toJson())

    def isEquivalentTo(self, other) -> bool:
        return self == other

    def isLiteralTypeNode(self) -> bool:
        return False

    def isTypedIdentifierReferenceNode(self) -> bool:
        return False

    def isTypedLiteralNode(self) -> bool:
        return False
    
    def isTypedErrorNode(self) -> bool:
        return False
    
    def isPiLiteralValue(self) -> bool:
        return False

    def isTypedFunctionalNode(self) -> bool:
        return False

    def isTypedPiNode(self) -> bool:
        return False

    def isTypedPiNodeOrLiteralValue(self) -> bool:
        return self.isPiLiteralValue() or self.isTypedPiNode()

    def isTypedLambdaNode(self) -> bool:
        return False

class ASTLiteralTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def prettyPrint(self) -> str:
        return str(self.value)

    def computeTypeUniverseIndex(self) -> int:
        return self.value.getTypeUniverseIndex()

    def isEquivalentTo(self, other: ASTNode) -> bool:
        if self == other:
            return True
        elif other.isLiteralTypeNode():
            return self.value.isEquivalentTo(other.value)
        elif other.isTypedLiteralNode():
            return self.value.isEquivalentTo(other.value)
        else:
            return False
    
    def isLiteralTypeNode(self) -> bool:
        return True

    def isPiLiteralValue(self) -> bool:
        return self.value.isPi()

    def accept(self, visitor):
        return visitor.visitLiteralTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'LiteralType', 'value': self.value.toJson()}

class ASTTypedNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.type = type

    def computeTypeUniverseIndex(self) -> int:
        return self.type.computeTypeUniverseIndex()

class ASTTypedLiteralNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, value: TypedValue) -> None:
        super().__init__(sourcePosition, type)
        self.value = value

    def prettyPrint(self) -> str:
        return str(self.value)

    def isTypedLiteralNode(self) -> bool:
        return True

    def isPiLiteralValue(self) -> bool:
        return self.value.isPi()

    def isEquivalentTo(self, other: ASTNode) -> bool:
        if self == other:
            return True
        elif other.isLiteralTypeNode():
            return self.value.isEquivalentTo(other.value)
        elif other.isTypedLiteralNode():
            return self.value.isEquivalentTo(other.value)
        else:
            return False
        
    def accept(self, visitor):
        return visitor.visitTypedLiteralNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedLiteral', 'type': self.type.toJson(), 'value': self.value.toJson()}

class SymbolBinding(ABC):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol) -> None:
        super().__init__()
        self.sourcePosition = sourcePosition
        self.name = name

    def evaluateInActivationEnvironmentAt(self, activationEnvironment, sourcePosition: SourcePosition) -> TypedValue:
        return activationEnvironment.lookBindingValueAt(self, sourcePosition)

    def evaluateSubstitutionInContextFor(self, substitutionContext, oldNode: ASTTypedNode) -> ASTTypedNode:
        return substitutionContext.lookSubstitutionForBindingInNode(self, oldNode)

    @abstractmethod
    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        pass

    def getCanonicalBinding(self):
        return self

    def isCanonicalEquivalentTo(self, other) -> bool:
        return self == other

    def isEquivalentTo(self, other) -> bool:
        if self == other: return True
        if not isinstance(other, SymbolBinding): return False
        return self.getCanonicalBinding().isCanonicalEquivalentTo(other.getCanonicalBinding())

    def isValueBinding(self) -> bool:
        return False

    ## The nesting level of the capture. This corresponds with the Bruijn index of the binding if lambdas only have a single argument.
    @abstractmethod
    def getCaptureNestingLevel(self) -> int:
        pass

class ASTTypedIdentifierReferenceNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, binding: SymbolBinding) -> None:
        super().__init__(sourcePosition, type)
        self.binding = binding

    def isEquivalentTo(self, other) -> bool:
        if self == other: return True
        if not isinstance(other, self.__class__): return False
        return self.binding.isEquivalentTo(other.binding)

    def isTypedIdentifierReferenceNode(self) -> bool:
        return True

    def accept(self, visitor):
        return visitor.visitTypedIdentifierReferenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedIdentifierReference', 'type': self.type.toJson(), 'binding': self.binding.toJson()}

class SymbolValueBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, value: TypedValue) -> None:
        super().__init__(sourcePosition, name)
        self.value = value
        self.typeExpression = ASTLiteralTypeNode(sourcePosition, self.value.getType())

    def evaluateInActivationEnvironmentAt(self, activationEnvironment, sourcePosition: SourcePosition) -> TypedValue:
        return self.value

    def evaluateSubstitutionInContextAt(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode | ASTLiteralTypeNode:
        if self.value.isType():
            return ASTLiteralTypeNode(sourcePosition, self.value)
        return ASTTypedLiteralNode(sourcePosition, self.getTypeExpression(), self.value)

    def getTypeExpression(self) -> TypedValue:
        return self.typeExpression

    def isValueBinding(self) -> bool:
        return True
    
    def getCaptureNestingLevel(self) -> int:
        return 0

class SymbolArgumentBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTLiteralTypeNode | ASTTypedNode) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression

    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 1

    def toJson(self):
        return {'name': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

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
    ['+', [NatType, NatType, NatType], lambda x, y: x + y],
    ['+', [IntegerType, IntegerType, IntegerType], lambda x, y: x + y],
    ['+', [FloatType, FloatType, FloatType], lambda x, y: x + y]
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