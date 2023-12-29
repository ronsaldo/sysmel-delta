from .value import *

class SymbolTypeClass(BaseType):
    pass

SymbolType = SymbolTypeClass("Symbol")

class Symbol(TypedValue):
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return '#' + repr(self.value)
    
    def __str__(self) -> str:
        return '#' + repr(self.value)
    
    def getType(self):
        return SymbolType

    def toJson(self):
        return repr(self)
    
InternedSymbolDictionary = dict()

def intern(value: str) -> Symbol:
    if value in InternedSymbolDictionary:
        return InternedSymbolDictionary[value]
    
    newSymbol = Symbol(value)
    InternedSymbolDictionary[value] = newSymbol
    return newSymbol
