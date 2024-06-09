from .mop import *
from .asg import *
from .module import *
from .target import *
from .environment import *
from .gcm import *
from .sdvmInstructions import *
from .sdvmModule import *

class SDVMModuleFrontEnd(ASGDynamicProgrammingAlgorithm):
    def __init__(self, target: CompilationTarget) -> None:
        super().__init__()
        self.target = target
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
        self.environment: ASGTopLevelTargetEnvironment = None
        self.setupTranslationTables()

    def setupTranslationTables(self):
        self.environment = ASGTopLevelTargetEnvironment.getForTarget(self.target)
        for typeName, constantTranslationFunction, loadInstruction, storeInstruction, loadGCInstruction, storeGCInstruction, argumentInst, callArgumentInst, callInst, callClosureInst, returnInst in [
            ('MIR::Void',      None,                       None,                  None,                   None,                     None,                      None,                 None,                     SdvmInstCallVoid,      SdvmInstCallClosureVoid,      SdvmInstReturnVoid),
            ('MIR::Boolean',   SDVMFunction.constBoolean,  SdvmInstLoadBoolean,   SdvmInstStoreBoolean,   SdvmInstLoadGC_Boolean,   SdvmInstStoreGC_Boolean,   SdvmInstArgBoolean,   SdvmInstCallArgBoolean,   SdvmInstCallBoolean,   SdvmInstCallClosureBoolean,   SdvmInstReturnBoolean),
            ('MIR::Int8',      SDVMFunction.constInt8,     SdvmInstLoadInt8,      SdvmInstStoreInt8,      SdvmInstLoadGC_Int8,      SdvmInstStoreGC_Int8,      SdvmInstArgInt8,      SdvmInstCallArgInt8,      SdvmInstCallInt8,      SdvmInstCallClosureInt8,      SdvmInstReturnInt8),
            ('MIR::Int16',     SDVMFunction.constInt16,    SdvmInstLoadInt16,     SdvmInstStoreInt16,     SdvmInstLoadGC_Int16,     SdvmInstStoreGC_Int16,     SdvmInstArgInt16,     SdvmInstCallArgInt16,     SdvmInstCallInt16,     SdvmInstCallClosureInt16,     SdvmInstReturnInt16),
            ('MIR::Int32',     SDVMFunction.constInt32,    SdvmInstLoadInt32,     SdvmInstStoreInt32,     SdvmInstLoadGC_Int32,     SdvmInstStoreGC_Int32,     SdvmInstArgInt32,     SdvmInstCallArgInt32,     SdvmInstCallInt32,     SdvmInstCallClosureInt32,     SdvmInstReturnInt32),
            ('MIR::Int64',     SDVMFunction.constInt64,    SdvmInstLoadInt64,     SdvmInstStoreInt64,     SdvmInstLoadGC_Int64,     SdvmInstStoreGC_Int64,     SdvmInstArgInt64,     SdvmInstCallArgInt64,     SdvmInstCallInt64,     SdvmInstCallClosureInt64,     SdvmInstReturnInt64),
            ('MIR::UInt8',     SDVMFunction.constUInt8,    SdvmInstLoadUInt8,     SdvmInstStoreUInt8,     SdvmInstLoadGC_UInt8,     SdvmInstStoreGC_UInt8,     SdvmInstArgUInt8,     SdvmInstCallArgUInt8,     SdvmInstCallUInt8,     SdvmInstCallClosureUInt8,     SdvmInstReturnUInt8),
            ('MIR::UInt16',    SDVMFunction.constUInt16,   SdvmInstLoadUInt16,    SdvmInstStoreUInt16,    SdvmInstLoadGC_UInt16,    SdvmInstStoreGC_UInt16,    SdvmInstArgUInt16,    SdvmInstCallArgUInt16,    SdvmInstCallUInt16,    SdvmInstCallClosureUInt16,    SdvmInstReturnUInt16),
            ('MIR::UInt32',    SDVMFunction.constUInt32,   SdvmInstLoadUInt32,    SdvmInstStoreUInt32,    SdvmInstLoadGC_UInt32,    SdvmInstStoreGC_UInt32,    SdvmInstArgUInt32,    SdvmInstCallArgUInt32,    SdvmInstCallUInt32,    SdvmInstCallClosureUInt32,    SdvmInstReturnUInt32),
            ('MIR::UInt64',    SDVMFunction.constUInt64,   SdvmInstLoadUInt64,    SdvmInstStoreUInt64,    SdvmInstLoadGC_UInt64,    SdvmInstStoreGC_UInt64,    SdvmInstArgUInt64,    SdvmInstCallArgUInt64,    SdvmInstCallUInt64,    SdvmInstCallClosureUInt64,    SdvmInstReturnUInt64),
            ('MIR::Float32',   SDVMFunction.constFloat32,  SdvmInstLoadFloat32,   SdvmInstStoreFloat32,   SdvmInstLoadGC_Float32,   SdvmInstStoreGC_Float32,   SdvmInstArgFloat32,   SdvmInstCallArgFloat32,   SdvmInstCallFloat32,   SdvmInstCallClosureFloat32,   SdvmInstReturnFloat32),
            ('MIR::Float64',   SDVMFunction.constFloat64,  SdvmInstLoadFloat64,   SdvmInstStoreFloat64,   SdvmInstLoadGC_Float64,   SdvmInstStoreGC_Float64,   SdvmInstArgFloat64,   SdvmInstCallArgFloat64,   SdvmInstCallFloat64,   SdvmInstCallClosureFloat64,   SdvmInstReturnFloat64),
        ]:
            type = self.environment.lookValidLastBindingOf(typeName)
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

    def compileModule(self, module: Module):
        for exportedValue in module.exportedValues:
            self.module.exportValue(exportedValue.name, self.translateTopLevelValue(exportedValue.mirValue), exportedValue.externalName, '')
        self.module.finishBuilding()
        return self.module

    def translateValue(self, value: ASGNode):
        return self(value)

    def translateTopLevelValue(self, value: ASGNode):
        return self(value)

    @asgPatternMatchingOnNodeKind(ASGMirFromExternalImportNode)
    def translateMirFromExternalImportNode(self, node: ASGMirFromExternalImportNode):
        ## TODO: Pass the string encoded type descriptor.
        return self.module.importExternalValue(node.externalName, node.importedName, '')
    
    @asgPatternMatchingOnNodeKind(ASGMirLambdaNode)
    def translateMirLambdaNode(self, node: ASGMirLambdaNode):
        # TODO: Add support for lambdas with captures
        assert len(node.captures) == 0
        return self.fromNodeContinueExpanding(node, node.functionDefinition)
    
    @asgRecursivePatternMatchingOnNodeKind(ASGMirFunctionDefinitionNode)
    def translateMirFunctionDefinitionNode(self, expansionResult: ASGDynamicProgrammingAlgorithmNodeExpansionResult, node: ASGMirFunctionDefinitionNode):
        function = self.module.newFunction(node.name, sourcePosition = node.sourceDerivation.getSourcePosition())
        expansionResult.finishWithValue(function)
        SDVMFunctionFrontEnd(self).translateMirFunctionInto(node, function)
        return function
        
