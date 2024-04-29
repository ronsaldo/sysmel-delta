from abc import ABC, abstractmethod
import json
from typing import Any
import math
import struct
import os.path

class TypedValueVisitor(ABC):
    @abstractmethod
    def visitGenericTypedValue(self, value):
        pass

    @abstractmethod
    def visitVoidTypeValue(self, value):
        pass

    @abstractmethod
    def visitIntegerValue(self, value):
        pass

    @abstractmethod
    def visitPrimitiveIntegerValue(self, value):
        pass

    @abstractmethod
    def visitPrimitiveCharacterValue(self, value):
        pass

    @abstractmethod
    def visitPrimitiveFloatValue(self, value):
        pass

    @abstractmethod
    def visitStringDataValue(self, value):
        pass

    @abstractmethod
    def visitSymbol(self, value):
        pass

    @abstractmethod
    def visitLambdaValue(self, value):
        pass

    @abstractmethod
    def visitPiValue(self, value):
        pass

    @abstractmethod
    def visitSigmaValue(self, value):
        pass

    @abstractmethod
    def visitPrimitiveFunction(self, value):
        pass

    @abstractmethod
    def visitCurriedFunctionalValue(self, value):
        pass

    @abstractmethod
    def visitCurryingFunctionalValue(self, value):
        pass

    @abstractmethod
    def visitProductType(self, value):
        pass

    @abstractmethod
    def visitFunctionType(self, value):
        pass

    @abstractmethod
    def visitRecordType(self, value):
        pass

    @abstractmethod
    def visitSumType(self, value):
        pass

    @abstractmethod
    def visitDecoratedType(self, value):
        pass

    @abstractmethod
    def visitArrayType(self, value):
        pass

    @abstractmethod
    def visitPointerType(self, value):
        pass

    @abstractmethod
    def visitReferenceType(self, value):
        pass

    @abstractmethod
    def visitTemporaryReferenceType(self, value):
        pass
    
class TypedValue(ABC):
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitGenericTypedValue(self)
        
    @abstractmethod
    def getType(self):
        pass

    @abstractmethod
    def toJson(self):
        pass

    def prettyPrint(self) -> str:
        return json.dumps(self.toJson())
    
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
    
    def isFunctionType(self) -> bool:
        return False

    def isLambda(self) -> bool:
        return False

    def isSigma(self) -> bool:
        return False

    def isCVarArgType(self) -> bool:
        return False

    def isAnyType(self) -> bool:
        return False

    def isProductType(self) -> bool:
        return False
    
    def isProductTypeValue(self) -> bool:
        return False

    def isRecordType(self) -> bool:
        return False

    def isSumType(self) -> bool:
        return False

    def isEquivalentTo(self, other) -> bool:
        return self == other

    def isFunctionalValue(self) -> bool:
        return False

    def isReducibleFunctionalValue(self) -> bool:
        return False

    def isMacroValue(self) -> bool:
        return False

    def isPurelyFunctional(self) -> bool:
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

    def getRankOfProductTypeOrNone(self):
        return None    

    def findIndexOfFieldOrNoneAt(self, fieldName, sourcePosition):
        return None, None

    def findTypeOfFieldAtIndexOrNoneAt(self, index: int, sourcePosition):
        return None

    def getBaseTypeExpressionAt(self, sourcePosition):
        assert False

    def getElementTypeExpressionAt(self, sourcePosition):
        assert False

    def isArrayTypeNodeOrLiteral(self) -> bool:
        return False
    
    def isPointerTypeNodeOrLiteral(self) -> bool:
        return False

    def isReferenceLikeTypeNodeOrLiteral(self) -> bool:
        return False

    def isProductTypeNodeOrLiteral(self) -> bool:
        return False

    def isRecordTypeNodeOrLiteral(self) -> bool:
        return False

    def isSumTypeNodeOrLiteral(self) -> bool:
        return False

    def isSumTypeNode(self) -> bool:
        return False

    def isCVarArgTypeNode(self) -> bool:
        return False
    
    def isCVarArgCompatibleType(self) -> bool:
        return False
    
    def asTypedFunctionTypeNodeAtFor(self, sourcePosition, typechecker):
        return typechecker.makeSemanticError(sourcePosition, "Failed to convert value into function type node %s." % self.prettyPrint())
    
    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return None

    def interpretAsBoolean(self) -> bool:
        raise Exception("Not a boolean value.")
    
    def applyCoercionExpresionIntoCVarArgType(self, node):
        return node

class TypeUniverse(TypedValue):
    InstancedUniverses = dict()
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def toJson(self):
        if self.index == 0: return "Type"
        return "Type@%d" % self.index

    def prettyPrint(self) -> str:
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

    def prettyPrint(self) -> str:
        if self.name is None:
            return str(self.__class__)
        return self.name
    
    def getType(self) -> TypedValue:
        return TypeType

    def toJson(self):
        return self.name
        
    def isSubtypeOf(self, otherType: TypedValue) -> bool:
        if otherType.isTypeUniverse():
            return True
        return self == otherType

class AbortTypeClass(BaseType):
    pass

class VoidTypeValue(TypedValue):
    def __init__(self, type: BaseType, name: str) -> None:
        super().__init__()
        self.type = type
        self.name = name

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitVoidTypeValue(self)

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return self.type.isEquivalentTo(other.getType())
    
    def getType(self) -> TypedValue:
        return self.type

    def toJson(self):
        if self.name is None:
            return str(self.type) + ".value"
        return self.name
    
class VoidTypeClass(BaseType):
    def __init__(self, name: str, valueName: str) -> None:
        super().__init__(name)
        self.singleton = VoidTypeValue(self, valueName)

    def getSingleton(self) -> VoidTypeValue:
        return self.singleton

class CVarArgTypeClass(BaseType):
    def isCVarArgType(self) -> bool:
        return True

class AnyTypeClass(BaseType):
    def isAnyType(self) -> bool:
        return True

class IntegerTypeClass(BaseType):
    pass

class PrimitiveTypeClass(BaseType):
    def __init__(self, name: str, valueSize: int, literalSuffix = '') -> None:
        super().__init__(name)
        self.valueSize = valueSize
        self.literalSuffix = literalSuffix

class PrimitiveIntegerTypeClass(PrimitiveTypeClass):
    @abstractmethod
    def normalizeIntegerValue(self, value: int) -> int:
        pass

    def isCVarArgCompatibleType(self) -> bool:
        return True

class PrimitiveSizeIntegerTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, isSigned, literalSuffix) -> None:
        super().__init__(name, 0, literalSuffix)
        self.isSigned = isSigned

    def normalizeIntegerValue(self, value: int) -> int:
        return value
    
class PrimitiveUnsignedIntegerTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, valueSize: int, literalSuffix) -> None:
        super().__init__(name, valueSize, literalSuffix)
        self.mask = (1<<(valueSize*8)) - 1

    def normalizeIntegerValue(self, value: int) -> int:
        return value & self.mask

class PrimitiveCharacterTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, valueSize: int, literalSuffix) -> None:
        super().__init__(name, valueSize, literalSuffix)
        self.mask = (1<<(valueSize*8)) - 1

    def normalizeIntegerValue(self, value: int) -> int:
        return value & self.mask
    
class PrimitiveSignedIntegerTypeClass(PrimitiveIntegerTypeClass):
    def __init__(self, name: str, valueSize: int, literalSuffix) -> None:
        super().__init__(name, valueSize, literalSuffix)
        self.mask = (1<<(valueSize*8)) - 1
        self.signBitMask = 1<<(valueSize*8 - 1)

    def normalizeIntegerValue(self, value: int) -> int:
        return (value & (self.signBitMask - 1)) - (value & self.signBitMask)

class PrimitiveFloatTypeClass(PrimitiveTypeClass):
    def normalizeFloatValue(self, value: float) -> float:
        return value

class PrimitiveFloat32TypeClass(PrimitiveFloatTypeClass):
    def normalizeFloatValue(self, value: float) -> float:
        return struct.unpack('f', struct.pack('f', value))[0]

    def applyCoercionExpresionIntoCVarArgType(self, node):
        from .ast import ASTMessageSendNode, ASTLiteralNode
        return ASTMessageSendNode(node.sourcePosition, node, ASTLiteralNode(node.sourcePosition, Symbol.intern('asFloat64')), [node])
    
class PrimitiveFloat64TypeClass(PrimitiveFloatTypeClass):
    def isCVarArgCompatibleType(self) -> bool:
        return True

class PrimitiveVectorTypeClass(PrimitiveTypeClass):
    def __init__(self, name: str, elementType: TypedValue, elements: int, literalSuffix='') -> None:
        super().__init__(name, elementType.valueSize * elements, literalSuffix)
        self.elementType = elementType
        self.elements = elements

class StringTypeClass(BaseType):
    pass

class ASTNodeTypeClass(BaseType):
    pass

class MacroContextTypeClass(BaseType):
    pass

class ModuleTypeClass(BaseType):
    pass

AbortType = AbortTypeClass("Abort")
VoidType = VoidTypeClass("Void", "void")
AnyType = AnyTypeClass("Any")

CVarArgType = CVarArgTypeClass("CVarArg")

IntegerType = IntegerTypeClass("Integer")
Float32Type = PrimitiveFloat32TypeClass("Float32", 4, 'f32')
Float64Type = PrimitiveFloat64TypeClass("Float64", 8, 'f64')

Char8Type  = PrimitiveCharacterTypeClass("Char8", 1, 'c8')
Char16Type = PrimitiveCharacterTypeClass("Char16", 2, 'c16')
Char32Type = PrimitiveCharacterTypeClass("Char32", 4, 'c32')

ASTNodeType = ASTNodeTypeClass("ASTNode")
MacroContextType = MacroContextTypeClass("MacroContext")
ModuleType = ModuleTypeClass("Module")

Int8Type  = PrimitiveSignedIntegerTypeClass("Int8", 1, 'i8')
Int16Type = PrimitiveSignedIntegerTypeClass("Int16", 2, 'i16')
Int32Type = PrimitiveSignedIntegerTypeClass("Int32", 4, 'i32')
Int64Type = PrimitiveSignedIntegerTypeClass("Int64", 8, 'i64')

UInt8Type  = PrimitiveUnsignedIntegerTypeClass("UInt8", 1, 'u8')
UInt16Type = PrimitiveUnsignedIntegerTypeClass("UInt16", 2, 'u16')
UInt32Type = PrimitiveUnsignedIntegerTypeClass("UInt32", 4, 'u32')
UInt64Type = PrimitiveUnsignedIntegerTypeClass("UInt64", 8, 'u64')

SizeType = PrimitiveSizeIntegerTypeClass("Size", False, 'sz')
SignedSizeType = PrimitiveSizeIntegerTypeClass("SignedSize", True, 'ssz')
UIntPointerType = PrimitiveSizeIntegerTypeClass("UIntPointer", False, 'uptr')
IntPointerType = PrimitiveSizeIntegerTypeClass("IntPointer", True, 'iptr')

PrimitiveIntegerTypes = [
    Int8Type, Int16Type, Int32Type, Int64Type,
    UInt8Type, UInt16Type, UInt32Type, UInt64Type,
    SizeType, SignedSizeType, UIntPointerType, IntPointerType,
    Char8Type, Char16Type, Char32Type
]
PrimitiveFloatTypes = [Float32Type, Float64Type]
NumberTypes = [IntegerType] + PrimitiveIntegerTypes + PrimitiveFloatTypes

Float32x2Type = PrimitiveVectorTypeClass('Float32x2', Float32Type, 2, 'f32x2')
Float32x3Type = PrimitiveVectorTypeClass('Float32x3', Float32Type, 3, 'f32x3')
Float32x4Type = PrimitiveVectorTypeClass('Float32x4', Float32Type, 4, 'f32x4')

Float64x2Type = PrimitiveVectorTypeClass('Float64x2', Float64Type, 2, 'f64x2')
Float64x3Type = PrimitiveVectorTypeClass('Float64x3', Float64Type, 3, 'f64x3')
Float64x4Type = PrimitiveVectorTypeClass('Float64x4', Float64Type, 4, 'f64x4')

Int32x2Type = PrimitiveVectorTypeClass('Int32x2', Int32Type, 2, 'i32x2')
Int32x3Type = PrimitiveVectorTypeClass('Int32x3', Int32Type, 3, 'i32x3')
Int32x4Type = PrimitiveVectorTypeClass('Int32x4', Int32Type, 4, 'i32x4')

UInt32x2Type = PrimitiveVectorTypeClass('UInt32x2', UInt32Type, 2, 'u32x2')
UInt32x3Type = PrimitiveVectorTypeClass('UInt32x3', UInt32Type, 3, 'u32x3')
UInt32x4Type = PrimitiveVectorTypeClass('UInt32x4', UInt32Type, 4, 'u32x4')

