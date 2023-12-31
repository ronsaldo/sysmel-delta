from abc import ABC, abstractmethod
import json

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
    
    def isForAll(self) -> bool:
        return False

    def isEquivalentTo(self, other) -> bool:
        return self == other

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
        return self.index + 1

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

AbsurdType = AbsurdTypeClass("Absurd")
UnitType = UnitTypeClass("Unit", "unit")

NatType = IntegerTypeClass("Nat")
IntegerType = IntegerTypeClass("Integer")
FloatType = FloatTypeClass("Float")
CharacterType = CharacterTypeClass("Character")
StringType = StringTypeClass("String")

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

class CharacterValue(TypedValue):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def getType(self):
        return CharacterType

    def isEquivalentTo(self, other: TypedValue) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def toJson(self):
        return self.value

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

class ASTNode:
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

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
    
    def isForAllLiteralValue(self) -> bool:
        return False

    def isTypedForAllNode(self) -> bool:
        return False

    def isTypedForAllNodeOrLiteralValue(self) -> bool:
        return self.isForAllLiteralValue() or self.isTypedForAllNode()

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

    def isForAllLiteralValue(self) -> bool:
        return self.value.isForAll()

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

    def isForAllLiteralValue(self) -> bool:
        return self.value.isForAll()

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

    @abstractmethod
    def evaluateInActivationContext(self, activationContext) -> TypedValue:
        pass

    @abstractmethod
    def evaluateSubstitutionInContext(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode:
        pass

    @abstractmethod
    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        pass

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

    def evaluateInActivationContext(self, activationContext) -> TypedValue:
        return self.value

    def evaluateSubstitutionInContext(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode:
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

    def evaluateInActivationContext(self, activationContext) -> TypedValue:
        return activationContext.getArgumentValueFor(self)

    def evaluateSubstitutionInContext(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode:
        return substitutionContext.getArgumentSubstitutionFor(self, sourcePosition)

    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        return self.typeExpression

    def getCaptureNestingLevel(self) -> int:
        return 1

    def toJson(self):
        return {'name': repr(self.name), 'typeExpression': self.typeExpression.toJson()}

class SymbolCaptureBinding(SymbolBinding):
    def __init__(self, capturedBinding: SymbolBinding) -> None:
        super().__init__(capturedBinding.sourcePosition, capturedBinding.name)
        self.capturedBinding = capturedBinding
        self.captureNestingLevel = capturedBinding.getCaptureNestingLevel() + 1

    def evaluateInActivationContext(self, activationContext) -> TypedValue:
        return activationContext.getCaptureValueFor(self)

    def evaluateSubstitutionInContext(self, substitutionContext, sourcePosition: SourcePosition) -> ASTTypedNode:
        return substitutionContext.getCaptureSubstitutionFor(self, sourcePosition)

    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        return self.capturedBinding.getTypeExpression()
    
    def getCaptureNestingLevel(self) -> int:
        return self.captureNestingLevel

class AbstractEnvironment(ABC):
    @abstractmethod
    def lookSymbolRecursively(symbol: Symbol) -> SymbolBinding:
        pass

class EmptyEnvironment(AbstractEnvironment):
    Singleton = None
    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding:
        return None
    
    @classmethod
    def getSingleton(cls):
        if cls.Singleton is None:
            cls.Singleton = cls()
        return cls.Singleton

class LexicalEnvironment(AbstractEnvironment):
    def __init__(self, parent: AbstractEnvironment, sourcePosition: SourcePosition = None) -> None:
        self.parent = parent
        self.sourcePosition = sourcePosition
        self.symbolTable: dict[Symbol, SymbolBinding] = dict()

    def setSymbolBinding(self, symbol: Symbol, binding: SymbolBinding) -> None:
        if symbol in self.symbolTable:
            raise Exception("Overriding symbol " + str(symbol))
        self.symbolTable[symbol] = binding

    def setSymbolValueBinding(self, symbol: Symbol, value: TypedValue, sourcePosition: SourcePosition = None) -> None:
        self.setSymbolBinding(symbol, SymbolValueBinding(sourcePosition, symbol, value))

    def lookSymbol(self, symbol: Symbol) -> SymbolBinding | None:
        return self.symbolTable.get(symbol, None)

    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding | None:
        binding = self.lookSymbol(symbol)
        if binding is not None:
            return binding

        return self.parent.lookSymbolRecursively(symbol)
    
    def addBaseType(self, baseType: BaseType):
        assert baseType.name is not None
        self.setSymbolValueBinding(Symbol.intern(baseType.name), baseType)

    def addUnitTypeValue(self, unitTypeValue: UnitTypeValue):
        assert unitTypeValue.name is not None
        self.setSymbolValueBinding(Symbol.intern(unitTypeValue.name), unitTypeValue)

class LambdaEnvironment(LexicalEnvironment):
    def __init__(self, parent: AbstractEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.argumentBinding = None
        self.captureBindings = []
        self.captureCache = dict()

    def setArgumentBinding(self, binding: SymbolArgumentBinding):
        if binding.name is not None:
            self.setSymbolBinding(binding.name, binding)
        self.argumentBinding = binding

    def lookSymbolRecursively(self, symbol: Symbol) -> SymbolBinding | None:
        binding = self.lookSymbol(symbol)
        if binding is not None:
            return binding
        
        if symbol in self.captureCache:
            return self.captureCache[symbol]
        
        parentSymbol = self.parent.lookSymbolRecursively(symbol)
        if parentSymbol is None:
            return parentSymbol
        
        if parentSymbol.isValueBinding():
            return parentSymbol
        
        captureBinding = SymbolCaptureBinding(parentSymbol)
        self.captureBindings.append(captureBinding)
        return captureBinding

class FunctionalValue(TypedValue):
    def __init__(self, type: TypedValue, captureBindings: list[SymbolCaptureBinding], captureValues: list[TypedValue], argumentBinding: SymbolArgumentBinding, body) -> None:
        super().__init__()
        self.type = type
        self.captureBindings = captureBindings
        self.captureValues = captureValues
        self.argumentBinding = argumentBinding
        self.body = body

    def getCaptureValueFor(self, captureBinding: SymbolCaptureBinding) -> TypedValue:
        return self.captureValues[self.captureBindings.index(captureBinding)]

    def getType(self):
        return self.type

class LambdaValue(FunctionalValue):
    def toJson(self):
        return {'lambda': self.argumentBinding.toJson(), 'body': self.body.toJson()}

class ForAllValue(FunctionalValue):
    def getType(self):
        return self.type

    def toJson(self):
        return {'forAll': self.argumentBinding.toJson(), 'body': self.body.toJson()}
    
    def isForAll(self) -> bool:
        return True

class FunctionalActivationContext:
    def __init__(self, functionalValue: FunctionalValue, argumentValue: TypedValue):
        self.functionalValue = functionalValue
        self.argumentValue = argumentValue

    def getArgumentValueFor(self, argumentBinding: SymbolArgumentBinding) -> TypedValue:
        assert argumentBinding == self.functionalValue.argumentBinding
        return self.argumentValue

    def getCaptureValueFor(self, captureBinding: SymbolCaptureBinding) -> TypedValue:
        return self.functionalValue.getCaptureValue(captureBinding)

class SubstitutionContext:
    def __init__(self, captureBindings: list[SymbolCaptureBinding], captureSubstitutions: list[ASTNode], argumentBinding: SymbolArgumentBinding, argumentSubstitution: ASTNode) -> None:
        self.captureBindings = captureBindings
        self.captureSubstitutions = captureSubstitutions
        self.argumentBinding = argumentBinding
        self.argumentSubstitution = argumentSubstitution

    def getArgumentSubstitutionFor(self, argumentBinding: SymbolArgumentBinding, sourcePosition: SourcePosition) -> ASTNode:
        assert argumentBinding == self.argumentBinding
        return self.applySourcePositionToSubstitution(self.argumentSubstitution, sourcePosition)

    def getCaptureSubstitutionFor(self, captureBinding: SymbolCaptureBinding, sourcePosition: SourcePosition) -> ASTNode:
        return self.applySourcePositionToSubstitution(self.captureSubstitutions[self.captureBindings.index(captureBinding)], sourcePosition)
    
    def applySourcePositionToSubstitution(self, substitution: ASTNode, sourcePosition: SourcePosition) -> ASTNode:
        if substitution.isTypedIdentifierReferenceNode():
            return ASTTypedIdentifierReferenceNode(sourcePosition, substitution.type, substitution.binding)
        return substitution

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
TopLevelEnvironment.addBaseType(AbsurdType)
TopLevelEnvironment.addBaseType(UnitType)
TopLevelEnvironment.addUnitTypeValue(UnitType.getSingleton())
TopLevelEnvironment.addBaseType(NatType)
TopLevelEnvironment.addBaseType(IntegerType)
TopLevelEnvironment.addBaseType(FloatType)
TopLevelEnvironment.addBaseType(CharacterType)
TopLevelEnvironment.addBaseType(StringType)

## Boolean :: False | True.
FalseType = UnitTypeClass("False", "false")
TrueType = UnitTypeClass("True", "true")
BooleanType = SumType.makeWithVariantTypes([FalseType, TrueType])
TopLevelEnvironment.addBaseType(FalseType)
TopLevelEnvironment.addUnitTypeValue(FalseType.getSingleton())
TopLevelEnvironment.addBaseType(TrueType)
TopLevelEnvironment.addUnitTypeValue(TrueType.getSingleton())
TopLevelEnvironment.setSymbolValueBinding(Symbol.intern("Boolean"), BooleanType)
TopLevelEnvironment.setSymbolValueBinding(Symbol.intern("Type"), TypeType)

def makeDefaultEvaluationEnvironment() -> LexicalEnvironment:
    return LexicalEnvironment(TopLevelEnvironment)