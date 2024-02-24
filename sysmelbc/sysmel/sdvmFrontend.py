from .mir import *
from .sdvmInstructions import *
from .sdvmModule import *

class SDVMModuleFrontEnd:
    def __init__(self) -> None:
        self.module = SDVMModule()
        self.translatedFunctionDictionary = dict()
        self.translatedValueDictionary = dict()
        self.constantTranslationFunctions = dict()
        self.constantImportInstructionDictionary = dict()
        self.argumentInstructionDictionary = dict()
        self.callArgumentInstructionDictionary = dict()
        self.callInstructionDictionary = dict()
        self.callClosureInstructionDictionary = dict()
        self.returnInstructionDictionary = dict()

    def compileMIRModule(self, mirModule: MIRModule) -> SDVMModule:
        mirContext = mirModule.context
        for type, constantTranslationFunction, constImportInstruction, argumentInst, callArgumentInst, callInst, callClosureInst, returnInst in [
            (mirContext.voidType,      None,                       None,                     None,                 None,                     SdvmInstCallVoid,      SdvmInstCallClosureVoid,      SdvmInstReturnVoid),
            (mirContext.booleanType,   SDVMFunction.constBoolean,  SdvmConstImportBoolean,   SdvmInstArgBoolean,   SdvmInstCallArgBoolean,   SdvmInstCallBoolean,   SdvmInstCallClosureBoolean,   SdvmInstReturnBoolean),
            (mirContext.int8Type,      SDVMFunction.constInt8,     SdvmConstImportInt8,      SdvmInstArgInt8,      SdvmInstCallArgInt8,      SdvmInstCallInt8,      SdvmInstCallClosureInt8,      SdvmInstReturnInt8),
            (mirContext.int16Type,     SDVMFunction.constInt16,    SdvmConstImportInt16,     SdvmInstArgInt16,     SdvmInstCallArgInt16,     SdvmInstCallInt16,     SdvmInstCallClosureInt16,     SdvmInstReturnInt16),
            (mirContext.int32Type,     SDVMFunction.constInt32,    SdvmConstImportInt32,     SdvmInstArgInt32,     SdvmInstCallArgInt32,     SdvmInstCallInt32,     SdvmInstCallClosureInt32,     SdvmInstReturnInt32),
            (mirContext.int64Type,     SDVMFunction.constInt64,    SdvmConstImportInt64,     SdvmInstArgInt64,     SdvmInstCallArgInt64,     SdvmInstCallInt64,     SdvmInstCallClosureInt64,     SdvmInstReturnInt64),
            (mirContext.uint8Type,     SDVMFunction.constUInt8,    SdvmConstImportUInt8,     SdvmInstArgUInt8,     SdvmInstCallArgUInt8,     SdvmInstCallUInt8,     SdvmInstCallClosureUInt8,     SdvmInstReturnUInt8),
            (mirContext.uint16Type,    SDVMFunction.constUInt16,   SdvmConstImportUInt16,    SdvmInstArgUInt16,    SdvmInstCallArgUInt16,    SdvmInstCallUInt16,    SdvmInstCallClosureUInt16,    SdvmInstReturnUInt16),
            (mirContext.uint32Type,    SDVMFunction.constUInt32,   SdvmConstImportUInt32,    SdvmInstArgUInt32,    SdvmInstCallArgUInt32,    SdvmInstCallUInt32,    SdvmInstCallClosureUInt32,    SdvmInstReturnUInt32),
            (mirContext.uint64Type,    SDVMFunction.constUInt64,   SdvmConstImportUInt64,    SdvmInstArgUInt64,    SdvmInstCallArgUInt64,    SdvmInstCallUInt64,    SdvmInstCallClosureUInt64,    SdvmInstReturnUInt64),
            (mirContext.float32Type,   SDVMFunction.constFloat32,  SdvmConstImportFloat32,   SdvmInstArgFloat32,   SdvmInstCallArgFloat32,   SdvmInstCallFloat32,   SdvmInstCallClosureFloat32,   SdvmInstReturnFloat32),
            (mirContext.float64Type,   SDVMFunction.constFloat64,  SdvmConstImportFloat64,   SdvmInstArgFloat64,   SdvmInstCallArgFloat64,   SdvmInstCallFloat64,   SdvmInstCallClosureFloat64,   SdvmInstReturnFloat64),
            (mirContext.pointerType,   None,                       SdvmConstImportPointer,   SdvmInstArgPointer,   SdvmInstCallArgPointer,   SdvmInstCallPointer,   SdvmInstCallClosurePointer,   SdvmInstReturnPointer),
            (mirContext.gcPointerType, None,                       SdvmConstImportGCPointer, SdvmInstArgGCPointer, SdvmInstCallArgGCPointer, SdvmInstCallGCPointer, SdvmInstCallClosureGCPointer, SdvmInstReturnGCPointer),
        ]:
            self.constantTranslationFunctions[type] = constantTranslationFunction
            self.constantImportInstructionDictionary[type] = constImportInstruction
            self.argumentInstructionDictionary[type] = argumentInst
            self.callArgumentInstructionDictionary[type] = callArgumentInst
            self.callInstructionDictionary[type] = callInst
            self.callClosureInstructionDictionary[type] = callClosureInst
            self.returnInstructionDictionary[type] = returnInst

        for globalValue in mirModule.globalValues:
            self.translateValue(globalValue)

        for name, value in mirModule.exportedValues:
            self.module.exportValue(name, self.translateValue(value))
        if mirModule.entryPoint is not None:
            self.module.entryPoint = self.translateFunction(mirModule.entryPoint).index

        #if mirModule.entryPointClosure is not None:
        #    self.module.entryPointClosure = self.translateGlobalValue(mirModule.entryPointClosure).index
        #entryPointFunction = self.module.newFunction()
        #entryPointFunction.inst(SdvmInstReturnInt32, entryPointFunction.constInt32(0))
        #self.module.entryPoint = entryPointFunction.index

        self.module.finishBuilding()
        return self.module
    
    def translateValue(self, mirValue: MIRValue):
        if mirValue in self.translatedValueDictionary:
            return self.translatedValueDictionary[mirValue]
        translatedValue = mirValue.accept(self)
        self.translatedValueDictionary[mirValue] = translatedValue
        return translatedValue
    
    def visitGlobalVariable(self, mirGlobalVariable: MIRGlobalVariable):
        ## TODO: Implement this part.
        return None
    
    def visitFunction(self, mirFunction: MIRFunction) -> SDVMFunction:
        return self.translateFunction(mirFunction)

    def visitImportedModule(self, value: MIRImportedModule):
        return self.module.importModule(value.name)

    def visitImportedModuleValue(self, value: MIRImportedModuleValue):
        importdModule = self.translateValue(value.importedModule)
        ## TODO: Pass the string encoded type descriptor.
        return importdModule.importValue(value.valueName, '')

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
        argumentInstruction = self.function.addArgumentInstruction(SDVMInstruction(self.moduleFrontend.argumentInstructionDictionary[mirArgument.type]))
        self.translatedValueDictionary[mirArgument] = argumentInstruction
        return argumentInstruction

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

    def visitImportedModule(self, value: MIRImportedModule):
        assert False

    def visitImportedModuleValue(self, value: MIRImportedModuleValue):
        moduleImportedValue = self.moduleFrontend.translateValue(value)
        importInstruction = self.moduleFrontend.constantImportInstructionDictionary[value.getType()]
        return self.function.addConstant(SDVMConstant(importInstruction, moduleImportedValue, moduleImportedValue.index))
    
    def visitConstantInteger(self, instruction: MIRConstantInteger) -> SDVMOperand:
        return self.moduleFrontend.constantTranslationFunctions[instruction.getType()](self.function, instruction.value)

    def visitNullaryPrimitiveInstruction(self, instruction: MIRNullaryPrimitiveInstruction) -> SDVMOperand:
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef))

    def visitUnaryPrimitiveInstruction(self, instruction: MIRUnaryPrimitiveInstruction) -> SDVMOperand:
        operand = self.translateValue(instruction.operand)
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef, operand))

    def visitBinaryPrimitiveInstruction(self, instruction: MIRBinaryPrimitiveInstruction) -> SDVMOperand:
        left = self.translateValue(instruction.left)
        right = self.translateValue(instruction.right)
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef, left, right))

    def visitCallInstruction(self, instruction: MIRCallInstruction) -> SDVMOperand:
        calledFunctional = self.translateValue(instruction.functional)
        translatedArguments = list(map(self.translateValue, instruction.arguments))
        self.function.addInstruction(SDVMInstruction(SdvmOpBeginCall, len(instruction.arguments)))
        
        for i in range(len(translatedArguments)):
            translatedArgument = translatedArguments[i]
            argument = instruction.arguments[i]
            callArgumentInstruction = self.moduleFrontend.callArgumentInstructionDictionary[argument.getType()]
            self.function.addInstruction(SDVMInstruction(callArgumentInstruction, translatedArgument))

        if instruction.functional.getType().isClosureType():
            callInstruction = self.moduleFrontend.callClosureInstructionDictionary[instruction.getType()]
        else:
            callInstruction = self.moduleFrontend.callInstructionDictionary[instruction.getType()]
        return self.function.addInstruction(SDVMInstruction(callInstruction, calledFunctional))

    def visitReturnInstruction(self, instruction: MIRReturnInstruction) -> SDVMOperand:
        result = self.translateValue(instruction.result)
        return self.function.addInstruction(SDVMInstruction(self.moduleFrontend.returnInstructionDictionary[instruction.result.type], result))
