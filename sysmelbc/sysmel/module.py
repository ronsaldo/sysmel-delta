from .target import *
from .namespace import *

class ModuleExportedValue:
    def __init__(self, name: str, value, externalName: str = None):
        self.name = name
        self.value = value
        self.externalName = externalName
        self.mirValue = None

class Module:
    def __init__(self, name: str, target: CompilationTarget) -> None:
        self.name = name
        self.target = target
        self.exportedValues = []
        self.mirExportedValues = []
        self.globalNamespace = Namespace('__global')

    def exportValueWithName(self, value, name, externalName):
        self.exportedValues.append(ModuleExportedValue(name, value, externalName))
