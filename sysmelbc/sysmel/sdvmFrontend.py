from .ghir import *
from .sdvmInstructions import *
from .sdvmModule import *

class SDVMModuleFrontEnd:
    def __init__(self) -> None:
        self.module = SDVMModule()

    def compileGHIRModule(self, ghirModule: GHIRModule) -> SDVMModule:
        self.module.finishBuilding()
        entryPointFunction = self.module.newFunction()
        entryPointFunction.inst(SdvmInstReturnInt32, entryPointFunction.constInt32(0))
        self.module.entryPoint = entryPointFunction.index
        self.module.finishBuilding()
        return self.module
    
