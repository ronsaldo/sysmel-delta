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

    def isASTNode(self):
        return False
    
    def isSymbolBinding(self):
        return False

    def isOverloadsType(self) -> bool:
        return False

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

    def isMacroValue(self) -> bool:
        return False

    def isPurelyFunction(self) -> bool:
        return False
    
    def expectsMacroEvaluationContext(self) -> bool:
        return False
    
    def isDecoratedType(self) -> bool:
        return False

    def isArrayType(self) -> bool:
        return False

    def isPointerType(self) -> bool:
        return False

    def isReferenceType(self) -> bool:
        return False

    def isTemporaryReferenceType(self) -> bool:
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

class MacroContextTypeClass(BaseType):
    pass

class PrimitiveIntegerTypeClass(BaseType):
    def __init__(self, name: str, valueSize: int) -> None:
        super().__init__(name)
        self.valueSize = valueSize

    @abstractmethod
    def normalizeIntegerValue(self, value: int) -> int:
        pass

class PrimitiveUnsignedIntegerTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, valueSize: int) -> None:
        super().__init__(name, valueSize)
        self.mask = (1<<(valueSize*8)) - 1

    def normalizeIntegerValue(self, value: int) -> int:
        return value & self.mask

class PrimitiveSignedIntegerTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, valueSize: int) -> None:
        super().__init__(name, valueSize)
        self.mask = (1<<(valueSize*8)) - 1
        self.signBitMask = 1<<(valueSize*8 - 1)

    def normalizeIntegerValue(self, value: int) -> int:
        return (value & (self.signBitMask - 1)) - (value & self.signBitMask)

AbsurdType = AbsurdTypeClass("Absurd")
UnitType = UnitTypeClass("Unit", "unit")

IntegerType = IntegerTypeClass("Integer")
FloatType = FloatTypeClass("Float")
CharacterType = CharacterTypeClass("Character")
StringType = StringTypeClass("String")
ASTNodeType = ASTNodeTypeClass("ASTNode")
MacroContextType = MacroContextTypeClass("MacroContext")

Int8Type  = PrimitiveSignedIntegerTypeClass("Int8", 1)
Int16Type = PrimitiveSignedIntegerTypeClass("Int16", 2)
Int32Type = PrimitiveSignedIntegerTypeClass("Int32", 4)
Int64Type = PrimitiveSignedIntegerTypeClass("Int64", 8)

UInt8Type  = PrimitiveUnsignedIntegerTypeClass("UInt8", 1)
UInt16Type = PrimitiveUnsignedIntegerTypeClass("UInt16", 2)
UInt32Type = PrimitiveUnsignedIntegerTypeClass("UInt32", 4)
UInt64Type = PrimitiveUnsignedIntegerTypeClass("UInt64", 8)

PrimitiveIntegerTypes = [Int8Type, Int16Type, Int32Type, Int64Type, UInt8Type, UInt16Type, UInt32Type, UInt64Type]

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
    
    def quotientWith(self, other):
        return IntegerValue(int(self.value / other.value))

    def remainderWith(self, other):
        quotient = int(self.value / other.value)
        return IntegerValue(self.value - quotient*other.value)

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
        self.value = value

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

    def __init__(self, elementTypes: list[TypedValue], name = None) -> None:
        self.elementTypes = elementTypes
        self.name = name

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

class OverloadsTypeValue(TypedValue):
    def __init__(self, type: TypedValue, alternatives: tuple) -> None:
        super().__init__()
        self.alternatives = alternatives
        self.type = type

    def getType(self):
        return self.type

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not self.type.isEquivalentTo(other.getType()): return False
        if len(self.alternatives) != len(other.alternatives): return False
        for i in range(len(self.alternatives)):
            if not self.alternatives[i].isEquivalentTo(other.alternatives[i]):
                return False

        return True

    def toJson(self):
        return {'overloads': list(map(lambda v: v.toJson(), self.alternatives))}

