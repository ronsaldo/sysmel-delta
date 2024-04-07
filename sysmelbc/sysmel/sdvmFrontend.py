from .mir import *
from .sdvmInstructions import *
from .sdvmModule import *

class SDVMModuleFrontEnd:
    def __init__(self) -> None:
        self.module = SDVMModule()
        self.translatedFunctionDictionary = dict()
        self.translatedValueDictionary = dict()
        self.constantTranslationFunctions = dict()
        self.loadInstructionDictionary = dict()
        self.loadGCInstructionDictionary = dict()
        self.storeInstructionDictionary = dict()
        self.storeGCInstructionDictionary = dict()
        self.argumentInstructionDictionary = dict()
        self.callArgumentInstructionDictionary = dict()
        self.callInstructionDictionary = dict()
        self.callClosureInstructionDictionary = dict()
        self.returnInstructionDictionary = dict()

    def compileMIRModule(self, mirModule: MIRModule) -> SDVMModule:
        mirContext = mirModule.context
        self.module.setName(mirModule.name)

        for type, constantTranslationFunction, loadInstruction, storeInstruction, loadGCInstruction, storeGCInstruction, argumentInst, callArgumentInst, callInst, callClosureInst, returnInst in [
            (mirContext.voidType,      None,                       None,                  None,                   None,                     None,                      None,                 None,                     SdvmInstCallVoid,      SdvmInstCallClosureVoid,      SdvmInstReturnVoid),
            (mirContext.booleanType,   SDVMFunction.constBoolean,  SdvmInstLoadBoolean,   SdvmInstStoreBoolean,   SdvmInstLoadGC_Boolean,   SdvmInstStoreGC_Boolean,   SdvmInstArgBoolean,   SdvmInstCallArgBoolean,   SdvmInstCallBoolean,   SdvmInstCallClosureBoolean,   SdvmInstReturnBoolean),
            (mirContext.int8Type,      SDVMFunction.constInt8,     SdvmInstLoadInt8,      SdvmInstStoreInt8,      SdvmInstLoadGC_Int8,      SdvmInstStoreGC_Int8,      SdvmInstArgInt8,      SdvmInstCallArgInt8,      SdvmInstCallInt8,      SdvmInstCallClosureInt8,      SdvmInstReturnInt8),
            (mirContext.int16Type,     SDVMFunction.constInt16,    SdvmInstLoadInt16,     SdvmInstStoreInt16,     SdvmInstLoadGC_Int16,     SdvmInstStoreGC_Int16,     SdvmInstArgInt16,     SdvmInstCallArgInt16,     SdvmInstCallInt16,     SdvmInstCallClosureInt16,     SdvmInstReturnInt16),
            (mirContext.int32Type,     SDVMFunction.constInt32,    SdvmInstLoadInt32,     SdvmInstStoreInt32,     SdvmInstLoadGC_Int32,     SdvmInstStoreGC_Int32,     SdvmInstArgInt32,     SdvmInstCallArgInt32,     SdvmInstCallInt32,     SdvmInstCallClosureInt32,     SdvmInstReturnInt32),
            (mirContext.int64Type,     SDVMFunction.constInt64,    SdvmInstLoadInt64,     SdvmInstStoreInt64,     SdvmInstLoadGC_Int64,     SdvmInstStoreGC_Int64,     SdvmInstArgInt64,     SdvmInstCallArgInt64,     SdvmInstCallInt64,     SdvmInstCallClosureInt64,     SdvmInstReturnInt64),
            (mirContext.uint8Type,     SDVMFunction.constUInt8,    SdvmInstLoadUInt8,     SdvmInstStoreUInt8,     SdvmInstLoadGC_UInt8,     SdvmInstStoreGC_UInt8,     SdvmInstArgUInt8,     SdvmInstCallArgUInt8,     SdvmInstCallUInt8,     SdvmInstCallClosureUInt8,     SdvmInstReturnUInt8),
            (mirContext.uint16Type,    SDVMFunction.constUInt16,   SdvmInstLoadUInt16,    SdvmInstStoreUInt16,    SdvmInstLoadGC_UInt16,    SdvmInstStoreGC_UInt16,    SdvmInstArgUInt16,    SdvmInstCallArgUInt16,    SdvmInstCallUInt16,    SdvmInstCallClosureUInt16,    SdvmInstReturnUInt16),
            (mirContext.uint32Type,    SDVMFunction.constUInt32,   SdvmInstLoadUInt32,    SdvmInstStoreUInt32,    SdvmInstLoadGC_UInt32,    SdvmInstStoreGC_UInt32,    SdvmInstArgUInt32,    SdvmInstCallArgUInt32,    SdvmInstCallUInt32,    SdvmInstCallClosureUInt32,    SdvmInstReturnUInt32),
            (mirContext.uint64Type,    SDVMFunction.constUInt64,   SdvmInstLoadUInt64,    SdvmInstStoreUInt64,    SdvmInstLoadGC_UInt64,    SdvmInstStoreGC_UInt64,    SdvmInstArgUInt64,    SdvmInstCallArgUInt64,    SdvmInstCallUInt64,    SdvmInstCallClosureUInt64,    SdvmInstReturnUInt64),
            (mirContext.float32Type,   SDVMFunction.constFloat32,  SdvmInstLoadFloat32,   SdvmInstStoreFloat32,   SdvmInstLoadGC_Float32,   SdvmInstStoreGC_Float32,   SdvmInstArgFloat32,   SdvmInstCallArgFloat32,   SdvmInstCallFloat32,   SdvmInstCallClosureFloat32,   SdvmInstReturnFloat32),
            (mirContext.float64Type,   SDVMFunction.constFloat64,  SdvmInstLoadFloat64,   SdvmInstStoreFloat64,   SdvmInstLoadGC_Float64,   SdvmInstStoreGC_Float64,   SdvmInstArgFloat64,   SdvmInstCallArgFloat64,   SdvmInstCallFloat64,   SdvmInstCallClosureFloat64,   SdvmInstReturnFloat64),
            (mirContext.pointerType,   None,                       SdvmInstLoadPointer,   SdvmInstStorePointer,   SdvmInstLoadGC_Pointer,   SdvmInstStoreGC_Pointer,   SdvmInstArgPointer,   SdvmInstCallArgPointer,   SdvmInstCallPointer,   SdvmInstCallClosurePointer,   SdvmInstReturnPointer),
            (mirContext.gcPointerType, None,                       SdvmInstLoadGCPointer, SdvmInstStoreGCPointer, SdvmInstLoadGC_GCPointer, SdvmInstStoreGC_GCPointer, SdvmInstArgGCPointer, SdvmInstCallArgGCPointer, SdvmInstCallGCPointer, SdvmInstCallClosureGCPointer, SdvmInstReturnGCPointer),
            (mirContext.closureType,   None,                       SdvmInstLoadGCPointer, SdvmInstStoreGCPointer, SdvmInstLoadGC_GCPointer, SdvmInstStoreGC_GCPointer, SdvmInstArgGCPointer, SdvmInstCallArgGCPointer, SdvmInstCallGCPointer, SdvmInstCallClosureGCPointer, SdvmInstReturnGCPointer),

            (mirContext.float32x2Type, SDVMFunction.constFloat32x2, SdvmInstLoadFloat32x2, SdvmInstStoreFloat32x2, SdvmInstLoadGC_Float32x2, SdvmInstStoreGC_Float32x2, SdvmInstArgFloat32x2, SdvmInstCallArgFloat32x2, SdvmInstCallFloat32x2, SdvmInstCallClosureFloat32x2, SdvmInstReturnFloat32x2),
            (mirContext.float32x3Type, SDVMFunction.constFloat32x3, SdvmInstLoadFloat32x4, SdvmInstStoreFloat32x4, SdvmInstLoadGC_Float32x4, SdvmInstStoreGC_Float32x4, SdvmInstArgFloat32x4, SdvmInstCallArgFloat32x4, SdvmInstCallFloat32x4, SdvmInstCallClosureFloat32x4, SdvmInstReturnFloat32x4),
            (mirContext.float32x4Type, SDVMFunction.constFloat32x4, SdvmInstLoadFloat32x4, SdvmInstStoreFloat32x4, SdvmInstLoadGC_Float32x4, SdvmInstStoreGC_Float32x4, SdvmInstArgFloat32x4, SdvmInstCallArgFloat32x4, SdvmInstCallFloat32x4, SdvmInstCallClosureFloat32x4, SdvmInstReturnFloat32x4),
            (mirContext.float64x2Type, SDVMFunction.constFloat64x2, SdvmInstLoadFloat64x2, SdvmInstStoreFloat64x2, SdvmInstLoadGC_Float64x2, SdvmInstStoreGC_Float64x2, SdvmInstArgFloat64x2, SdvmInstCallArgFloat64x2, SdvmInstCallFloat64x2, SdvmInstCallClosureFloat64x2, SdvmInstReturnFloat64x2),
            (mirContext.float64x3Type, SDVMFunction.constFloat64x3, SdvmInstLoadFloat64x4, SdvmInstStoreFloat64x4, SdvmInstLoadGC_Float64x4, SdvmInstStoreGC_Float64x4, SdvmInstArgFloat64x4, SdvmInstCallArgFloat64x4, SdvmInstCallFloat64x4, SdvmInstCallClosureFloat64x4, SdvmInstReturnFloat64x4),
            (mirContext.float64x4Type, SDVMFunction.constFloat64x4, SdvmInstLoadFloat64x4, SdvmInstStoreFloat64x4, SdvmInstLoadGC_Float64x4, SdvmInstStoreGC_Float64x4, SdvmInstArgFloat64x4, SdvmInstCallArgFloat64x4, SdvmInstCallFloat64x4, SdvmInstCallClosureFloat64x4, SdvmInstReturnFloat64x4),
            (mirContext.int32x2Type,   SDVMFunction.constInt32x2,   SdvmInstLoadInt32x2,   SdvmInstStoreInt32x2,   SdvmInstLoadGC_Int32x2,   SdvmInstStoreGC_Int32x2,   SdvmInstArgInt32x2,   SdvmInstCallArgInt32x2,   SdvmInstCallInt32x2,   SdvmInstCallClosureInt32x2,   SdvmInstReturnInt32x2),
            (mirContext.int32x3Type,   SDVMFunction.constInt32x3,   SdvmInstLoadInt32x4,   SdvmInstStoreInt32x4,   SdvmInstLoadGC_Int32x4,   SdvmInstStoreGC_Int32x4,   SdvmInstArgInt32x4,   SdvmInstCallArgInt32x4,   SdvmInstCallInt32x4,   SdvmInstCallClosureInt32x4,   SdvmInstReturnInt32x4),
            (mirContext.int32x4Type,   SDVMFunction.constInt32x4,   SdvmInstLoadInt32x4,   SdvmInstStoreInt32x4,   SdvmInstLoadGC_Int32x4,   SdvmInstStoreGC_Int32x4,   SdvmInstArgInt32x4,   SdvmInstCallArgInt32x4,   SdvmInstCallInt32x4,   SdvmInstCallClosureInt32x4,   SdvmInstReturnInt32x4),
            (mirContext.uint32x2Type,  SDVMFunction.constUInt32x2,  SdvmInstLoadUInt32x2,  SdvmInstStoreUInt32x2,  SdvmInstLoadGC_UInt32x2,  SdvmInstStoreGC_UInt32x2,  SdvmInstArgUInt32x2,  SdvmInstCallArgUInt32x2,  SdvmInstCallUInt32x2,  SdvmInstCallClosureUInt32x2,  SdvmInstReturnUInt32x2),
            (mirContext.uint32x3Type,  SDVMFunction.constUInt32x3,  SdvmInstLoadUInt32x4,  SdvmInstStoreUInt32x4,  SdvmInstLoadGC_UInt32x4,  SdvmInstStoreGC_UInt32x4,  SdvmInstArgUInt32x4,  SdvmInstCallArgUInt32x4,  SdvmInstCallUInt32x4,  SdvmInstCallClosureUInt32x4,  SdvmInstReturnUInt32x4),
            (mirContext.uint32x4Type,  SDVMFunction.constUInt32x4,  SdvmInstLoadUInt32x4,  SdvmInstStoreUInt32x4,  SdvmInstLoadGC_UInt32x4,  SdvmInstStoreGC_UInt32x4,  SdvmInstArgUInt32x4,  SdvmInstCallArgUInt32x4,  SdvmInstCallUInt32x4,  SdvmInstCallClosureUInt32x4,  SdvmInstReturnUInt32x4),
        ]:
            self.constantTranslationFunctions[type] = constantTranslationFunction
            self.loadInstructionDictionary[type] = loadInstruction
            self.loadGCInstructionDictionary[type] = loadGCInstruction
            self.storeInstructionDictionary[type] = storeInstruction
            self.storeGCInstructionDictionary[type] = storeGCInstruction
            self.argumentInstructionDictionary[type] = argumentInst
            self.callArgumentInstructionDictionary[type] = callArgumentInst
            self.callInstructionDictionary[type] = callInst
            self.callClosureInstructionDictionary[type] = callClosureInst
            self.returnInstructionDictionary[type] = returnInst

        for globalValue in mirModule.globalValues:
            self.translateValue(globalValue)

        for name, value, externalName in mirModule.exportedValues:
            self.module.exportValue(name, self.translateValue(value), externalName, '')
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
        importedModule = self.translateValue(value.importedModule)
        ## TODO: Pass the string encoded type descriptor.
        return importedModule.importValue(value.valueName, '')

    def visitImportedExternalValue(self, value: MIRImportedExternalValue):
        ## TODO: Pass the string encoded type descriptor.
        return self.module.importExternalValue(value.externalName, value.valueName, '')

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
        basicBlocks = list(mirFunction.reachableBasicBlocksInReversePostOrder())
        for basicBlock in basicBlocks:
            basicBlockLabel = SDVMInstruction(SdvmConstLabel)
            self.translatedValueDictionary[basicBlock] = basicBlockLabel

        for i in range(len(basicBlocks)):
            basicBlock = basicBlocks[i]
            nextBasicBlock = None
            if i + 1 < len(basicBlocks):
                nextBasicBlock = basicBlocks[i + 1]
            self.translateBasicBlock(basicBlock, nextBasicBlock)

    def translateBasicBlock(self, basicBlock: MIRBasicBlock, nextBasicBlock: MIRBasicBlock) -> SDVMOperand:
        self.currentBasicBlock = basicBlock
        self.nextBasicBlock = nextBasicBlock
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

    def visitImportedValue(self, value: MIRImportedValue):
        moduleImportedValue = self.moduleFrontend.translateValue(value)
        if value.getType().isFunctionType():
            return self.function.addConstant(SDVMConstant(SdvmConstImportProcedureHandle, moduleImportedValue, moduleImportedValue.index))
        return self.function.addConstant(SDVMConstant(SdvmConstImportPointer, moduleImportedValue, moduleImportedValue.index))

    def visitImportedModuleValue(self, value: MIRImportedModuleValue):
        return self.visitImportedValue(value)
    
    def visitImportedExternalValue(self, value: MIRImportedExternalValue):
        return self.visitImportedValue(value)
    
    def visitConstantInteger(self, constant: MIRConstantInteger) -> SDVMOperand:
        return self.moduleFrontend.constantTranslationFunctions[constant.getType()](self.function, constant.value)
    
    def visitConstantStringData(self, constant: MIRConstantStringData) -> SDVMOperand:
        if constant.nullTerminated:
            return self.function.constCString(constant.value)
        else:
            return self.function.constString(constant.value)
        
    def visitFunction(self, function: MIRFunction):
        sdvmFunction = self.moduleFrontend.translateValue(function)
        return self.function.constLocalProcedure(sdvmFunction)

    def visitNullaryPrimitiveInstruction(self, instruction: MIRNullaryPrimitiveInstruction) -> SDVMOperand:
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef))

    def visitUnaryPrimitiveInstruction(self, instruction: MIRUnaryPrimitiveInstruction) -> SDVMOperand:
        operand = self.translateValue(instruction.operand)
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef, operand))

    def visitBinaryPrimitiveInstruction(self, instruction: MIRBinaryPrimitiveInstruction) -> SDVMOperand:
        left = self.translateValue(instruction.left)
        right = self.translateValue(instruction.right)
        return self.function.addInstruction(SDVMInstruction(instruction.instructionDef, left, right))
    
    def visitAllocaInstruction(self, instruction: MIRAllocaInstruction) -> SDVMOperand:
        if instruction.isGCPointer():
            if instruction.hasNoEscape:
                allocaInstruction = SdvmInstAllocateGCNoEscape
            else:
                allocaInstruction = SdvmInstAllocateGC
        else:
            allocaInstruction = SdvmInstAllocateLocal

        memoryDescriptor = self.moduleFrontend.module.addMemoryDescriptor(instruction.memoryDescriptor)
        return self.function.addInstruction(SDVMInstruction(allocaInstruction, memoryDescriptor))

    def visitLoadInstruction(self, instruction: MIRLoadInstruction) -> SDVMOperand:
        pointer = self.translateValue(instruction.pointer)
        if instruction.pointer.isGCPointer():
            loadInstruction = self.moduleFrontend.loadGCInstructionDictionary[instruction.getType()]
        else:
            loadInstruction = self.moduleFrontend.loadInstructionDictionary[instruction.getType()]
        return self.function.addInstruction(SDVMInstruction(loadInstruction, pointer))

    def visitStoreInstruction(self, instruction: MIRStoreInstruction) -> SDVMOperand:
        pointer = self.translateValue(instruction.pointer)
        value = self.translateValue(instruction.value)
        if instruction.pointer.isGCPointer():
            storeInstruction = self.moduleFrontend.storeGCInstructionDictionary[instruction.value.getType()]
        else:
            storeInstruction = self.moduleFrontend.storeInstructionDictionary[instruction.value.getType()]
        return self.function.addInstruction(SDVMInstruction(storeInstruction, pointer, value))

    def visitCallInstruction(self, instruction: MIRCallInstruction) -> SDVMOperand:
        calledFunctional = self.translateValue(instruction.functional)
        translatedArguments = list(map(self.translateValue, instruction.arguments))
        self.function.addInstruction(SDVMInstruction(SdvmInstBeginCall, len(instruction.arguments)))
        
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

    def visitBranchInstruction(self, instruction: MIRBranchInstruction) -> SDVMOperand:
        if instruction.destination is self.nextBasicBlock:
            return None

        destination = self.translateValue(instruction.destination)
        self.function.inst(SdvmInstJump, destination)
        return None

    def visitCondBranchInstruction(self, instruction: MIRCondBranchInstruction) -> SDVMOperand:
        condition = self.translateValue(instruction.condition)
        trueDestination = self.translateValue(instruction.trueDestination)
        falseDestination = self.translateValue(instruction.falseDestination)

        if instruction.trueDestination is self.nextBasicBlock:
            self.function.inst(SdvmInstJumpIfFalse, condition, falseDestination)
        elif instruction.falseDestination is self.nextBasicBlock:
            self.function.inst(SdvmInstJumpIfTrue, condition, trueDestination)
        else:
            self.function.inst(SdvmInstJumpIfTrue, condition, trueDestination)
            self.function.inst(SdvmInstJump, falseDestination)
        return None

    def visitReturnInstruction(self, instruction: MIRReturnInstruction) -> SDVMOperand:
        result = self.translateValue(instruction.result)
        return self.function.addInstruction(SDVMInstruction(self.moduleFrontend.returnInstructionDictionary[instruction.result.type], result))
