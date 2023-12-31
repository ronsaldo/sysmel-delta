from abc import ABC, abstractmethod

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

class TypeUniverse(TypedValue):
    InstancedUniverses = dict()
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def toJson(self):
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

AbsurdType = AbsurdTypeClass("Absurd")
UnitType = UnitTypeClass("Unit", "unit")

IntegerType = IntegerTypeClass("Integer")
FloatType = FloatTypeClass("Float")
CharacterType = CharacterTypeClass("Character")
StringType = StringTypeClass("String")
    
class IntegerValue(TypedValue):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def getType(self) -> TypedValue:
        return IntegerType

    def toJson(self):
        return self.value
    

class FloatValue(TypedValue):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def getType(self):
        return FloatType

    def toJson(self):
        return self.value

class CharacterValue(TypedValue):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def getType(self):
        return CharacterType

    def toJson(self):
        return self.value

class StringValue(TypedValue):
    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = str

    def getType(self):
        return StringType

    def toJson(self):
        return self.value

class ProductTypeValue(TypedValue):
    def __init__(self, type: TypedValue, elements: tuple) -> None:
        super().__init__()
        self.elements = elements
        self.type = type

    def getType(self):
        return self.type

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

    def toJson(self):
        return {'productType': list(map(lambda v: v.toJson(), self.elementTypes))}
    
    @classmethod
    def makeWithElementTypes(cls, elementTypes: list[TypedValue]):
        if elementTypes in cls.ProductTypeCache:
            return cls.ProductTypeCache[elementTypes]

        productType = cls(elementTypes)
        cls.ProductTypeCache[elementTypes] = productType
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

    def isLiteralTypeNode(self) -> bool:
        return False

    def isTypedLiteralNode(self) -> bool:
        return False
    
    def isTypedErrorNode(self) -> bool:
        return False

class ASTLiteralTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def computeTypeUniverseIndex(self) -> int:
        return self.value.getTypeUniverseIndex()

    def isLiteralTypeNode(self) -> bool:
        return True

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

class SymbolBinding(ABC):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol) -> None:
        super().__init__()
        self.sourcePosition = sourcePosition
        self.name = name

    @abstractmethod
    def getTypeExpression(self) -> ASTLiteralTypeNode | ASTTypedNode:
        pass

    def isValueBinding(self) -> bool:
        return False

    ## The nesting level of the capture. This corresponds with the Bruijn index of the binding if lambdas only have a single argument.
    @abstractmethod
    def getCaptureNestingLevel(self) -> int:
        pass

class SymbolValueBinding(SymbolBinding):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, value: TypedValue) -> None:
        super().__init__(sourcePosition, name)
        self.value = value
        self.typeExpression = ASTLiteralTypeNode(sourcePosition, self.value.getType())

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

class SymbolCaptureBinding(SymbolBinding):
    def __init__(self, capturedBinding: SymbolBinding) -> None:
        super().__init__(capturedBinding.sourcePosition, capturedBinding.name)
        self.capturedBinding = capturedBinding
        self.captureNestingLevel = capturedBinding.getCaptureNestingLevel() + 1

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

class LambdaValue(TypedValue):
    def __init__(self, type: TypedValue, captureBindings: list[SymbolCaptureBinding], captureValues: list[TypedValue], argumentBinding: SymbolArgumentBinding, body) -> None:
        super().__init__()
        self.type = type
        self.captureBindings = captureBindings
        self.captureValues = captureValues
        self.argumentBinding = argumentBinding
        self.body = body

    def getType(self):
        return self.type

    def toJson(self):
        return {'lambda': self.argumentBinding.toJson(), 'body': self.body.toJson()}

class ForAllValue(TypedValue):
    def __init__(self, type: TypedValue, captureBindings: list[SymbolCaptureBinding], captureValues: list[TypedValue], argumentBinding: SymbolArgumentBinding, body) -> None:
        super().__init__()
        self.type = type
        self.captureBindings = captureBindings
        self.captureValues = captureValues
        self.argumentBinding = argumentBinding
        self.body = body

    def getType(self):
        return self.type

    def toJson(self):
        return {'forAll': self.argumentBinding.toJson(), 'body': self.body.toJson()}

TopLevelEnvironment = LexicalEnvironment(EmptyEnvironment.getSingleton())
TopLevelEnvironment.addBaseType(AbsurdType)
TopLevelEnvironment.addBaseType(UnitType)
TopLevelEnvironment.addUnitTypeValue(UnitType.getSingleton())
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

def makeDefaultEvaluationEnvironment() -> LexicalEnvironment:
    return LexicalEnvironment(TopLevelEnvironment)