PrimitiveFloatVectorTypes = [
    Float32x2Type, Float32x3Type, Float32x4Type,
    Float64x2Type, Float64x3Type, Float64x4Type,
]

PrimitiveIntegerVectorTypes = [
    Int32x2Type, Int32x3Type, Int32x4Type,
    UInt32x2Type, UInt32x3Type, UInt32x4Type,
]

PrimitiveVectorTypes = PrimitiveFloatVectorTypes + PrimitiveIntegerVectorTypes

class IntegerValue(TypedValue):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitIntegerValue(self)

    def prettyPrint(self) -> str:
        return str(self.value)

    def getType(self) -> TypedValue:
        return IntegerType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

    def __neg__(self):
        return self.__class__(-self.value)

    def __invert__(self):
        return self.__class__(-1 - self.value)

    def __add__(self, other):
        return self.__class__(self.value + other.value)

    def __sub__(self, other):
        return self.__class__(self.value - other.value)

    def __mul__(self, other):
        return self.__class__(self.value * other.value)

    def __and__(self, other):
        return self.__class__(self.value & other.value)

    def __or__(self, other):
        return self.__class__(self.value | other.value)

    def __xor__(self, other):
        return self.__class__(self.value ^ other.value)

    def __lshift__(self, other):
        return self.__class__(self.value << other.value)

    def __rshift__(self, other):
        return self.__class__(self.value >> other.value)
    
    def equals(self, other):
        return booleanValueFor(self.value == other.value)

    def notEquals(self, other):
        return booleanValueFor(self.value != other.value)

    def lessThan(self, other):
        return booleanValueFor(self.value < other.value)

    def lessOrEquals(self, other):
        return booleanValueFor(self.value <= other.value)

    def greaterThan(self, other):
        return booleanValueFor(self.value > other.value)

    def greaterOrEquals(self, other):
        return booleanValueFor(self.value >= other.value)
    
    def quotientWith(self, other):
        return self.__class__(int(self.value / other.value))

    def remainderWith(self, other):
        quotient = int(self.value / other.value)
        return self.__class__(self.value - quotient*other.value)

    def minWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def maxWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def castToInteger(self):
        return self

    def castToPrimitiveIntegerType(self, targetType):
        return PrimitiveIntegerValue(targetType, self.value)

    def castToPrimitiveCharacterType(self, targetType):
        return PrimitiveCharacterValue(targetType, self.value)
    
    def castToPrimitiveFloatType(self, targetType):
        return PrimitiveFloatValue(targetType, float(self.value))
    
class PrimitiveIntegerValue(TypedValue):
    def __init__(self, type: TypedValue, value: int) -> None:
        self.type = type
        self.value = type.normalizeIntegerValue(value)

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPrimitiveIntegerValue(self)

    def prettyPrint(self) -> str:
        return str(self.value) + self.type.literalSuffix

    def getType(self):
        return self.type

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.type == other.type and self.value == other.value

    def __neg__(self):
        return self.__class__(self.type, -self.value)

    def __invert__(self):
        return self.__class__(self.type, -1 - self.value)

    def __add__(self, other):
        return self.__class__(self.type, self.value + other.value)

    def __sub__(self, other):
        return self.__class__(self.type, self.value - other.value)

    def __mul__(self, other):
        return self.__class__(self.type, self.value * other.value)
    
    def quotientWith(self, other):
        return self.__class__(self.type, int(self.value / other.value))

    def remainderWith(self, other):
        quotient = int(self.value / other.value)
        return self.__class__(self.type, self.value - quotient*other.value)

    def __and__(self, other):
        return self.__class__(self.type, self.value & other.value)

    def __or__(self, other):
        return self.__class__(self.type, self.value | other.value)

    def __xor__(self, other):
        return self.__class__(self.type, self.value ^ other.value)

    def __lshift__(self, other):
        return self.__class__(self.type, self.value << other.value)

    def __rshift__(self, other):
        return self.__class__(self.type, self.value >> other.value)

    def equals(self, other):
        return booleanValueFor(self.value == other.value)

    def notEquals(self, other):
        return booleanValueFor(self.value != other.value)

    def lessThan(self, other):
        return booleanValueFor(self.value < other.value)

    def lessOrEquals(self, other):
        return booleanValueFor(self.value <= other.value)

    def greaterThan(self, other):
        return booleanValueFor(self.value > other.value)

    def greaterOrEquals(self, other):
        return booleanValueFor(self.value >= other.value)
    
    def minWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def maxWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def castToInteger(self):
        return IntegerValue(self.value)

    def castToPrimitiveIntegerType(self, targetType):
        return PrimitiveIntegerValue(targetType, self.value)

    def castToPrimitiveCharacterType(self, targetType):
        return PrimitiveCharacterValue(targetType, self.value)

    def castToPrimitiveFloatType(self, targetType):
        return PrimitiveFloatValue(targetType, float(self.value))
    
    def toJson(self):
        return self.value
    
class PrimitiveCharacterValue(PrimitiveIntegerValue):
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPrimitiveCharacterValue(self)

    def toJson(self):
        return chr(self.value)

class PrimitiveFloatValue(TypedValue):
    def __init__(self, type: TypedValue, value: float) -> None:
        super().__init__()
        self.type = type
        self.value = type.normalizeFloatValue(value)

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPrimitiveFloatValue(self)

    def prettyPrint(self) -> str:
        return str(self.value) + self.type.literalSuffix

    def getType(self):
        return self.type

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

    def __neg__(self):
        return self.__class__(-self.value)
    
    def __add__(self, other):
        return self.__class__(self.type, self.value + other.value)

    def __sub__(self, other):
        return self.__class__(self.type, self.value - other.value)

    def __mul__(self, other):
        return self.__class__(self.type, self.value * other.value)

    def __div__(self, other):
        return self.__class__(self.type, self.value / other.value)

    def sqrt(self):
        return self.__class__(self.type, math.sqrt(self.value))

    def minWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def maxWith(self, other):
        if self.value <= other.value:
            return self
        else:
            return other

    def equals(self, other):
        return booleanValueFor(self.value == other.value)

    def notEquals(self, other):
        return booleanValueFor(self.value != other.value)

    def lessThan(self, other):
        return booleanValueFor(self.value < other.value)

    def lessOrEquals(self, other):
        return booleanValueFor(self.value <= other.value)

    def greaterThan(self, other):
        return booleanValueFor(self.value > other.value)

    def greaterOrEquals(self, other):
        return booleanValueFor(self.value >= other.value)
    
    def castToInteger(self):
        return IntegerValue(int(self.value))

    def castToPrimitiveIntegerType(self, targetType):
        return PrimitiveIntegerValue(targetType, int(self.value))

    def castToPrimitiveCharacterType(self, targetType):
        return PrimitiveCharacterValue(targetType, int(self.value))

    def castToPrimitiveFloatType(self, targetType):
        return PrimitiveFloatValue(targetType, self.value)