class SDVMFunctionFrontEnd(ASGDynamicProgrammingAlgorithm):
    def __init__(self, moduleFrontend: SDVMModuleFrontEnd) -> None:
        super().__init__()

        self.moduleFrontend = moduleFrontend
        self.environment = self.moduleFrontend.environment
        self.function: SDVMFunction = None

    def translateMirFunctionInto(self, mirFunction: ASGMirFunctionDefinitionNode, function: SDVMFunction):
        self.function = function
        scheduledMirFunction = mirFunctionDefinitionGCM(mirFunction)

        # Translate the arguments.
        self.function.beginArguments(len(mirFunction.arguments))
        for argument in mirFunction.arguments:
            self.translateValue(argument)

        # Declare the labels and the phi nodes
        for instruction in scheduledMirFunction.serializedInstructions:
            if instruction.isBasicBlockStart():
                basicBlockLabel = SDVMInstruction(SdvmConstLabel, sourcePosition = instruction.sourceDerivation.getSourcePosition())
                self.setValueForNodeExpansion(instruction, basicBlockLabel)
            elif instruction.isPhiNode(): 
                assert False

        # Generate the instructions.
        for instruction in scheduledMirFunction.serializedInstructions:
            instructionValue = self(instruction)
            if instruction.isBasicBlockStart() or instruction.isPhiNode():
                self.function.addInstruction(instructionValue)

    def translateValue(self, value):
        return self(value)

    @asgPatternMatchingOnNodeKind(ASGArgumentNode)
    def translateMirArgument(self, node: ASGArgumentNode):
        self.function.addArgumentInstruction(SDVMInstruction(node.type.getSDVMArgumentInstructionWith(self.moduleFrontend)))

    def translateApplicationWithArguments(self, resultType: ASGNode, functional: ASGNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
        if functional.isLiteralPrimitiveFunction():
            return self.translatePrimitiveApplicationWithArguments(self, resultType, functional, arguments, sourcePosition)
            
        calledFunctional = self(functional)
        translatedArguments = list(map(self.translateValue, arguments))

        functionType = functional.type.asFunctionType()
        isClosure = functional.type.isMirClosureType()
        argumentsDescriptor = functionType.getFixedArgumentCount() & SdvmBeginCallFixedArgumentMask
        if functionType.isVariadic:
            argumentsDescriptor |= SdvmBeginCallVariadicFlag

        self.function.addInstruction(SDVMInstruction(SdvmInstBeginCall, argumentsDescriptor, sourcePosition = sourcePosition))
        
        for i in range(len(translatedArguments)):
            translatedArgument = translatedArguments[i]
            argument = arguments[i]
            callArgumentInstruction = argument.getTypeInEnvironment(self.moduleFrontend.environment).getSDVMCallArgumentInstructionWith(self.moduleFrontend)
            self.function.addInstruction(SDVMInstruction(callArgumentInstruction, translatedArgument, sourcePosition = sourcePosition))

        if isClosure:
            callInstruction = resultType.getSDVMCallClosureInstructionWith(self.moduleFrontend)
        else:
            callInstruction = resultType.getSDVMCallInstructionWith(self.moduleFrontend)
        return self.function.addInstruction(SDVMInstruction(callInstruction, calledFunctional, sourcePosition = sourcePosition))

    def translateImportedValue(self, node):
        moduleImportedValue = self.moduleFrontend.translateValue(node)
        if node.type.isMirFunctionType():
            return self.function.addConstant(SDVMConstant(SdvmConstImportProcedureHandle, moduleImportedValue, moduleImportedValue.index))
        return self.function.addConstant(SDVMConstant(SdvmConstImportPointer, moduleImportedValue, moduleImportedValue.index))

    @asgPatternMatchingOnNodeKind(ASGLiteralStringDataNode)
    def translateLiteralStringData(self, node: ASGLiteralStringDataNode):
        if node.nullTerminated:
            return self.function.constCString(node.value.encode('utf-8'))
        else:
            return self.function.constString(node.value.encode('utf-8'))

    @asgPatternMatchingOnNodeKind(ASGLiteralIntegerNode)
    def translateLiteralIntegerNode(self, node: ASGLiteralIntegerNode):
        return self.moduleFrontend.constantTranslationFunctions[node.type](self.function, node.value)

    @asgPatternMatchingOnNodeKind(ASGLiteralIntegerNode)
    def translateLiteralFloatNode(self, node: ASGLiteralFloatNode):
        return self.moduleFrontend.constantTranslationFunctions[node.type](self.function, node.value)

    @asgPatternMatchingOnNodeKind(ASGMirFromExternalImportNode)
    def translateMirFromExternalImportNode(self, node: ASGMirFromExternalImportNode):
        return self.translateImportedValue(node)
    
    @asgPatternMatchingOnNodeKind(ASGApplicationNode)
    def translateMirApplication(self, node: ASGApplicationNode):
        return self.translateApplicationWithArguments(node.type, node.functional, node.arguments, node.sourceDerivation.getSourcePosition())

    @asgPatternMatchingOnNodeKind(ASGFxApplicationNode)
    def translateMirFxApplication(self, node: ASGFxApplicationNode):
        return self.translateApplicationWithArguments(node.type, node.functional, node.arguments, node.sourceDerivation.getSourcePosition())

    @asgPatternMatchingOnNodeKind(ASGSequenceReturnNode)
    def translateSequenceReturn(self, node: ASGSequenceReturnNode):
        result = self.translateValue(node.value)
        returnInstruction = node.value.type.getSDVMReturnInstructionWith(self.moduleFrontend)
        return self.function.addInstruction(SDVMInstruction(returnInstruction, result, sourcePosition = node.sourceDerivation.sourcePosition))