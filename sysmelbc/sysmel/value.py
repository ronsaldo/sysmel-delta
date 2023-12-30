from abc import ABC, abstractmethod

class TypedValue(ABC):
    @abstractmethod
    def getType(self):
        pass

    @abstractmethod
    def toJson(self):
        pass

class TypeUniverse(TypedValue):
    InstancedUniverses = dict()
    def __init__(self, index: int) -> None:
        super().__init__()

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

TypeType = TypeUniverse.getWithIndex(0)

class BaseType(TypedValue):
    def __init__(self, name: str) -> None:
        self.name = name

    def getType(self) -> TypedValue:
        return TypeType

    def toJson(self):
        return self.name

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
        if variantTypes in cls.SumTypeCache:
            return cls.SumTypeCache[variantTypes]

        sumType = cls(variantTypes)
        cls.SumTypeCache[variantTypes] = sumType
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
