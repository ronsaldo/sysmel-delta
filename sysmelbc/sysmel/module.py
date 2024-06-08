class ModuleExportedValue:
    def __init__(self, name: str, value, externalName: str = None):
        self.name = name
        self.value = value
        self.externalName = externalName
        self.mirValue = None

class Module:
    def __init__(self, name: str) -> None:
        self.name = name
        self.exportedValues = []
        self.mirExportedValues = []

    def exportValueWithName(self, value, name, externalName):
        self.exportedValues.append(ModuleExportedValue(name, value, externalName))
