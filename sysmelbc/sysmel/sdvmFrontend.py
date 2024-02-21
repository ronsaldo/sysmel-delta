from .mir import *
from .sdvmInstructions import *
from .sdvmModule import *

class SDVMModuleFrontEnd:
    def __init__(self) -> None:
        self.module = SDVMModule()
        self.translatedFunctionDictionary = dict()
        self.constantTranslationFunctions = dict()
        self.argumentInstructionDictionary = dict()
        self.callArgumentInstructionDictionary = dict()
        self.callInstructionDictionary = dict()
        self.returnInstructionDictionary = dict()

    def compileMIRModule(self, mirModule: MIRModule) -> SDVMModule:
        mirContext = mirModule.context
        for type, constantTranslationFunction, argumentInst, callArgumentInst, callInst, returnInst in [
            (mirContext.voidType,  None,  None,  None,  SdvmInstCallVoid, SdvmInstReturnVoid),
            (mirContext.booleanType,  SDVMFunction.constBoolean,  SdvmInstArgBoolean,  SdvmInstCallArgBoolean,  SdvmInstCallBoolean, SdvmInstReturnBoolean),
            (mirContext.int8Type,  SDVMFunction.constInt8,  SdvmInstArgInt8,  SdvmInstCallArgInt8,  SdvmInstCallInt8, SdvmInstReturnInt8),
            (mirContext.int16Type, SDVMFunction.constInt16, SdvmInstArgInt16, SdvmInstCallArgInt16, SdvmInstCallInt16, SdvmInstReturnInt16),
            (mirContext.int32Type, SDVMFunction.constInt32, SdvmInstArgInt32, SdvmInstCallArgInt32, SdvmInstCallInt32, SdvmInstReturnInt32),
            (mirContext.int64Type, SDVMFunction.constInt64, SdvmInstArgInt64, SdvmInstCallArgInt64, SdvmInstCallInt64, SdvmInstReturnInt64),
            (mirContext.uint8Type,  SDVMFunction.constUInt8,  SdvmInstArgUInt8,  SdvmInstCallArgUInt8,  SdvmInstCallUInt8, SdvmInstReturnUInt8),
            (mirContext.uint16Type, SDVMFunction.constUInt16, SdvmInstArgUInt16, SdvmInstCallArgUInt16, SdvmInstCallUInt16, SdvmInstReturnUInt16),
            (mirContext.uint32Type, SDVMFunction.constUInt32, SdvmInstArgUInt32, SdvmInstCallArgUInt32, SdvmInstCallUInt32, SdvmInstReturnUInt32),
            (mirContext.uint64Type, SDVMFunction.constUInt64, SdvmInstArgUInt64, SdvmInstCallArgUInt64, SdvmInstCallUInt64, SdvmInstReturnUInt64),
            (mirContext.float32Type, SDVMFunction.constFloat32, SdvmInstArgFloat32, SdvmInstCallArgFloat32, SdvmInstCallFloat32, SdvmInstReturnFloat32),
            (mirContext.float64Type, SDVMFunction.constFloat64, SdvmInstArgFloat64, SdvmInstCallArgFloat64, SdvmInstCallFloat64, SdvmInstReturnFloat64),
            (mirContext.pointerType,  None,  SdvmInstArgPointer,  SdvmInstCallArgPointer,  SdvmInstCallPointer, SdvmInstReturnPointer),
            (mirContext.gcPointerType,  None,  SdvmInstArgGCPointer,  SdvmInstCallArgGCPointer,  SdvmInstCallGCPointer, SdvmInstReturnGCPointer),
        ]:
            self.constantTranslationFunctions[type] = constantTranslationFunction
            self.argumentInstructionDictionary[type] = argumentInst
            self.callArgumentInstructionDictionary[type] = callArgumentInst
            self.callInstructionDictionary[type] = callInst
            self.returnInstructionDictionary[type] = returnInst
        if mirModule.entryPoint is not None:
            self.module.entryPoint = self.translateFunction(mirModule.entryPoint).index

        #if mirModule.entryPointClosure is not None:
        #    self.module.entryPointClosure = self.translateGlobalValue(mirModule.entryPointClosure).index
        #entryPointFunction = self.module.newFunction()
        #entryPointFunction.inst(SdvmInstReturnInt32, entryPointFunction.constInt32(0))
        #self.module.entryPoint = entryPointFunction.index

        self.module.finishBuilding()
        return self.module
    
    def translateFunction(self, mirFunction: MIRFunction) -> SDVMFunction:
        if mirFunction in self.translatedFunctionDictionary:
            return self.translatedFunctionDictionary[mirFunction]

        function = self.module.newFunction(mirFunction.name)
        self.translatedFunctionDictionary[mirFunction] = function
        SDVMFunctionFrontEnd(self).translateMirFunctionInto(mirFunction, function)
        return function


