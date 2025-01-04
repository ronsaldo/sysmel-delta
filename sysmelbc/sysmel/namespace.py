class Namespace:
    def __init__(self, name: str, parent = None) -> None:
        self.name = name
        self.exportedValues = []
        self.mirExportedValues = []
        self.subnamespaces = []
        self.subnamespaceDictionary = {}

    def getOrCreateSubNamespace(self, name):
        if name in self.subnamespaceDictionary:
            return self.subnamespaceDictionary[name]
        
        subnamespace = Namespace(name, self)
        self.subnamespaces.append(subnamespace)
        self.subnamespaceDictionary[name] = subnamespace
        return subnamespace
    