class StringDataValue(TypedValue):
    def __init__(self, value: bytes) -> None:
        super().__init__()
        self.value = value

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitStringDataValue(self)

    def getType(self):
        return Char8PointerType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return repr(self.value)

class FunctionType(BaseType):
    FunctionTypeCache = dict()

    def __init__(self, argumentType: TypedValue, isVariadic: bool, resultType: TypedValue, callingConventionName: TypedValue = None) -> None:
        super().__init__(None)
        self.type = None
        self.argumentType = argumentType
        self.isVariadic = isVariadic
        self.resultType = resultType
        self.callingConventionName = callingConventionName

    def withCallingConventionNamed(self, conventionName: TypedValue):
        return self.__class__.makeFromTo(self.argumentType, self.resultType, conventionName)

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitFunctionType(self)
    
    def getType(self) -> TypedValue:
        if self.type is None:
            self.type = TypeType.getWithIndex(max(self.argumentType.getType().getTypeUniverseIndex(), self.resultType.getType().getTypeUniverseIndex()))
        return self.type
    
    def isFunctionType(self) -> bool:
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, FunctionType): return False

        return self.argumentType.isEquivalentTo(other.argumentType) and self.resultType.isEquivalentTo(other.resultType)

    def toJson(self):
        return {'Function': self.argumentType.toJson(), 'resultType': self.resultType.toJson(), 'callingConvention': optionalToJson(self.callingConventionName)}

    @classmethod
    def makeFromTo(cls, argumentType: TypedValue, resultType: TypedValue, callingConventionName: TypedValue = None):
        functionKey = (argumentType, resultType, callingConventionName)
        if functionKey in cls.FunctionTypeCache:
            return cls.FunctionTypeCache[functionKey]

        functionType = cls(argumentType, False, resultType, callingConventionName)
        cls.FunctionTypeCache[functionKey] = functionType
        return functionType

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
        if not isinstance(other, OverloadsType): return False

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

class ProductTypeValue(TypedValue):
    def __init__(self, type: TypedValue, elements: tuple) -> None:
        super().__init__()
        self.elements = elements
        self.type = type

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitProductTypeValue(self)

    def getType(self):
        return self.type

    def isProductTypeValue(self) -> bool:
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not self.type.isEquivalentTo(other.getType()): return False
        if len(self.elements) != len(other.elements): return False
        for i in range(len(self.elements)):
            if not self.elements[i].isEquivalentTo(other.elements[i]):
                return False

        return True
    
    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return list(map(lambda v: ASTTypedLiteralNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, v.getType()), v), self.elements))

    def __getitem__(self, index):
        return self.elements[index]

    def toJson(self):
        return {'product': list(map(lambda v: v.toJson(), self.elements))}
    
    def prettyPrint(self) -> str:
        result = '('
        isFirst = True
        for element in self.elements:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += element.prettyPrint()
        result += ')'
        return result

class ProductType(BaseType):
    ProductTypeCache = dict()

    def __init__(self, elementTypes: list[TypedValue], name = None) -> None:
        self.elementTypes = elementTypes
        self.name = name

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitProductType(self)

    def makeWithElements(self, elements) -> ProductTypeValue:
        return ProductTypeValue(self, elements)

    def getType(self):
        return TypeType
    
    def isProductType(self):
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, ProductType): return False

        if len(self.elementTypes) != len(other.elementTypes): return False
        for i in range(len(self.elementTypes)):
            if not self.elementTypes[i].isEquivalentTo(other.elementTypes[i]):
                return False

        return True

    def toJson(self):
        return {'productType': list(map(lambda v: v.toJson(), self.elementTypes))}
    
    def findTypeOfFieldAtIndexOrNoneAt(self, index: int, sourcePosition):
        if index < len(self.elementTypes):
            return ASTLiteralTypeNode(sourcePosition, self.elementTypes[index])
        else:
            return None
    
    def getRankOfProductTypeOrNone(self):
        return len(self.elementTypes)

    @classmethod
    def makeWithElementTypes(cls, elementTypes: list[TypedValue]):
        productKey = tuple(elementTypes)
        if productKey in cls.ProductTypeCache:
            return cls.ProductTypeCache[productKey]

        productType = cls(productKey)
        cls.ProductTypeCache[productKey] = productType
        return productType
    
class RecordTypeValue(ProductTypeValue):
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitRecordTypeValue(self)

    def toJson(self):
        result = dict()
        for i in range(len(self.elements)):
            result[self.type.fields[i].value] = self.elements[i].toJson()

        return result

    def prettyPrint(self) -> str:
        result = self.type.prettyPrint()
        result += '#{'
        isFirst = True
        for i in range(len(self.elements)):
            element = self.elements[i]
            if isFirst:
                isFirst = False
            else:
                result += '. '
            result += self.type.fields[i].prettyPrint()
            result += ' : '
            result += element.prettyPrint()
        result += '}'
        return result
class RecordType(ProductType):
    def __init__(self, elementTypes: list[TypedValue], fields: list[TypedValue], name = None) -> None:
        assert len(elementTypes) == len(fields)
        self.elementTypes = elementTypes
        self.fields = fields
        self.name = name
        self.fieldNameDictionary = {}
        for i in range(len(fields)):
            self.fieldNameDictionary[fields[i]] = i

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitRecordType(self)

    def makeWithElements(self, elements) -> RecordTypeValue:
        return RecordTypeValue(self, elements)
    
    def findIndexOfFieldOrNoneAt(self, fieldName: TypedValue, sourcePosition) -> int:
        found = self.fieldNameDictionary.get(fieldName, None)
        if found is None:
            return None, None

        return found, ASTLiteralTypeNode(sourcePosition, self.elementTypes[found])
    
    def isRecordType(self) -> bool:
        return True

    @classmethod
    def makeWithElementTypes(cls, elementTypes: list[TypedValue]):
        assert False

    def toJson(self):
        return {'recordType': list(map(lambda v: v.toJson(), self.elementTypes)), 'fields' : list(map(lambda v: v.toJson(), self.fields))}
    
    def prettyPrint(self) -> str:
        if self.name is not None:
            return self.name
        result = '(RecordWithFields: #{'
        for i in range(len(self.fields)):
            if i > 0:
                result += '. '
            result += self.elementTypes[i].prettyPrint()
            result += ' : '
            result += self.fields[i].prettyPrint()
        result += '})'
        return result

