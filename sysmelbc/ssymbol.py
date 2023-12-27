class Symbol:
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return '#' + repr(self.value)
    
    def __str__(self) -> str:
        return '#' + repr(self.value)
    
InternedSymbolDictionary = dict()

def intern(value: str) -> Symbol:
    if value in InternedSymbolDictionary:
        return InternedSymbolDictionary[value]
    
    newSymbol = Symbol(value)
    InternedSymbolDictionary[value] = newSymbol
    return newSymbol