class OverloadsType(BaseType):
    def __init__(self, elementTypes: list[TypedValue]) -> None:
        self.elementTypes = elementTypes

    def makeWithAlternatives(self, elements) -> OverloadsTypeValue:
        return OverloadsTypeValue(self, elements)

    def getType(self):
        return TypeType
    
    def isOverloadsType(self):
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, ProductType): return False

        if len(self.elementTypes) != len(other.elementTypes): return False
        for i in range(len(self.elementTypes)):
            if not self.elementTypes[i].isEquivalentTo(other.elementTypes[i]):
                return False

        return True

    def toJson(self):
        return {'overloadsType': list(map(lambda v: v.toJson(), self.elementTypes))}
    
    @classmethod
    def makeWithAlternativeTypes(cls, elementTypes: list[TypedValue]):
        return cls(tuple(elementTypes))

class RecordTypeValue(ProductTypeValue):
    def toJson(self):
        result = dict()
        for i in range(len(self.elements)):
            result[self.type.fields[i]] = self.elements[i]

        return result
    
class RecordType(ProductType):
    def __init__(self, elementTypes: list[TypedValue], fields: list[TypedValue], name = None) -> None:
        self.elementTypes = elementTypes
        self.fields = fields
        self.name = name

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

    def __init__(self, variantTypes: list[TypedValue], name = None) -> None:
        self.variantTypes = variantTypes
        self.name = name

    def makeWithTypeIndexAndValue(self, variantIndex: int, value: TypedValue) -> SumTypeValue:
        return SumTypeValue(self, variantIndex, value)

    def getType(self):
        return TypeType

    def toJson(self):
        return {'sumType': list(map(lambda v: v.toJson(), self.variantTypes))}

    @classmethod
    def makeNamedWithVariantTypes(cls, name, variantTypes: list[TypedValue]):
        return cls(name, tuple(variantTypes))

    @classmethod
    def makeWithVariantTypes(cls, variantTypes: list[TypedValue]):
        key = tuple(variantTypes)
        if key in cls.SumTypeCache:
            return cls.SumTypeCache[key]

        sumType = cls(key)
        cls.SumTypeCache[key] = sumType
        return sumType

class DerivedType(BaseType):
    def __init__(self, baseType) -> None:
        self.baseType = baseType

    def getType(self):
        return self.baseType.getType()

class DecoratedType(DerivedType):
    Const = 1<<0
    Volatile = 1<<1
    
    def __init__(self, baseType, decorations: int) -> None:
        super().__init__(baseType)
        self.decorations = decorations

    @classmethod
    def makeWithDecorations(cls, baseType: TypedValue, decorations: int):
        if baseType.isDecoratedType():
            return cls(baseType.baseType, baseType.decorations | decorations)
        return cls(baseType, decorations)

    @classmethod
    def makeConst(cls, baseType: TypedValue):
        return cls.makeWithDecorations(baseType, cls.Const)

    @classmethod
    def makeVolatile(cls, baseType: TypedValue):
        return cls.makeWithDecorations(baseType, cls.Volatile)

    def isDecoratedType(self) -> bool:
        return True

    def toJson(self):
        return {'decoratedType': self.baseType.toJson(), 'decorations': self.decorations}

class ArrayType(DerivedType):
    def __init__(self, baseType: TypedValue, size: int) -> None:
        super().__init__(baseType)
        self.size = size

    @classmethod
    def makeWithElementTypeAndSize(cls, elementType: TypedValue, size: IntegerValue):
        return cls(elementType, size.value)

    def isArrayType(self) -> bool:
        return True

    def toJson(self):
        return {'arrayType': self.baseType.toJson(), 'size': self.size}

class PointerType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isPointerType(self) -> bool:
        return True

    def toJson(self):
        return {'pointerType': self.baseType.toJson()}