class SumTypeValue(TypedValue):
    def __init__(self, type: TypedValue, variantIndex: int, value: TypedValue) -> None:
        super().__init__()
        self.type = type
        self.variantIndex = variantIndex
        self.value = value

    def getType(self):
        return self.type

    def toJson(self):
        return {'sum': self.variantIndex, 'value': self.value.toJson()}
    
    def interpretAsBoolean(self) -> bool:
        return self.variantIndex != 0
    
    def isSumTypeValue(self) -> bool:
        return True
    
    def prettyPrint(self) -> str:
        return self.value.prettyPrint()

class SumType(BaseType):
    SumTypeCache = dict()

    def __init__(self, variantTypes: list[TypedValue], name = None) -> None:
        self.variantTypes = variantTypes
        self.name = name

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitSumType(self)
    
    def isSumType(self) -> bool:
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, SumType): return False

        if len(self.variantTypes) != len(other.variantTypes): return False
        for i in range(len(self.variantTypes)):
            if not self.variantTypes[i].isEquivalentTo(other.variantTypes[i]):
                return False

        return True
    
    def makeWithTypeIndexAndValue(self, variantIndex: int, value: TypedValue) -> SumTypeValue:
        return SumTypeValue(self, variantIndex, value)

    def getType(self):
        return TypeType

    def toJson(self):
        return {'sumType': list(map(lambda v: v.toJson(), self.variantTypes))}

    @classmethod
    def makeNamedWithVariantTypes(cls, name, variantTypes: list[TypedValue]):
        return cls(tuple(variantTypes), name)

    @classmethod
    def makeWithVariantTypes(cls, variantTypes: list[TypedValue]):
        key = tuple(variantTypes)
        if key in cls.SumTypeCache:
            return cls.SumTypeCache[key]

        sumType = cls(key)
        cls.SumTypeCache[key] = sumType
        return sumType
    
    def prettyPrint(self) -> str:
        if self.name is not None:
            return self.name
        
        result = '('
        for i in range(len(self.variantTypes)):
            if i > 0:
                result += '|'
            result += self.variantTypes[i].prettyPrint()
        result += ')'
        return result

class DictionaryTypeValue(TypedValue):
    def __init__(self, type: TypedValue, elements: list[TypedValue]) -> None:
        super().__init__()
        self.type = type
        self.elements = elements

    def getType(self):
        return self.type

    def toJson(self):
        return {'dictionary': list(map(lambda v: v.toJson(), self.elements))}
    
    def prettyPrint(self) -> str:
        result = '#{'
        isFirst = True
        for element in self.elements:
            if isFirst:
                isFirst = False
            else:
                result += '. '
            result += element.elements[0].prettyPrint()
            result += ' : '
            result += element.elements[1].prettyPrint()

        result += '}'
        return result
    
class DictionaryType(BaseType):
    DictionaryTypeCache = dict()

    def __init__(self, keyType: TypedValue, valueType: TypedValue, name = None) -> None:
        self.keyType = keyType
        self.valueType = valueType
        self.name = name

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitDictionaryType(self)

    def makeWithElements(self, elements) -> DictionaryTypeValue:
        return DictionaryTypeValue(self, elements)

    def getType(self):
        return TypeType
    
    def isDictionaryType(self):
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not isinstance(other, DictionaryType): return False

        return self.keyType.isEquivalentTo(other.keyType) and self.valueType.isEquivalentTo(other.valueType)

    def toJson(self):
        return {'dictionaryType': self.keyType.toJson(), 'valueType': self.valueType.toJson()}
    
    @classmethod
    def makeWithKeyAndValueType(cls, keyType: TypedValue, valueType: TypedValue):
        hashKey = (keyType, valueType)
        if hashKey in cls.DictionaryTypeCache:
            return cls.DictionaryTypeCache[hashKey]

        dictionaryType = cls(keyType, valueType)
        cls.DictionaryTypeCache[hashKey] = dictionaryType
        return dictionaryType
    
## Boolean :: False | True.
FalseType = VoidTypeClass("False", "false")
TrueType = VoidTypeClass("True", "true")
BooleanType = SumType.makeNamedWithVariantTypes("Boolean", [FalseType, TrueType])
FalseValue = BooleanType.makeWithTypeIndexAndValue(0, FalseType.getSingleton())
TrueValue = BooleanType.makeWithTypeIndexAndValue(1, TrueType.getSingleton())
assert not FalseValue.interpretAsBoolean()
assert TrueValue.interpretAsBoolean()

def booleanValueFor(b: bool):
    if b:
        return TrueValue
    else:
        return FalseValue

class DerivedType(BaseType):
    def __init__(self, baseType) -> None:
        super().__init__(None)
        self.baseType = baseType

    def isEquivalentTo(self, other) -> bool:
        if self == other: return True
        if not isinstance(other, self.__class__): return False
        return self.baseType.isEquivalentTo(other.baseType)
    
    def getBaseTypeExpressionAt(self, sourcePosition):
        return ASTLiteralTypeNode(sourcePosition, self.baseType)

    def getType(self):
        return self.baseType.getType()

    def isCVarArgCompatibleType(self) -> bool:
        return self.baseType.isCVarArgCompatibleType()