class SDVMFunctionFrontEnd:
    def __init__(self, moduleFrontend: SDVMModuleFrontEnd) -> None:
        self.moduleFrontend = moduleFrontend
        self.function: SDVMFunction = None
        self.translatedValueDictionary = dict()

    def translateMirFunctionInto(self, mirFunction: MIRFunction, function: SDVMFunction):
        self.function = function

        # Translate the arguments.
        self.function.beginArguments(len(mirFunction.arguments))
        for argument in mirFunction.arguments:
            self.translateArgument(argument)
        
        # Translate the captures
        self.function.beginCaptures(len(mirFunction.captures))
        for capture in mirFunction.captures:
            self.translateCapture(capture)

        # Translate the basic blocks
        self.translateBasicBlocksOf(mirFunction)

    def translateArgument(self, mirArgument: MIRArgument):
        pass

    def translateCapture(self, mirCapture: MIRArgument):
        pass

    def translateBasicBlocksOf(self, mirFunction: MIRFunction):
        basicBlocks = mirFunction.basicBlocksInReversePostOrder()
        for basicBlock in basicBlocks:
            basicBlockLabel = SDVMInstruction(SdvmConstLabel)
            self.translatedValueDictionary[basicBlock] = basicBlockLabel

        for basicBlock in basicBlocks:
            self.translateBasicBlock(basicBlock)

    def translateBasicBlock(self, basicBlock: MIRBasicBlock) -> SDVMOperand:
        basicBlockLabel = self.translatedValueDictionary[basicBlock]
        self.function.addInstruction(basicBlockLabel)
        for instruction in basicBlock.instructions():
            self.translateInstruction(instruction)
        return basicBlockLabel
    
    def translateInstruction(self, instruction: MIRInstruction) -> SDVMOperand:
        assert instruction not in self.translatedValueDictionary
        translatedValue = instruction.accept(self)
        self.translatedValueDictionary[instruction] = translatedValue
        return translatedValue
    
    def translateValue(self, value: MIRValue) -> SDVMOperand:
        if value.isFunctionLocalValue():
            return self.translatedValueDictionary[value]
        return self.translateConstant(value)

    def translateConstant(self, value: MIRValue) -> SDVMOperand:
        assert value.isConstant()
        if value in self.translatedValueDictionary:
            return self.translatedValueDictionary[value]

        translatedValue = value.accept(self)
        self.translatedValueDictionary[value] = translatedValue
        return translatedValue
    
    def visitConstantInteger(self, instruction: MIRConstantInteger) -> SDVMOperand:
        return self.moduleFrontend.constantTranslationFunctions[instruction.getType()](self.function, instruction.value)

    def visitReturnInstruction(self, instruction: MIRReturnInstruction) -> SDVMOperand:
        result = self.translateValue(instruction.result)
        return self.function.addInstruction(SDVMInstruction(self.moduleFrontend.returnInstructionDictionary[instruction.result.type], result))