class ReferenceType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isReferenceType(self) -> bool:
        return True

    def toJson(self):
        return {'refType': self.baseType.toJson()}

class TemporaryReferenceType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isTemporaryReferenceType(self) -> bool:
        return True
    
    def toJson(self):
        return {'tempRefType': self.baseType.toJson()}

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

class MacroContext(TypedValue):
    def __init__(self, sourcePosition: SourcePosition, lexicalEnvironment) -> None:
        self.sourcePosition = sourcePosition
        self.lexicalEnvironment = lexicalEnvironment

    def getType(self):
        return MacroContextType

    def toJson(self) -> dict:
        return {'kind': 'MacroContext'}

class ASTNode(TypedValue):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

    def getType(self):
        return ASTNodeType
    
    def prettyPrint(self) -> str:
        return json.dumps(self.toJson())

    def isASTNode(self):
        return True

    def isEquivalentTo(self, other) -> bool:
        return self == other

    def isTypeNode(self) -> bool:
        return False
    
    def isOverloadsTypeNode(self) -> bool:
        return False

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
    
    def isTypedOverloadsNode(self) -> bool:
        return False

class ASTTypeNode(ASTNode):
    def isTypeNode(self) -> bool:
        return True
    
    def getTypeUniverse(self) -> TypedValue:
        return TypeUniverse.getWithIndex(self.computeTypeUniverseIndex())

    @abstractmethod
    def computeTypeUniverseIndex(self) -> int:
        pass

    def getTypeExpressionAt(self, sourcePosition: SourcePosition):
        return ASTLiteralTypeNode(sourcePosition, self.getTypeUniverse())

class ASTLiteralTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def prettyPrint(self) -> str:
        return str(self.value)

    def getTypeUniverse(self) -> TypedValue:
        return self.value.getType()

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
    
    def getTypeExpressionAt(self, sourcePosition: SourcePosition) -> ASTTypeNode:
        return self.type

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

    def isSymbolBinding(self):
        return True
    
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

class SymbolCaptureBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, capturedBinding: SymbolBinding) -> None:
        super().__init__(sourcePosition, name)
        self.capturedBinding = capturedBinding

    def getTypeExpression(self) -> TypedValue:
        return self.capturedBinding.getTypeExpression()
    
    def getCaptureNestingLevel(self) -> int:
        return self.capturedBinding.getCaptureNestingLevel() + 1

    def getCanonicalBinding(self):
        return self.capturedBinding.getCanonicalBinding()
    
    def toJson(self):
        return {'name': repr(self.name)}

class SymbolValueBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, value: TypedValue) -> None:
        super().__init__(sourcePosition, name)
        self.value = value
        self.typeExpression = ASTLiteralTypeNode(sourcePosition, self.value.getType())

    def evaluateInActivationEnvironmentAt(self, activationEnvironment, sourcePosition: SourcePosition) -> TypedValue:
        return self.value

    def evaluateSubstitutionInContextAt(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode | ASTTypeNode:
        if self.value.isType():
            return ASTLiteralTypeNode(sourcePosition, self.value)
        return ASTTypedLiteralNode(sourcePosition, self.getTypeExpression(), self.value)

    def getTypeExpression(self) -> TypedValue:
        return self.typeExpression

    def isValueBinding(self) -> bool:
        return True
    
    def getCaptureNestingLevel(self) -> int:
        return 0

class SymbolLocalBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTTypeNode, valueExpression: ASTTypedNode | ASTTypeNode) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression
        self.valueExpression = valueExpression

    def getTypeExpression(self) -> ASTTypeNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 0
    
    def toJson(self):
        return {'name': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

class SymbolArgumentBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTLiteralTypeNode | ASTTypedNode) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression

    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 1
    
    def hasTypeOf(self, expectedType: TypedValue):
        return self.typeExpression.isLiteralTypeNode() and self.typeExpression.value.isEquivalentTo(expectedType)

    def toJson(self):
        return {'name': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