class DecoratedType(DerivedType):
    DecoratedTypeCache = dict()

    Mutable = 1<<0
    Volatile = 1<<1
    
    def __init__(self, baseType, decorations: int) -> None:
        super().__init__(baseType)
        self.decorations = decorations

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitDecoratedType(self)

    def findIndexOfFieldOrNoneAt(self, fieldName: TypedValue, sourcePosition) -> int:
        return self.baseType.findIndexOfFieldOrNoneAt(self, fieldName, sourcePosition)
    
    def findTypeOfFieldAtIndexOrNoneAt(self, index: int, sourcePosition):
        return self.baseType.findTypeOfFieldAtIndexOrNoneAt(index, sourcePosition)
        
    def getRankOfProductTypeOrNone(self):
        return self.baseType.getRankOfProductTypeOrNone()
    
    def prettyPrint(self) -> str:
        result = self.baseType.prettyPrint()
        if self.isMutable():
            result += ' mutable'

        if self.isVolatile():
            result += ' volatile'

        return result
    
    def isMutable(self) -> bool:
        return (self.decorations & DecoratedType.Mutable) != 0

    def isVolatile(self) -> bool:
        return (self.decorations & DecoratedType.Volatile) != 0

    def isEquivalentTo(self, other) -> bool:
        if self == other: return True
        if not isinstance(other, DecoratedType): return False
        return self.decorations == other.decorations and self.baseType.isEquivalentTo(other.baseType)
    
    @classmethod
    def privateMakeWithDecorations(cls, baseType: TypedValue, decorations: int):
        decoratedTypeKey = (baseType, decorations)
        if decoratedTypeKey in cls.DecoratedTypeCache:
            return cls.DecoratedTypeCache[decoratedTypeKey]
        
        decoratedType = cls(baseType, decorations)
        cls.DecoratedTypeCache[decoratedTypeKey] = decoratedType
        return decoratedType

    @classmethod
    def makeWithDecorations(cls, baseType: TypedValue, decorations: int):
        if baseType.isDecoratedType():
            return cls.privateMakeWithDecorations(baseType.baseType, baseType.decorations | decorations)
        return cls.privateMakeWithDecorations(baseType, decorations)

    @classmethod
    def makeMutable(cls, baseType: TypedValue):
        return cls.makeWithDecorations(baseType, cls.Mutable)

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

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitArrayType(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ('[%d]' % self.size)

    @classmethod
    def makeWithElementTypeAndSize(cls, elementType: TypedValue, size: IntegerValue):
        return cls(elementType, size.value)

    def isArrayType(self) -> bool:
        return True

    def getElementTypeExpressionAt(self, sourcePosition):
        return ASTLiteralTypeNode(sourcePosition, self.baseType)

    def toJson(self):
        return {'arrayType': self.baseType.toJson(), 'size': self.size}

class ValueBox(TypedValue):
    def __init__(self, valueType: TypedValue, initialValue = None):
        self.valueType = valueType
        self.value = initialValue

    def getType(self):
        return None

    def loadAtOffset(self, offset: int):
        assert offset == 0
        return self.value

    def storeAtOffset(self, offset: int, value):
        assert offset == 0
        self.value = value
    
    def toJson(self):
        return {'valueBox': optionalToJson(self.value)}

class PointerLikeValue(TypedValue):
    def __init__(self, type: TypedValue, storage, offset: int = 0) -> None:
        super().__init__()
        self.storage = storage
        self.offset = offset
        self.type = type

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPointerLikeValue(self)

    def getType(self):
        return self.type

    def loadValue(self):
        return self.storage.loadAtOffset(self.offset)

    def storeValue(self, value):
        return self.storage.storeAtOffset(self.offset, value)
    
    def reinterpretTo(self, targetType):
        return PointerLikeValue(targetType, self.storage, self.offset)

    def isPointerLikeValue(self) -> bool:
        return True

    def isEquivalentTo(self, other: TypedValue) -> bool:
        if not self.type.isEquivalentTo(other.getType()): return False
        return self.storage is other.storage and self.offset == other.offset
    
    def toJson(self):
        return {'pointerLikeValue': self.type.toJson(), 'storage' : optionalToJson(self.storage)}
    
class PointerType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' pointer'

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitPointerType(self)

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isPointerType(self) -> bool:
        return True
    
    def isCVarArgCompatibleType(self) -> bool:
        return True

    def getElementTypeExpressionAt(self, sourcePosition):
        return ASTLiteralTypeNode(sourcePosition, self.baseType)

    def toJson(self):
        return {'pointerType': self.baseType.toJson()}

class ReferenceType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitReferenceType(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' ref'

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isReferenceType(self) -> bool:
        return True

    def getElementTypeExpressionAt(self, sourcePosition):
        return self.baseType.getElementTypeExpressionAt(sourcePosition)
    
    def toJson(self):
        return {'refType': self.baseType.toJson()}

class TemporaryReferenceType(DerivedType):
    def __init__(self, baseType) -> None:
        super().__init__(baseType)

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitTemporaryReferenceType(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' tempRef'

    @classmethod
    def makeWithBaseType(cls, baseType):
        return cls(baseType)

    def isTemporaryReferenceType(self) -> bool:
        return True
    
    def getElementTypeExpressionAt(self, sourcePosition):
        return self.baseType.getElementTypeExpressionAt(sourcePosition)

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
    
    def prettyPrint(self) -> str:
        return '#' + repr(self.value)
    
    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitSymbol(self)

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

Char8PointerType = PointerType.makeWithBaseType(Char8Type)
StringType = RecordType([Char8PointerType, SizeType], [Symbol.intern('elements'), Symbol.intern('size')], 'String')

def makeStringValue(value: str):
    data = StringDataValue(value.encode('utf-8'))
    size = PrimitiveIntegerValue(SizeType, len(value))
    return StringType.makeWithElements((data, size))

class SourceCode:
    def __init__(self, directory: str, name: str, language: str, text: bytes) -> None:
        self.directory = directory
        self.name = name
        self.language = language
        self.text = text

    def __str__(self) -> str:
        return os.path.join(self.directory, self.name)

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
    def __init__(self, sourcePosition: SourcePosition, lexicalEnvironment, typechecker) -> None:
        self.sourcePosition = sourcePosition
        self.lexicalEnvironment = lexicalEnvironment
        self.typechecker = typechecker

    def getType(self):
        return MacroContextType

    def toJson(self) -> dict:
        return {'kind': 'MacroContext'}

class ASTNode(TypedValue):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

    def getType(self):
        return ASTNodeType
    
    def isASTNode(self):
        return True

    def isEquivalentTo(self, other) -> bool:
        return self == other
    
    def parseAndUnpackArgumentsPattern(self):
        from .ast import ASTErrorNode
        return [ASTErrorNode(self.sourcePosition, 'Not a valid argument spec.')], False, False

    def performSatisfiedByCheckInEnvironment(self, other, environment) -> bool:
        return self.performEquivalenceCheckInEnvironment(other, environment)
    
    def performEquivalenceCheckInEnvironment(self, other, environment) -> bool:
        if self == other: return True
        if other.isTypedIdentifierReferenceNode() and other.binding.isImplicitValueBinding():
            assert not self.isTypedIdentifierReferenceNode()
            assert False

        return self.isEquivalentTo(other), environment
    
    def isBindableNameNode(self) -> bool:
        return False
    
    def isMessageSendNode(self) -> bool:
        return False

    def isTypeNode(self) -> bool:
        return False
    
    def isOverloadsTypeNode(self) -> bool:
        return False

    def isDecoratedTypeNode(self) -> bool:
        return False

    def isPointerTypeNode(self) -> bool:
        return False

    def isReferenceTypeNode(self) -> bool:
        return False

    def isTemporaryReferenceTypeNode(self) -> bool:
        return False

    def isLiteralTypeNode(self) -> bool:
        return False

    def isTypedIdentifierReferenceNode(self) -> bool:
        return False

    def isTypedLiteralNode(self) -> bool:
        return False
    
    def isTypedErrorNode(self) -> bool:
        return False
    
    def isTypedTupleNode(self) -> bool:
        return False

    def isTypedTupleAtNode(self) -> bool:
        return False

    def isPiLiteralValue(self) -> bool:
        return False

    def isFunctionTypeLiteralValue(self) -> bool:
        return False

    def isTypedFunctionalNode(self) -> bool:
        return False

    def isTypedPiNode(self) -> bool:
        return False
    
    def isFunctionTypeNode(self) -> bool:
        return False
    
    def isFunctionalDependentTypeNode(self) -> bool:
        return False
    
    def isTypedFunctionTypeNode(self) -> bool:
        return False

    def isAnyFunctionTypeNode(self) -> bool:
        return self.isPiLiteralValue() or self.isFunctionTypeLiteralValue() or self.isTypedPiNode() or self.isTypedFunctionTypeNode()

    def isTypedLambdaNode(self) -> bool:
        return False
    
    def isTypedLiteralFunctionalValue(self) -> bool:
        return False

    def isTypedLiteralReducibleFunctionalValue(self) -> bool:
        return False

    def isTypedOverloadsNode(self) -> bool:
        return False
    
    def isTypedPointerLikeReinterpretToNode(self) -> bool:
        return False

    def isTupleNode(self) -> bool:
        return False
    
    def expandBindingOfValueWithAt(self, value, typechecker, sourcePosition):
        from .ast import ASTSequenceNode, ASTErrorNode
        return ASTSequenceNode(sourcePosition, [value, ASTErrorNode(self.sourcePosition, 'Not a valid pattern expression.')] )

class ASTTypeNode(ASTNode):
    def isTypeNode(self) -> bool:
        return True
    
    def getTypeUniverse(self) -> TypedValue:
        return TypeUniverse.getWithIndex(self.computeTypeUniverseIndex())
    
    def applyCoercionExpresionIntoCVarArgType(self, node):
        return node

    @abstractmethod
    def computeTypeUniverseIndex(self) -> int:
        pass

    def getTypeExpressionAt(self, sourcePosition: SourcePosition):
        return ASTLiteralTypeNode(sourcePosition, self.getTypeUniverse())
    
    def isCVarArgCompatibleTypeNode(self) -> bool:
        return False

class ASTLiteralTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def applyCoercionExpresionIntoCVarArgType(self, node):
        return self.value.applyCoercionExpresionIntoCVarArgType(node)

    def findIndexOfFieldOrNoneAt(self, fieldName: TypedValue, sourcePosition: SourcePosition) -> int:
        return self.value.findIndexOfFieldOrNoneAt(fieldName, sourcePosition)
    
    def findTypeOfFieldAtIndexOrNoneAt(self, index: int, sourcePosition):
        return self.value.findTypeOfFieldAtIndexOrNoneAt(index, sourcePosition)

    def getRankOfProductTypeOrNone(self):
        return self.value.getRankOfProductTypeOrNone()
    
    def withCallingConventionNamed(self, callingConventionName: TypedValue):
        return ASTLiteralTypeNode(SourceCode, self.value.withCallingConventionNamed(callingConventionName))

    def prettyPrint(self) -> str:
        return self.value.prettyPrint()

    def getBaseTypeExpressionAt(self, sourcePosition):
        return self.value.getBaseTypeExpressionAt(sourcePosition)

    def getTypeUniverse(self) -> TypedValue:
        return self.value.getType()

    def computeTypeUniverseIndex(self) -> int:
        return self.value.getTypeUniverseIndex()
    
    def isCVarArgCompatibleTypeNode(self) -> bool:
        return self.value.isCVarArgCompatibleType()
    
    def performSatisfiedByCheckInEnvironment(self, other, environment) -> bool:
        if self.value.isCVarArgType():
            if other.isCVarArgCompatibleTypeNode():
                return True, environment

        return super().performSatisfiedByCheckInEnvironment(other, environment)

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
    
    def isFunctionTypeLiteralValue(self) -> bool:
        return self.value.isFunctionType()

    def isTypedLiteralFunctionalValue(self) -> bool:
        return self.value.isFunctionalValue()
    
    def isTypedLiteralReducibleFunctionalValue(self) -> bool:
        return self.value.isReducibleFunctionalValue()
    
    def isArrayTypeNodeOrLiteral(self) -> bool:
        return self.value.isArrayType()
    
    def isPointerTypeNodeOrLiteral(self) -> bool:
        return self.value.isPointerType()

    def isReferenceLikeTypeNodeOrLiteral(self) -> bool:
        return self.value.isReferenceType() or self.value.isTemporaryReferenceType()
    
    def isProductTypeNodeOrLiteral(self) -> bool:
        return self.value.isProductType()
    
    def isRecordTypeNodeOrLiteral(self) -> bool:
        return self.value.isRecordType()

    def isSumTypeNodeOrLiteral(self) -> bool:
        return self.value.isSumType()

    def isCVarArgTypeNode(self) -> bool:
        return self.value.isCVarArgType()
    
    def asUnpackedTupleTypeExpressionsAt(self, sourcePosition: SourcePosition):
        return list(map(lambda t: ASTLiteralTypeNode(sourcePosition, t), self.value.elementTypes))
    
    def accept(self, visitor):
        return visitor.visitLiteralTypeNode(self)
    
    def asTypedFunctionTypeNodeAtFor(self, sourcePosition, typechecker):
        return self.value.asTypedFunctionTypeNodeAtFor(sourcePosition, typechecker)

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
        return self.value.prettyPrint()

    def isTypedLiteralNode(self) -> bool:
        return True

    def isPiLiteralValue(self) -> bool:
        return self.value.isPi()

    def isTypedLiteralFunctionalValue(self) -> bool:
        return self.value.isFunctionalValue()

    def isTypedLiteralReducibleFunctionalValue(self) -> bool:
        return self.value.isReducibleFunctionalValue()

    def isEquivalentTo(self, other: ASTNode) -> bool:
        if self == other:
            return True
        elif other.isLiteralTypeNode():
            return self.value.isEquivalentTo(other.value)
        elif other.isTypedLiteralNode():
            return self.value.isEquivalentTo(other.value)
        else:
            return False
        
    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return self.value.attemptToUnpackTupleExpressionsAt(sourcePosition)

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
    
    def prettyPrint(self) -> str:
        return self.name.prettyPrint()
    
    def evaluateInActivationEnvironmentAt(self, activationEnvironment, sourcePosition: SourcePosition) -> TypedValue:
        return activationEnvironment.lookBindingValueAt(self, sourcePosition)

    def evaluateSubstitutionInContextFor(self, substitutionContext, oldNode: ASTTypedNode) -> ASTTypedNode:
        return substitutionContext.lookSubstitutionForBindingInNode(self, oldNode)

    @abstractmethod
    def getTypeExpression(self) -> ASTNode:
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

    def isImplicitValueBinding(self) -> bool:
        return False

    ## The nesting level of the capture. This corresponds with the Bruijn index of the binding if lambdas only have a single argument.
    @abstractmethod
    def getCaptureNestingLevel(self) -> int:
        pass

class ASTTypedIdentifierReferenceNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, binding: SymbolBinding) -> None:
        super().__init__(sourcePosition, type)
        self.binding = binding

    def prettyPrint(self) -> str:
        return self.binding.prettyPrint()

    def isEquivalentTo(self, other) -> bool:
        if self == other: return True
        if not other.isTypedIdentifierReferenceNode(): return False
        return self.binding.isEquivalentTo(other.binding)

    def performEquivalenceCheckInEnvironment(self, other, environment) -> bool:
        if self == other: return True, environment
        if other.isTypedIdentifierReferenceNode() and other.binding.isEquivalentTo(self.binding): return True, environment

        if self.binding.isImplicitValueBinding() and not environment.hasSubstitutionForImplicitValueBinding(self.binding):
            if other.isTypedIdentifierReferenceNode() and other.binding.isImplicitValueBinding():
                return False
            return True, environment.withImplicitValueBindingSubstitution(self.binding, other)
        return super().performEquivalenceCheckInEnvironment(other, environment)

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

    def evaluateSubstitutionInContextAt(self, substitutionContext, sourcePosition: SourcePosition) -> ASTNode:
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
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTTypeNode, valueExpression: ASTNode, isMutable: bool) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression
        self.valueExpression = valueExpression
        self.isMutable = isMutable

    def getTypeExpression(self) -> ASTTypeNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 0
    
    def toJson(self):
        return {'localBinding': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

class SymbolArgumentBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTNode, isImplicit = False, isExistential = False) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression
        self.isImplicit = isImplicit
        self.isExistential = isExistential

    def getTypeExpression(self) -> ASTNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 0
    
    def hasTypeOf(self, expectedType: TypedValue):
        return self.typeExpression.isLiteralTypeNode() and self.typeExpression.value.isEquivalentTo(expectedType)

    def toJson(self):
        return {'argument': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

class SymbolImplicitValueBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, typeExpression: ASTNode) -> None:
        super().__init__(sourcePosition, name)
        self.typeExpression = typeExpression
    
    def getTypeExpression(self) -> ASTNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 0
    
    def isImplicitValueBinding(self) -> bool:
        return True

    def toJson(self):
        return {'implicitValue': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

class Module(TypedValue):
    def __init__(self, name: TypedValue) -> None:
        super().__init__()
        self.name = name
        self.importedModuleDictionary = dict()
        self.importedModules = []
        self.exportedBindings = []
        self.exportedValues = []
        self.entryPoint = None

    def importModuleNamed(self, name):
        if name in self.importedModuleDictionary:
            return self.importedModuleDictionary[name]
        
        importedModule = ImportedModule(name)
        self.importedModuleDictionary[name] = importedModule
        return importedModule


    def exportBinding(self, binding: SymbolBinding):
        if binding in self.exportedBindings:
            return
        self.exportedBindings.append(binding)

    def exportValue(self, name: Symbol, value: TypedValue, externalName: Symbol = None):
        self.exportedValues.append((name, value, externalName))

    def getType(self):
        return ModuleType
    
    def toJson(self):
        return {'module': str(self.name), 'entryPointBinding': optionalToJson(self.entryPoint)}

class ImportedModuleValue(TypedValue):
    def __init__(self, module, name: TypedValue, type: TypedValue) -> None:
        super().__init__()
        self.module = module
        self.name = name
        self.type = type

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitImportedModuleValue(self)

    def getType(self):
        return self.type
    
    def toJson(self):
        return {'importedModuleValue': self.module.name.toJson(), 'name': self.name.toJson(), 'type': self.type.toJson()}

class ImportedExternalValue(TypedValue):
    def __init__(self, externalName: TypedValue, name: TypedValue, type: TypedValue) -> None:
        super().__init__()
        self.externalName = externalName
        self.name = name
        self.type = type

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitImportedExternalValue(self)

    def getType(self):
        return self.type
    
    def toJson(self):
        return {'importedExternalValue': self.externalName.toJson(), 'name': self.name.toJson(), 'type': self.type.toJson()}

class ImportedModule(TypedValue):
    def __init__(self, name: TypedValue) -> None:
        super().__init__()
        self.name = name
        self.importedValues: list[ImportedModuleValue] = []

    def acceptTypedValueVisitor(self, visitor: TypedValueVisitor):
        return visitor.visitImportedModule(self)
    
    def getType(self):
        return ModuleType
    
    def importValueWithType(self, name: TypedValue, type: TypedValue) -> ImportedModuleValue:
        for importedValue in self.importedValues:
            if name.isEquivalentTo(importedValue.name) and type.isEquivalentTo(importedValue.type):
                return importedValue
            
        importedValue = ImportedModuleValue(self, name, type)
        self.importedValues.append(importedValue)
        return importedValue
    
    def toJson(self):
        return {'importedModule': str(self.name)}

def optionalToJson(value: TypedValue):
    if value is None:
        return None
    else:
        return value.toJson()
