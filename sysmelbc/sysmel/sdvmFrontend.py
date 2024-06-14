from .mop import *
from .asg import *
from .module import *
from .target import *
from .environment import *
from .gcm import *
from .sdvmInstructions import *
from .sdvmModule import *

def yourselfTranslator(functionTranslator, resultType: ASGNode, functional: ASGLiteralPrimitiveFunctionNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
    assert len(arguments) == 1
    return functionTranslator.translateValue(arguments[0])

def sdvmUnaryPrimitiveFor(sdvmInstructionDef: SdvmInstructionDef):
    def translate(functionTranslator: SDVMFunctionFrontEnd, resultType: ASGNode, functional: ASGLiteralPrimitiveFunctionNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
        assert len(arguments) == 1
        operand = functionTranslator.translateValue(arguments[0])
        return functionTranslator.function.addInstruction(SDVMInstruction(sdvmInstructionDef, operand, sourcePosition = sourcePosition))
    return translate

def sdvmBinaryPrimitiveFor(sdvmInstructionDef: SdvmInstructionDef):
    def translate(functionTranslator: SDVMFunctionFrontEnd, resultType: ASGNode, functional: ASGLiteralPrimitiveFunctionNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
        assert len(arguments) == 2
        left = functionTranslator.translateValue(arguments[0])
        right = functionTranslator.translateValue(arguments[0])
        return functionTranslator.function.addInstruction(SDVMInstruction(sdvmInstructionDef, left, right, sourcePosition = sourcePosition))
    return translate

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
        self.sdvmPrimitiveFunctionTranslationTable = dict()
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

        for primitiveDef in [
            ('Int8::+',    sdvmBinaryPrimitiveFor(SdvmInstInt8Add)),
            ('Int8::-',    sdvmBinaryPrimitiveFor(SdvmInstInt8Sub)),
            ('Int8::*',    sdvmBinaryPrimitiveFor(SdvmInstInt8Mul)),
            ('Int8:://',   sdvmBinaryPrimitiveFor(SdvmInstInt8Div)),
            ('Int8::%',    sdvmBinaryPrimitiveFor(SdvmInstInt8Rem)),
            ('Int8::&',    sdvmBinaryPrimitiveFor(SdvmInstInt8And)),
            ('Int8::|',    sdvmBinaryPrimitiveFor(SdvmInstInt8Or)),
            ('Int8::^',    sdvmBinaryPrimitiveFor(SdvmInstInt8Xor)),
            ('Int8::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt8Lsl)),
            ('Int8::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt8Asr)),
            ('Int8::=',    sdvmBinaryPrimitiveFor(SdvmInstInt8Equals)),
            ('Int8::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt8NotEquals)),
            ('Int8::<',    sdvmBinaryPrimitiveFor(SdvmInstInt8LessThan)),
            ('Int8::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt8LessOrEquals)),
            ('Int8::>',    sdvmBinaryPrimitiveFor(SdvmInstInt8GreaterThan)),
            ('Int8::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt8GreaterOrEquals)),
            ('Int8::min:', sdvmBinaryPrimitiveFor(SdvmInstInt8Min)),
            ('Int8::max:', sdvmBinaryPrimitiveFor(SdvmInstInt8Max)),

            ('UInt8::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Add)),
            ('UInt8::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Sub)),
            ('UInt8::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Mul)),
            ('UInt8:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt8UDiv)),
            ('UInt8::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt8URem)),
            ('UInt8::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt8And)),
            ('UInt8::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Or)),
            ('UInt8::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Xor)),
            ('UInt8::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsl)),
            ('UInt8::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsr)),
            ('UInt8::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Equals)),
            ('UInt8::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8NotEquals)),
            ('UInt8::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt8LessThan)),
            ('UInt8::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8LessOrEquals)),
            ('UInt8::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterThan)),
            ('UInt8::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterOrEquals)),
            ('UInt8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Min)),
            ('UInt8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Max)),

            ('Char8::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Add)),
            ('Char8::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Sub)),
            ('Char8::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Mul)),
            ('Char8:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt8UDiv)),
            ('Char8::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt8URem)),
            ('Char8::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt8And)),
            ('Char8::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Or)),
            ('Char8::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Xor)),
            ('Char8::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsl)),
            ('Char8::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt8Lsr)),
            ('Char8::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt8Equals)),
            ('Char8::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8NotEquals)),
            ('Char8::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt8LessThan)),
            ('Char8::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8LessOrEquals)),
            ('Char8::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterThan)),
            ('Char8::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt8GreaterOrEquals)),
            ('Char8::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Min)),
            ('Char8::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt8Max)),

            ('Int16::+',    sdvmBinaryPrimitiveFor(SdvmInstInt16Add)),
            ('Int16::-',    sdvmBinaryPrimitiveFor(SdvmInstInt16Sub)),
            ('Int16::*',    sdvmBinaryPrimitiveFor(SdvmInstInt16Mul)),
            ('Int16:://',   sdvmBinaryPrimitiveFor(SdvmInstInt16Div)),
            ('Int16::%',    sdvmBinaryPrimitiveFor(SdvmInstInt16Rem)),
            ('Int16::&',    sdvmBinaryPrimitiveFor(SdvmInstInt16And)),
            ('Int16::|',    sdvmBinaryPrimitiveFor(SdvmInstInt16Or)),
            ('Int16::^',    sdvmBinaryPrimitiveFor(SdvmInstInt16Xor)),
            ('Int16::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt16Lsl)),
            ('Int16::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt16Asr)),
            ('Int16::=',    sdvmBinaryPrimitiveFor(SdvmInstInt16Equals)),
            ('Int16::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt16NotEquals)),
            ('Int16::<',    sdvmBinaryPrimitiveFor(SdvmInstInt16LessThan)),
            ('Int16::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt16LessOrEquals)),
            ('Int16::>',    sdvmBinaryPrimitiveFor(SdvmInstInt16GreaterThan)),
            ('Int16::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt16GreaterOrEquals)),
            ('Int16::min:', sdvmBinaryPrimitiveFor(SdvmInstInt16Min)),
            ('Int16::max:', sdvmBinaryPrimitiveFor(SdvmInstInt16Max)),

            ('UInt16::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Add)),
            ('UInt16::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Sub)),
            ('UInt16::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Mul)),
            ('UInt16:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt16UDiv)),
            ('UInt16::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt16URem)),
            ('UInt16::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt16And)),
            ('UInt16::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Or)),
            ('UInt16::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Xor)),
            ('UInt16::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsl)),
            ('UInt16::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsr)),
            ('UInt16::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Equals)),
            ('UInt16::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16NotEquals)),
            ('UInt16::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt16LessThan)),
            ('UInt16::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16LessOrEquals)),
            ('UInt16::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterThan)),
            ('UInt16::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterOrEquals)),
            ('UInt16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Min)),
            ('UInt16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Max)),

            ('Char16::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Add)),
            ('Char16::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Sub)),
            ('Char16::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Mul)),
            ('Char16:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt16UDiv)),
            ('Char16::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt16URem)),
            ('Char16::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt16And)),
            ('Char16::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Or)),
            ('Char16::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Xor)),
            ('Char16::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsl)),
            ('Char16::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt16Lsr)),
            ('Char16::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt16Equals)),
            ('Char16::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16NotEquals)),
            ('Char16::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt16LessThan)),
            ('Char16::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16LessOrEquals)),
            ('Char16::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterThan)),
            ('Char16::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt16GreaterOrEquals)),
            ('Char16::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Min)),
            ('Char16::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt16Max)),

            ('Int32::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32Add)),
            ('Int32::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32Sub)),
            ('Int32::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32Mul)),
            ('Int32:://',   sdvmBinaryPrimitiveFor(SdvmInstInt32Div)),
            ('Int32::%',    sdvmBinaryPrimitiveFor(SdvmInstInt32Rem)),
            ('Int32::&',    sdvmBinaryPrimitiveFor(SdvmInstInt32And)),
            ('Int32::|',    sdvmBinaryPrimitiveFor(SdvmInstInt32Or)),
            ('Int32::^',    sdvmBinaryPrimitiveFor(SdvmInstInt32Xor)),
            ('Int32::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt32Lsl)),
            ('Int32::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt32Asr)),
            ('Int32::=',    sdvmBinaryPrimitiveFor(SdvmInstInt32Equals)),
            ('Int32::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt32NotEquals)),
            ('Int32::<',    sdvmBinaryPrimitiveFor(SdvmInstInt32LessThan)),
            ('Int32::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt32LessOrEquals)),
            ('Int32::>',    sdvmBinaryPrimitiveFor(SdvmInstInt32GreaterThan)),
            ('Int32::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt32GreaterOrEquals)),
            ('Int32::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32Min)),
            ('Int32::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32Max)),

            ('UInt32::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Add)),
            ('UInt32::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Sub)),
            ('UInt32::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Mul)),
            ('UInt32:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt32UDiv)),
            ('UInt32::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt32URem)),
            ('UInt32::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt32And)),
            ('UInt32::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Or)),
            ('UInt32::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Xor)),
            ('UInt32::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsl)),
            ('UInt32::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsr)),
            ('UInt32::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Equals)),
            ('UInt32::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32NotEquals)),
            ('UInt32::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt32LessThan)),
            ('UInt32::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32LessOrEquals)),
            ('UInt32::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterThan)),
            ('UInt32::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterOrEquals)),
            ('UInt32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Min)),
            ('UInt32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Max)),

            ('Char32::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Add)),
            ('Char32::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Sub)),
            ('Char32::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Mul)),
            ('Char32:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt32UDiv)),
            ('Char32::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt32URem)),
            ('Char32::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt32And)),
            ('Char32::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Or)),
            ('Char32::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Xor)),
            ('Char32::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsl)),
            ('Char32::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt32Lsr)),
            ('Char32::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt32Equals)),
            ('Char32::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32NotEquals)),
            ('Char32::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt32LessThan)),
            ('Char32::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32LessOrEquals)),
            ('Char32::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterThan)),
            ('Char32::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt32GreaterOrEquals)),
            ('Char32::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Min)),
            ('Char32::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32Max)),

            ('Int64::+',    sdvmBinaryPrimitiveFor(SdvmInstInt64Add)),
            ('Int64::-',    sdvmBinaryPrimitiveFor(SdvmInstInt64Sub)),
            ('Int64::*',    sdvmBinaryPrimitiveFor(SdvmInstInt64Mul)),
            ('Int64:://',   sdvmBinaryPrimitiveFor(SdvmInstInt64Div)),
            ('Int64::%',    sdvmBinaryPrimitiveFor(SdvmInstInt64Rem)),
            ('Int64::&',    sdvmBinaryPrimitiveFor(SdvmInstInt64And)),
            ('Int64::|',    sdvmBinaryPrimitiveFor(SdvmInstInt64Or)),
            ('Int64::^',    sdvmBinaryPrimitiveFor(SdvmInstInt64Xor)),
            ('Int64::<<',   sdvmBinaryPrimitiveFor(SdvmInstInt64Lsl)),
            ('Int64::>>',   sdvmBinaryPrimitiveFor(SdvmInstInt64Asr)),
            ('Int64::=',    sdvmBinaryPrimitiveFor(SdvmInstInt64Equals)),
            ('Int64::~=',   sdvmBinaryPrimitiveFor(SdvmInstInt64NotEquals)),
            ('Int64::<',    sdvmBinaryPrimitiveFor(SdvmInstInt64LessThan)),
            ('Int64::<=',   sdvmBinaryPrimitiveFor(SdvmInstInt64LessOrEquals)),
            ('Int64::>',    sdvmBinaryPrimitiveFor(SdvmInstInt64GreaterThan)),
            ('Int64::>=',   sdvmBinaryPrimitiveFor(SdvmInstInt64GreaterOrEquals)),
            ('Int64::min:', sdvmBinaryPrimitiveFor(SdvmInstInt64Min)),
            ('Int64::max:', sdvmBinaryPrimitiveFor(SdvmInstInt64Max)),

            ('UInt64::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Add)),
            ('UInt64::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Sub)),
            ('UInt64::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Mul)),
            ('UInt64:://',   sdvmBinaryPrimitiveFor(SdvmInstUInt64UDiv)),
            ('UInt64::%',    sdvmBinaryPrimitiveFor(SdvmInstUInt64URem)),
            ('UInt64::&',    sdvmBinaryPrimitiveFor(SdvmInstUInt64And)),
            ('UInt64::|',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Or)),
            ('UInt64::^',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Xor)),
            ('UInt64::<<',   sdvmBinaryPrimitiveFor(SdvmInstUInt64Lsl)),
            ('UInt64::>>',   sdvmBinaryPrimitiveFor(SdvmInstUInt64Lsr)),
            ('UInt64::=',    sdvmBinaryPrimitiveFor(SdvmInstUInt64Equals)),
            ('UInt64::~=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64NotEquals)),
            ('UInt64::<',    sdvmBinaryPrimitiveFor(SdvmInstUInt64LessThan)),
            ('UInt64::<=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64LessOrEquals)),
            ('UInt64::>',    sdvmBinaryPrimitiveFor(SdvmInstUInt64GreaterThan)),
            ('UInt64::>=',   sdvmBinaryPrimitiveFor(SdvmInstUInt64GreaterOrEquals)),
            ('UInt64::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt64Min)),
            ('UInt64::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt64Max)),

            ('Float32::+',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Add)),
            ('Float32::-',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Sub)),
            ('Float32::*',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Mul)),
            ('Float32::/',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Div)),
            ('Float32::sqrt',      sdvmUnaryPrimitiveFor(SdvmInstFloat32Sqrt)),
            ('Float32::=',        sdvmBinaryPrimitiveFor(SdvmInstFloat32Equals)),
            ('Float32::~=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32NotEquals)),
            ('Float32::<',        sdvmBinaryPrimitiveFor(SdvmInstFloat32LessThan)),
            ('Float32::<=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32LessOrEquals)),
            ('Float32::>',        sdvmBinaryPrimitiveFor(SdvmInstFloat32GreaterThan)),
            ('Float32::>=',       sdvmBinaryPrimitiveFor(SdvmInstFloat32GreaterOrEquals)),
            ('Float32::min:',     sdvmBinaryPrimitiveFor(SdvmInstFloat32Min)),
            ('Float32::max:',     sdvmBinaryPrimitiveFor(SdvmInstFloat32Max)),
            ('Float32::rounded',   sdvmUnaryPrimitiveFor(SdvmInstFloat32Round)),
            ('Float32::floor',     sdvmUnaryPrimitiveFor(SdvmInstFloat32Floor)),
            ('Float32::ceil',      sdvmUnaryPrimitiveFor(SdvmInstFloat32Ceil)),
            ('Float32::truncated', sdvmUnaryPrimitiveFor(SdvmInstFloat32Truncate)),

            ('Float64::+',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Add)),
            ('Float64::-',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Sub)),
            ('Float64::*',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Mul)),
            ('Float64::/',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Div)),
            ('Float64::sqrt',      sdvmUnaryPrimitiveFor(SdvmInstFloat64Sqrt)),
            ('Float64::=',        sdvmBinaryPrimitiveFor(SdvmInstFloat64Equals)),
            ('Float64::~=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64NotEquals)),
            ('Float64::<',        sdvmBinaryPrimitiveFor(SdvmInstFloat64LessThan)),
            ('Float64::<=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64LessOrEquals)),
            ('Float64::>',        sdvmBinaryPrimitiveFor(SdvmInstFloat64GreaterThan)),
            ('Float64::>=',       sdvmBinaryPrimitiveFor(SdvmInstFloat64GreaterOrEquals)),
            ('Float64::min:',     sdvmBinaryPrimitiveFor(SdvmInstFloat64Min)),
            ('Float64::max:',     sdvmBinaryPrimitiveFor(SdvmInstFloat64Max)),
            ('Float64::rounded',   sdvmUnaryPrimitiveFor(SdvmInstFloat64Round)),
            ('Float64::floor',     sdvmUnaryPrimitiveFor(SdvmInstFloat64Floor)),
            ('Float64::ceil',      sdvmUnaryPrimitiveFor(SdvmInstFloat64Ceil)),
            ('Float64::truncated', sdvmUnaryPrimitiveFor(SdvmInstFloat64Truncate)),

            ## Primitive vector float instructions.
            ('Float32x2::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Add)),
            ('Float32x2::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Sub)),
            ('Float32x2::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Mul)),
            ('Float32x2::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Div)),
            ('Float32x2::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Sqrt)),
            ('Float32x2::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Min)),
            ('Float32x2::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x2Max)),
            ('Float32x2::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Round)),
            ('Float32x2::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Floor)),
            ('Float32x2::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Ceil)),
            ('Float32x2::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x2Truncate)),

            ('Float32x3::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Add)),
            ('Float32x3::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Sub)),
            ('Float32x3::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Mul)),
            ('Float32x3::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Div)),
            ('Float32x3::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Sqrt)),
            ('Float32x3::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Min)),
            ('Float32x3::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Max)),
            ('Float32x3::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Round)),
            ('Float32x3::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Floor)),
            ('Float32x3::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Ceil)),
            ('Float32x3::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Truncate)),

            ('Float32x4::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Add)),
            ('Float32x4::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Sub)),
            ('Float32x4::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Mul)),
            ('Float32x4::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Div)),
            ('Float32x4::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Sqrt)),
            ('Float32x4::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Min)),
            ('Float32x4::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat32x4Max)),
            ('Float32x4::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Round)),
            ('Float32x4::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Floor)),
            ('Float32x4::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Ceil)),
            ('Float32x4::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat32x4Truncate)),

            ('Float64x2::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Add)),
            ('Float64x2::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Sub)),
            ('Float64x2::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Mul)),
            ('Float64x2::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Div)),
            ('Float64x2::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Sqrt)),
            ('Float64x2::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Min)),
            ('Float64x2::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x2Max)),
            ('Float64x2::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Round)),
            ('Float64x2::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Floor)),
            ('Float64x2::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Ceil)),
            ('Float64x2::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x2Truncate)),

            ('Float64x3::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Add)),
            ('Float64x3::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Sub)),
            ('Float64x3::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Mul)),
            ('Float64x3::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Div)),
            ('Float64x3::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Sqrt)),
            ('Float64x3::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Min)),
            ('Float64x3::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Max)),
            ('Float64x3::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Round)),
            ('Float64x3::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Floor)),
            ('Float64x3::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Ceil)),
            ('Float64x3::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Truncate)),

            ('Float64x4::+',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Add)),
            ('Float64x4::-',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Sub)),
            ('Float64x4::*',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Mul)),
            ('Float64x4::/',         sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Div)),
            ('Float64x4::sqrt',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Sqrt)),
            ('Float64x4::min:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Min)),
            ('Float64x4::max:',      sdvmBinaryPrimitiveFor(SdvmInstFloat64x4Max)),
            ('Float64x4::rounded',    sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Round)),
            ('Float64x4::floor',      sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Floor)),
            ('Float64x4::ceil',       sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Ceil)),
            ('Float64x4::truncated',  sdvmUnaryPrimitiveFor(SdvmInstFloat64x4Truncate)),

            ## Primitive vector integer instructions.
            ('Int32x2::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Add)),
            ('Int32x2::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Sub)),
            ('Int32x2::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x2Mul)),
            ('Int32x2::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x2Min)),
            ('Int32x2::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x2Max)),

            ('Int32x3::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Add)),
            ('Int32x3::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Sub)),
            ('Int32x3::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Mul)),
            ('Int32x3::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Min)),
            ('Int32x3::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Max)),

            ('Int32x4::+',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Add)),
            ('Int32x4::-',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Sub)),
            ('Int32x4::*',    sdvmBinaryPrimitiveFor(SdvmInstInt32x4Mul)),
            ('Int32x4::min:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Min)),
            ('Int32x4::max:', sdvmBinaryPrimitiveFor(SdvmInstInt32x4Max)),

            ('UInt32x2::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Add)),
            ('UInt32x2::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Sub)),
            ('UInt32x2::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Mul)),
            ('UInt32x2::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Min)),
            ('UInt32x2::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x2Max)),

            ('UInt32x3::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Add)),
            ('UInt32x3::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Sub)),
            ('UInt32x3::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Mul)),
            ('UInt32x3::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Min)),
            ('UInt32x3::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Max)),

            ('UInt32x4::+',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Add)),
            ('UInt32x4::-',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Sub)),
            ('UInt32x4::*',    sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Mul)),
            ('UInt32x4::min:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Min)),
            ('UInt32x4::max:', sdvmBinaryPrimitiveFor(SdvmInstUInt32x4Max)),

            ## Casting instruction table.
            ('Int8::asInt8',    yourselfTranslator),
            ('Int8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int16)),
            ('Int8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int32)),
            ('Int8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt8_SignExtend_Int64)),
            ('Int8::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt8_Bitcast_UInt8)),
            ('Int8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt16)),
            ('Int8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt32)),
            ('Int8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt64)),
            ('Int8::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt8_Bitcast_UInt8)),
            ('Int8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt16)),
            ('Int8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt8_ZeroExtend_UInt32)),
            ('Int8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt8_IntegerToFloat_Float32)),
            ('Int8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt8_IntegerToFloat_Float64)),

            ('UInt8::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt8_Bitcast_Int8)),
            ('UInt8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int16)),
            ('UInt8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int32)),
            ('UInt8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int64)),
            ('UInt8::asUInt8',   yourselfTranslator),
            ('UInt8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
            ('UInt8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
            ('UInt8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt64)),
            ('UInt8::asChar8',   yourselfTranslator),
            ('UInt8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
            ('UInt8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
            ('UInt8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float32)),
            ('UInt8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float64)),

            ('Char8::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt8_Bitcast_Int8)),
            ('Char8::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int16)),
            ('Char8::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int32)),
            ('Char8::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_Int64)),
            ('Char8::asUInt8',   yourselfTranslator),
            ('Char8::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
            ('Char8::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
            ('Char8::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt64)),
            ('Char8::asChar8',   yourselfTranslator),
            ('Char8::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt16)),
            ('Char8::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt8_ZeroExtend_UInt32)),
            ('Char8::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float32)),
            ('Char8::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt8_IntegerToFloat_Float64)),

            ('Int16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_Int8)),
            ('Int16::asInt16',   yourselfTranslator),
            ('Int16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt16_SignExtend_Int32)),
            ('Int16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt16_SignExtend_Int64)),
            ('Int16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_UInt8)),
            ('Int16::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt16_Bitcast_UInt16)),
            ('Int16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt32)),
            ('Int16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt64)),
            ('Int16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt16_Truncate_UInt8)),
            ('Int16::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt16_Bitcast_UInt16)),
            ('Int16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt16_ZeroExtend_UInt32)),
            ('Int16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt16_IntegerToFloat_Float32)),
            ('Int16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt16_IntegerToFloat_Float64)),

            ('UInt16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_Int8)),
            ('UInt16::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Bitcast_Int16)),
            ('UInt16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int32)),
            ('UInt16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int64)),
            ('UInt16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
            ('UInt16::asUInt16',  yourselfTranslator),
            ('UInt16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
            ('UInt16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt64)),
            ('UInt16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
            ('UInt16::asChar16',  yourselfTranslator),
            ('UInt16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
            ('UInt16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float32)),
            ('UInt16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float64)),

            ('Char16::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_Int8)),
            ('Char16::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Bitcast_Int16)),
            ('Char16::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int32)),
            ('Char16::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_Int64)),
            ('Char16::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
            ('Char16::asUInt16',  yourselfTranslator),
            ('Char16::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
            ('Char16::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt64)),
            ('Char16::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt16_Truncate_UInt8)),
            ('Char16::asChar16',  yourselfTranslator),
            ('Char16::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt16_ZeroExtend_UInt32)),
            ('Char16::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float32)),
            ('Char16::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt16_IntegerToFloat_Float64)),

            ('Int32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_Int8)),
            ('Int32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_Int16)),
            ('Int32::asInt32',   yourselfTranslator),
            ('Int32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstInt32_SignExtend_Int64)),
            ('Int32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt8)),
            ('Int32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt16)),
            ('Int32::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Bitcast_UInt32)),
            ('Int32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64)),
            ('Int32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt8)),
            ('Int32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Truncate_UInt16)),
            ('Int32::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt32_Bitcast_UInt32)),
            ('Int32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt32_IntegerToFloat_Float32)),
            ('Int32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt32_IntegerToFloat_Float64)),

            ('UInt32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int8)),
            ('UInt32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int16)),
            ('UInt32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Bitcast_Int32)),
            ('UInt32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_Int64)),
            ('UInt32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
            ('UInt32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
            ('UInt32::asUInt32',  yourselfTranslator),
            ('UInt32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_UInt64)),
            ('UInt32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
            ('UInt32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
            ('UInt32::asChar32',  yourselfTranslator),
            ('UInt32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float32)),
            ('UInt32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float64)),

            ('Char32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int8)),
            ('Char32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_Int16)),
            ('Char32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Bitcast_Int32)),
            ('Char32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_Int64)),
            ('Char32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
            ('Char32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
            ('Char32::asUInt32',  yourselfTranslator),
            ('Char32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_ZeroExtend_UInt64)),
            ('Char32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt8)),
            ('Char32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt32_Truncate_UInt16)),
            ('Char32::asChar32',  yourselfTranslator),
            ('Char32::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float32)),
            ('Char32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt32_IntegerToFloat_Float64)),

            ('Int64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int8)),
            ('Int64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int16)),
            ('Int64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_Int32)),
            ('Int64::asInt64',   yourselfTranslator),
            ('Int64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt8)),
            ('Int64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt16)),
            ('Int64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt32)),
            ('Int64::asUInt64',  yourselfTranslator),
            ('Int64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt8)),
            ('Int64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt16)),
            ('Int64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstInt64_Truncate_UInt32)),
            ('Int64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstInt64_IntegerToFloat_Float32)),
            ('Int64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstInt64_IntegerToFloat_Float64)),

            ('UInt64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int8)),
            ('UInt64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int16)),
            ('UInt64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_Int32)),
            ('UInt64::asInt64',   yourselfTranslator),
            ('UInt64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt8)),
            ('UInt64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt16)),
            ('UInt64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt32)),
            ('UInt64::asUInt64',  yourselfTranslator),
            ('UInt64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt8)),
            ('UInt64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt16)),
            ('UInt64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstUInt64_Truncate_UInt32)),
            ('UInt64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstUInt64_IntegerToFloat_Float32)),
            ('UInt64::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstUInt64_IntegerToFloat_Float64)),

            ('Float32::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int8)),
            ('Float32::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int16)),
            ('Float32::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int32)),
            ('Float32::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_Int64)),
            ('Float32::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt8)),
            ('Float32::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt16)),
            ('Float32::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt32)),
            ('Float32::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt64)),
            ('Float32::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt8)),
            ('Float32::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt16)),
            ('Float32::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatToInteger_UInt32)),
            ('Float32::asFloat32', yourselfTranslator),
            ('Float32::asFloat64', sdvmUnaryPrimitiveFor(SdvmInstFloat32_FloatExtend_Float64)),

            ('Float64::asInt8',    sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int8)),
            ('Float64::asInt16',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int16)),
            ('Float64::asInt32',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int32)),
            ('Float64::asInt64',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_Int64)),
            ('Float64::asUInt8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt8)),
            ('Float64::asUInt16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt16)),
            ('Float64::asUInt32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt32)),
            ('Float64::asUInt64',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt64)),
            ('Float64::asChar8',   sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt8)),
            ('Float64::asChar16',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt16)),
            ('Float64::asChar32',  sdvmUnaryPrimitiveFor(SdvmInstFloat64_FloatToInteger_UInt32)),
            ('Float64::asFloat32', sdvmUnaryPrimitiveFor(SdvmInstFloat64_Truncate_Float32)),
            ('Float64::asFloat64', yourselfTranslator),

            ('Int32::asSize',        self.pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64))),
            ('Int32::asUIntPointer', self.pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_ZeroExtend_UInt64))),
            ('Int32::asIntPointer',  self.pointerSizeTranslatorFor(yourselfTranslator, sdvmUnaryPrimitiveFor(SdvmInstInt32_SignExtend_Int64))),
        ]:
            name, translator = primitiveDef
            self.sdvmPrimitiveFunctionTranslationTable[name] = translator

    def pointerSizeTranslatorFor(self, pointer32Translator, pointer64Translator):
        if self.target.pointerSize == 4:
            return pointer32Translator
        else:
            return pointer64Translator

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
        self.instructionToSerializationIndexDictionary = {}

    def translateMirFunctionInto(self, mirFunction: ASGMirFunctionDefinitionNode, function: SDVMFunction):
        self.function = function
        scheduledMirFunction = mirFunctionDefinitionGCM(mirFunction)

        # Translate the arguments.
        self.function.beginArguments(len(mirFunction.arguments))
        for argument in mirFunction.arguments:
            self.translateValue(argument)

        # Declare the labels and the phi nodes
        self.instructionToSerializationIndexDictionary = {}
        for i in range(len(scheduledMirFunction.serializedInstructions)):
            instruction = scheduledMirFunction.serializedInstructions[i]
            self.instructionToSerializationIndexDictionary[instruction] = i
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
    
    def isScheduledBeforeThanInclusive(self, firstLabel, secondLabel):
        return self.instructionToSerializationIndexDictionary[firstLabel] <= self.instructionToSerializationIndexDictionary[secondLabel]

    @asgPatternMatchingOnNodeKind(ASGArgumentNode)
    def translateMirArgument(self, node: ASGArgumentNode):
        self.function.addArgumentInstruction(SDVMInstruction(node.type.getSDVMArgumentInstructionWith(self.moduleFrontend)))

    def translatePrimitiveApplicationWithArguments(self, resultType: ASGNode, functional: ASGLiteralPrimitiveFunctionNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
        primitiveTranslator = self.moduleFrontend.sdvmPrimitiveFunctionTranslationTable[functional.name]
        return primitiveTranslator(self, resultType, functional, arguments, sourcePosition)

    def translateApplicationWithArguments(self, resultType: ASGNode, functional: ASGNode, arguments: list[ASGNode], sourcePosition: SourcePosition):
        if functional.isLiteralPrimitiveFunction():
            return self.translatePrimitiveApplicationWithArguments(resultType, functional, arguments, sourcePosition)
            
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

    @asgPatternMatchingOnNodeKind(ASGConditionalBranchNode)
    def translateConditionalBranch(self, node: ASGConditionalBranchNode):
        condition = self.translateValue(node.condition)
        trueDestinationLabel = self.translateValue(node.trueDestination)
        falseDestinationLabel = self.translateValue(node.falseDestination)
        sourcePosition = node.sourceDerivation.getSourcePosition()
        if self.isScheduledBeforeThanInclusive(node.trueDestination, node.falseDestination):
            self.function.addInstruction(SDVMInstruction(SdvmInstJumpIfFalse, condition, falseDestinationLabel, sourcePosition = sourcePosition))
            self.function.addInstruction(SDVMInstruction(SdvmInstJump, trueDestinationLabel, sourcePosition = sourcePosition))
        else:
            self.function.addInstruction(SDVMInstruction(SdvmInstJumpIfTrue, condition, trueDestinationLabel, sourcePosition = sourcePosition))
            self.function.addInstruction(SDVMInstruction(SdvmInstJump, falseDestinationLabel, sourcePosition = sourcePosition))
    
    @asgPatternMatchingOnNodeKind(ASGSequenceReturnNode)
    def translateSequenceReturn(self, node: ASGSequenceReturnNode):
        result = self.translateValue(node.value)
        returnInstruction = node.value.type.getSDVMReturnInstructionWith(self.moduleFrontend)
        return self.function.addInstruction(SDVMInstruction(returnInstruction, result, sourcePosition = node.sourceDerivation.sourcePosition))