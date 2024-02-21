// Constants.
SDVM_CONSTANT_DEF(Boolean, 0, Boolean, "Boolean constant.")
SDVM_CONSTANT_DEF(Int8, 0, Int8, "Int8 constant.")
SDVM_CONSTANT_DEF(Int16, 0, Int16, "Int16 constant.")
SDVM_CONSTANT_DEF(Int32, 0, Int32, "Int32 constant.")
SDVM_CONSTANT_DEF(Int64SExt, 1, Int64, "Signed extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ZExt, 2, Int64, "Zero extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ConstSection, 3, Int64, "Int64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(UInt8, 0, UInt8, "UInt8 constant.")
SDVM_CONSTANT_DEF(UInt16, 0, UInt16, "UInt16 constant.")
SDVM_CONSTANT_DEF(UInt32, 0, UInt32, "UInt32 constant.")
SDVM_CONSTANT_DEF(UInt64SExt, 1, UInt64, "Signed extended small UInt64 constant.")
SDVM_CONSTANT_DEF(UInt64ZExt, 2, UInt64, "Zero extended small UInt64 constant.")
SDVM_CONSTANT_DEF(UInt64ConstSection, 3, UInt64, "UInt64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(PointerSExt, 0, Pointer, "Signed extended pointer constant")
SDVM_CONSTANT_DEF(PointerZExt, 1, Pointer, "Zero extended pointer constant")
SDVM_CONSTANT_DEF(PointerConstSection, 2, Pointer, "Int64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(GCPointerNull, 0, GCPointer, "Null fat pointer constant")
SDVM_CONSTANT_DEF(Float32, 0, Float32, "IEEE 754 single precision floating point constant.")
SDVM_CONSTANT_DEF(Float64Small32, 1, Float64, "IEEE 754 double precision floating point constant, encoded by extending IEEE 754 single precision constant.")
SDVM_CONSTANT_DEF(Float64ConstSection, 2, Float64, "IEEE 754 double precision floating point encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(Label, 0, Label, "Label")

// Opcodes.
SDVM_OPCODE_DEF(Nop, 0, "No operation")
SDVM_OPCODE_DEF(BeginArguments, 1, "Begin fetching arguments")
SDVM_OPCODE_DEF(BeginCall, 2, "Begin call")
SDVM_OPCODE_DEF(BeginCaptures, 3, "Begin captures")
SDVM_OPCODE_DEF(Arg, 4, "Fetch argument")
SDVM_OPCODE_DEF(CallArg, 5, "Pass call argument")
SDVM_OPCODE_DEF(Call, 6, "Call procedure")
SDVM_OPCODE_DEF(Load, 7, "Load value from memory")
SDVM_OPCODE_DEF(Store, 8, "Store value from memory")
SDVM_OPCODE_DEF(Return, 9, "Return value")

SDVM_OPCODE_DEF(Jump, 10, "Jump")
SDVM_OPCODE_DEF(JumpIfTrue, 11, "Conditional branch if true")
SDVM_OPCODE_DEF(JumpIfFalse, 12, "Conditional branch if false")
SDVM_OPCODE_DEF(Phi, 13, "Phi")
SDVM_OPCODE_DEF(MovePhi, 14, "Move into phi")

SDVM_OPCODE_DEF(Add, 15, "Addition")
SDVM_OPCODE_DEF(Sub, 16, "Subtraction")
SDVM_OPCODE_DEF(Mul, 17, "Multiplication")
SDVM_OPCODE_DEF(Div, 18, "Division")
SDVM_OPCODE_DEF(UDiv, 19, "Unsigned division")
SDVM_OPCODE_DEF(Rem, 20, "Remainder")
SDVM_OPCODE_DEF(Sqrt, 21, "Sqrt")

SDVM_OPCODE_DEF(And, 22, "Bitwise and")
SDVM_OPCODE_DEF(Or, 23, "Bitwise or")
SDVM_OPCODE_DEF(Xor, 24, "Bitwise xor")
SDVM_OPCODE_DEF(Lsl, 25, "Logical shift left")
SDVM_OPCODE_DEF(Lsr, 26, "Logical shift right")
SDVM_OPCODE_DEF(Asr, 27, "Arithmetic shift right")

SDVM_OPCODE_DEF(Equals, 28, "Equals. Unordered if float.")
SDVM_OPCODE_DEF(NotEquals, 29, "Not equals. Unordered if float.")
SDVM_OPCODE_DEF(LessThan, 30, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(LessOrEquals, 31, "Less or equals. Unordered if float.")
SDVM_OPCODE_DEF(GreaterThan, 32, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(GreaterOrEquals, 33, "Greater or equals. Unordered if float.")

// Common instructions
SDVM_INSTRUCTION_DEF(Nop, Nop, Void, Void, Void, "No operation")
SDVM_INSTRUCTION_DEF(BeginArguments, BeginArguments, Void, Info, Info, "Begin fetching arguments. Argument count. Calling convention.")
SDVM_INSTRUCTION_DEF(BeginCall, BeginCall, Void, Info, Info, "Begin call. Argument count. Calling convention index.")
SDVM_INSTRUCTION_DEF(BeginCaptures, BeginCaptures, GCPointer, Info, Void, "Begin captures.")

// Argument fetching instruction.
SDVM_INSTRUCTION_DEF(ArgBoolean,  Arg, Boolean,  Void, Void, "Fetch boolean argument")
SDVM_INSTRUCTION_DEF(ArgInt8,  Arg, Int8,  Void, Void, "Fetch int8 argument")
SDVM_INSTRUCTION_DEF(ArgInt16, Arg, Int16, Void, Void, "Fetch int16 argument")
SDVM_INSTRUCTION_DEF(ArgInt32, Arg, Int32, Void, Void, "Fetch int32 argument")
SDVM_INSTRUCTION_DEF(ArgInt64, Arg, Int64, Void, Void, "Fetch int64 argument")
SDVM_INSTRUCTION_DEF(ArgUInt8,  Arg, UInt8,  Void, Void, "Fetch uint8 argument")
SDVM_INSTRUCTION_DEF(ArgUInt16, Arg, UInt16, Void, Void, "Fetch uint16 argument")
SDVM_INSTRUCTION_DEF(ArgUInt32, Arg, UInt32, Void, Void, "Fetch uint32 argument")
SDVM_INSTRUCTION_DEF(ArgUInt64, Arg, UInt64, Void, Void, "Fetch uint64 argument")
SDVM_INSTRUCTION_DEF(ArgPointer, Arg, Pointer, Void, Void, "Fetch pointer argument")
SDVM_INSTRUCTION_DEF(ArgProcedureHandle, Arg, ProcedureHandle, Void, Void, "Fetch procedure handle argument")
SDVM_INSTRUCTION_DEF(ArgGCPointer, Arg, GCPointer, Void, Void, "Fetch fat pointer argument")
SDVM_INSTRUCTION_DEF(ArgFloat32, Arg, Float32, Void, Void, "Fetch float32 argument")
SDVM_INSTRUCTION_DEF(ArgFloat64, Arg, Float64, Void, Void, "Fetch float64 argument")
SDVM_INSTRUCTION_DEF(ArgFloatVector128, Arg, FloatVector128, Void, Void, "Fetch float vector 128 argument")
SDVM_INSTRUCTION_DEF(ArgIntegerVector128, Arg, IntegerVector128, Void, Void, "Fetch integer vector 128 argument")
SDVM_INSTRUCTION_DEF(ArgFloatVector256, Arg, FloatVector256, Void, Void, "Fetch float vector 256 argument")
SDVM_INSTRUCTION_DEF(ArgIntegerVector256, Arg, IntegerVector256, Void, Void, "Fetch integer 256 vector argument")

// Call argument instruction.
SDVM_INSTRUCTION_DEF(CallArgBoolean,  CallArg, Boolean,  ProcedureHandle, Void, "Pass call boolean argument")
SDVM_INSTRUCTION_DEF(CallArgInt8,  CallArg, Int8,  ProcedureHandle, Void, "Pass call int8 argument")
SDVM_INSTRUCTION_DEF(CallArgInt16, CallArg, Int16, ProcedureHandle, Void, "Pass call int16 argument")
SDVM_INSTRUCTION_DEF(CallArgInt32, CallArg, Int32, ProcedureHandle, Void, "Pass call int32 argument")
SDVM_INSTRUCTION_DEF(CallArgInt64, CallArg, Int64, ProcedureHandle, Void, "Pass call int64 argument")
SDVM_INSTRUCTION_DEF(CallArgUInt8,  CallArg, UInt8,  ProcedureHandle, Void, "Pass call uint8 argument")
SDVM_INSTRUCTION_DEF(CallArgUInt16, CallArg, UInt16, ProcedureHandle, Void, "Pass call uint16 argument")
SDVM_INSTRUCTION_DEF(CallArgUInt32, CallArg, UInt32, ProcedureHandle, Void, "Pass call uint32 argument")
SDVM_INSTRUCTION_DEF(CallArgUInt64, CallArg, UInt64, ProcedureHandle, Void, "Pass call uint64 argument")
SDVM_INSTRUCTION_DEF(CallArgPointer, CallArg, Pointer, ProcedureHandle, Void, "Pass call pointer argument")
SDVM_INSTRUCTION_DEF(CallArgProcedureHandle, CallArg, ProcedureHandle, ProcedureHandle, Void, "Pass call procedure handle argument")
SDVM_INSTRUCTION_DEF(CallArgGCPointer, CallArg, GCPointer, ProcedureHandle, Void, "Pass call fat pointer argument")
SDVM_INSTRUCTION_DEF(CallArgFloat32, CallArg, Float32, ProcedureHandle, Void, "Pass call float 32 argument")
SDVM_INSTRUCTION_DEF(CallArgFloat64, CallArg, Float64, ProcedureHandle, Void, "Pass call float 64 argument")
SDVM_INSTRUCTION_DEF(CallArgFloatVector128, CallArg, FloatVector128, ProcedureHandle, Void, "Pass call float vector argument")
SDVM_INSTRUCTION_DEF(CallArgIntegerVector128, CallArg, IntegerVector128, ProcedureHandle, Void, "Pass call integer vector argument")
SDVM_INSTRUCTION_DEF(CallArgFloatVector256, CallArg, FloatVector256, ProcedureHandle, Void, "Pass call float vector argument")
SDVM_INSTRUCTION_DEF(CallArgIntegerVector256, CallArg, IntegerVector256, ProcedureHandle, Void, "Pass call integer vector argument")

// Call instruction.
SDVM_INSTRUCTION_DEF(CallVoid, Call, Void, ProcedureHandle, Void, "Call void returning procedure")
SDVM_INSTRUCTION_DEF(CallBoolean, Call, Boolean, ProcedureHandle, Info, "Call boolean returning procedure")
SDVM_INSTRUCTION_DEF(CallInt8,  Call, Int8,  ProcedureHandle, Void, "Call int8 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt16, Call, Int16, ProcedureHandle, Void, "Call int16 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt32, Call, Int32, ProcedureHandle, Void, "Call int32 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt64, Call, Int64, ProcedureHandle, Void, "Call int64 returning procedure")
SDVM_INSTRUCTION_DEF(CallUInt8,  Call, UInt8,  ProcedureHandle, Void, "Call uint8 returning procedure")
SDVM_INSTRUCTION_DEF(CallUInt16, Call, UInt16, ProcedureHandle, Void, "Call uint16 returning procedure")
SDVM_INSTRUCTION_DEF(CallUInt32, Call, UInt32, ProcedureHandle, Void, "Call uint32 returning procedure")
SDVM_INSTRUCTION_DEF(CallUInt64, Call, UInt64, ProcedureHandle, Void, "Call uint64 returning procedure")
SDVM_INSTRUCTION_DEF(CallPointer, Call, Pointer, ProcedureHandle, Void, "Call pointer returning procedure")
SDVM_INSTRUCTION_DEF(CallProcedureHandle, Call, ProcedureHandle, ProcedureHandle, Void, "Call procedure handle returning procedure")
SDVM_INSTRUCTION_DEF(CallGCPointer, Call, GCPointer, ProcedureHandle, Void, "Call fat pointer")
SDVM_INSTRUCTION_DEF(CallFloat32, Call, Float32, ProcedureHandle, Void, "Call float32")
SDVM_INSTRUCTION_DEF(CallFloat64, Call, Float64, ProcedureHandle, Void, "Call float64")
SDVM_INSTRUCTION_DEF(CallFloatVector128, Call, FloatVector128, ProcedureHandle, Void, "Call float vector")
SDVM_INSTRUCTION_DEF(CallIntegerVector128, Call, IntegerVector128, ProcedureHandle, Void, "Call integer vector")
SDVM_INSTRUCTION_DEF(CallFloatVector256, Call, FloatVector256, ProcedureHandle, Void, "Call float vector")
SDVM_INSTRUCTION_DEF(CallIntegerVector256, Call, IntegerVector256, ProcedureHandle, Void, "Call integer vector")

// Returning instruction.
SDVM_INSTRUCTION_DEF(ReturnVoid, Return, Void, Void, Void, "Return void")
SDVM_INSTRUCTION_DEF(ReturnBoolean,  Return, Void, Boolean, Void, "Return boolean")
SDVM_INSTRUCTION_DEF(ReturnInt8,  Return, Void, Int8,  Void, "Return int8")
SDVM_INSTRUCTION_DEF(ReturnInt16, Return, Void, Int16, Void, "Return int16")
SDVM_INSTRUCTION_DEF(ReturnInt32, Return, Void, Int32, Void, "Return int32")
SDVM_INSTRUCTION_DEF(ReturnInt64, Return, Void, Int64, Void, "Return int64")
SDVM_INSTRUCTION_DEF(ReturnUInt8,  Return, Void, UInt8,  Void, "Return uint8")
SDVM_INSTRUCTION_DEF(ReturnUInt16, Return, Void, UInt16, Void, "Return uint16")
SDVM_INSTRUCTION_DEF(ReturnUInt32, Return, Void, UInt32, Void, "Return uint32")
SDVM_INSTRUCTION_DEF(ReturnUInt64, Return, Void, UInt64, Void, "Return uint64")
SDVM_INSTRUCTION_DEF(ReturnPointer, Return, Void, Pointer, Void, "Return pointer")
SDVM_INSTRUCTION_DEF(ReturnProcedureHandle, Return, Void, ProcedureHandle, Void, "Return procedure handle")
SDVM_INSTRUCTION_DEF(ReturnGCPointer, Return, Void, GCPointer, Void, "Return fat pointer")
SDVM_INSTRUCTION_DEF(ReturnFloat32, Return, Void, Float32, Void, "Return float 32")
SDVM_INSTRUCTION_DEF(ReturnFloat64, Return, Void, Float64, Void, "Return float 64")
SDVM_INSTRUCTION_DEF(ReturnFloatVector128, Return, Void, FloatVector128, Void, "Return float vector")
SDVM_INSTRUCTION_DEF(ReturnIntegerVector128, Return, Void, IntegerVector128, Void, "Return integer vector")
SDVM_INSTRUCTION_DEF(ReturnFloatVector256, Return, Void, FloatVector256, Void, "Return float vector")
SDVM_INSTRUCTION_DEF(ReturnIntegerVector256, Return, Void, IntegerVector256, Void, "Return integer vector")

// Returning instruction.
SDVM_INSTRUCTION_DEF(Jump, Jump, Void, Label, Void, "Unconditional jump")
SDVM_INSTRUCTION_DEF(JumpIfTrue, JumpIfTrue, Void, Boolean, Label, "Jump if true")
SDVM_INSTRUCTION_DEF(JumpIfFalse, JumpIfFalse, Void, Boolean, Label, "Jump if false")

// Arithmetic instructions.
#define IntegerType Int8
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType Int16
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType Int32
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType Int64
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType UInt8
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType UInt16
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType UInt32
#include "integerOpcodes.inc"
#undef IntegerType

#define IntegerType UInt64
#include "integerOpcodes.inc"
#undef IntegerType

#define FloatType Float32
#include "floatOpcodes.inc"
#undef FloatType

#define FloatType Float64
#include "floatOpcodes.inc"
#undef FloatType
