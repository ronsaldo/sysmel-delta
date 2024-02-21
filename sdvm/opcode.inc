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
SDVM_OPCODE_DEF(Arg, 3, "Fetch argument")
SDVM_OPCODE_DEF(CallArg, 4, "Pass call argument")
SDVM_OPCODE_DEF(Call, 5, "Call procedure")
SDVM_OPCODE_DEF(Return, 6, "Return value")

SDVM_OPCODE_DEF(Jump, 7, "Jump")
SDVM_OPCODE_DEF(JumpIfTrue, 8, "Conditional branch if true")
SDVM_OPCODE_DEF(JumpIfFalse, 9, "Conditional branch if false")
SDVM_OPCODE_DEF(Phi, 10, "Phi")
SDVM_OPCODE_DEF(MovePhi, 11, "Move into phi")

SDVM_OPCODE_DEF(Add, 12, "Addition")
SDVM_OPCODE_DEF(Sub, 13, "Subtraction")
SDVM_OPCODE_DEF(Mul, 14, "Multiplication")
SDVM_OPCODE_DEF(Div, 15, "Division")
SDVM_OPCODE_DEF(UDiv, 16, "Unsigned division")
SDVM_OPCODE_DEF(Rem, 17, "Remainder")
SDVM_OPCODE_DEF(Sqrt, 18, "Sqrt")

SDVM_OPCODE_DEF(And, 19, "Bitwise and")
SDVM_OPCODE_DEF(Or, 20, "Bitwise or")
SDVM_OPCODE_DEF(Xor, 21, "Bitwise xor")
SDVM_OPCODE_DEF(Lsl, 22, "Logical shift left")
SDVM_OPCODE_DEF(Lsr, 23, "Logical shift right")
SDVM_OPCODE_DEF(Asr, 24, "Arithmetic shift right")

SDVM_OPCODE_DEF(Equals, 25, "Equals. Unordered if float.")
SDVM_OPCODE_DEF(NotEquals, 26, "Not equals. Unordered if float.")
SDVM_OPCODE_DEF(LessThan, 27, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(LessOrEquals, 28, "Less or equals. Unordered if float.")
SDVM_OPCODE_DEF(GreaterThan, 29, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(GreaterOrEquals, 30, "Greater or equals. Unordered if float.")

// Common instructions
SDVM_INSTRUCTION_DEF(Nop, Nop, Void, Void, Void, "No operation")
SDVM_INSTRUCTION_DEF(BeginArguments, BeginArguments, Void, Info, Info, "Begin fetching arguments. Argument count. Calling convention.")
SDVM_INSTRUCTION_DEF(BeginCall, BeginCall, Void, Info, Info, "Begin call. Argument count. Calling convention index.")

// Argument fetching instruction.
SDVM_INSTRUCTION_DEF(ArgInt8, Arg, Int8, Void, Void, "Fetch int8 argument")
SDVM_INSTRUCTION_DEF(ArgInt16, Arg, Int16, Void, Void, "Fetch int16 argument")
SDVM_INSTRUCTION_DEF(ArgInt32, Arg, Int32, Void, Void, "Fetch int32 argument")
SDVM_INSTRUCTION_DEF(ArgInt64, Arg, Int64, Void, Void, "Fetch int64 argument")
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
SDVM_INSTRUCTION_DEF(CallArgInt8, CallArg, Int8, ProcedureHandle, Info, "Pass call int8 argument")
SDVM_INSTRUCTION_DEF(CallArgInt16, CallArg, Int16, ProcedureHandle, Info, "Pass call int16 argument")
SDVM_INSTRUCTION_DEF(CallArgInt32, CallArg, Int32, ProcedureHandle, Info, "Pass call int32 argument")
SDVM_INSTRUCTION_DEF(CallArgInt64, CallArg, Int64, ProcedureHandle, Info, "Pass call int64 argument")
SDVM_INSTRUCTION_DEF(CallArgPointer, CallArg, Pointer, ProcedureHandle, Info, "Pass call pointer argument")
SDVM_INSTRUCTION_DEF(CallArgProcedureHandle, CallArg, ProcedureHandle, ProcedureHandle, Info, "Pass call procedure handle argument")
SDVM_INSTRUCTION_DEF(CallArgGCPointer, CallArg, GCPointer, ProcedureHandle, Info, "Pass call fat pointer argument")
SDVM_INSTRUCTION_DEF(CallArgFloat32, CallArg, Float32, ProcedureHandle, Info, "Pass call float 32 argument")
SDVM_INSTRUCTION_DEF(CallArgFloat64, CallArg, Float64, ProcedureHandle, Info, "Pass call float 64 argument")
SDVM_INSTRUCTION_DEF(CallArgFloatVector128, CallArg, FloatVector128, ProcedureHandle, Info, "Pass call float vector argument")
SDVM_INSTRUCTION_DEF(CallArgIntegerVector128, CallArg, IntegerVector128, ProcedureHandle, Info, "Pass call integer vector argument")
SDVM_INSTRUCTION_DEF(CallArgFloatVector256, CallArg, FloatVector256, ProcedureHandle, Info, "Pass call float vector argument")
SDVM_INSTRUCTION_DEF(CallArgIntegerVector256, CallArg, IntegerVector256, ProcedureHandle, Info, "Pass call integer vector argument")

// Call instruction.
SDVM_INSTRUCTION_DEF(CallVoid, Call, Void, ProcedureHandle, Info, "Call void returning procedure")
SDVM_INSTRUCTION_DEF(CallInt8, Call, Int8, ProcedureHandle, Info, "Call int8 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt16, Call, Int16, ProcedureHandle, Info, "Call int16 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt32, Call, Int32, ProcedureHandle, Info, "Call int32 returning procedure")
SDVM_INSTRUCTION_DEF(CallInt64, Call, Int64, ProcedureHandle, Info, "Call int64 returning procedure")
SDVM_INSTRUCTION_DEF(CallPointer, Call, Pointer, ProcedureHandle, Info, "Call pointer returning procedure")
SDVM_INSTRUCTION_DEF(CallProcedureHandle, Call, ProcedureHandle, ProcedureHandle, Info, "Call procedure handle returning procedure")
SDVM_INSTRUCTION_DEF(CallGCPointer, Call, GCPointer, ProcedureHandle, Info, "Call fat pointer")
SDVM_INSTRUCTION_DEF(CallFloat32, Call, Float32, ProcedureHandle, Info, "Call float32")
SDVM_INSTRUCTION_DEF(CallFloat64, Call, Float64, ProcedureHandle, Info, "Call float64")
SDVM_INSTRUCTION_DEF(CallFloatVector128, Call, FloatVector128, ProcedureHandle, Info, "Call float vector")
SDVM_INSTRUCTION_DEF(CallIntegerVector128, Call, IntegerVector128, ProcedureHandle, Info, "Call integer vector")
SDVM_INSTRUCTION_DEF(CallFloatVector256, Call, FloatVector256, ProcedureHandle, Info, "Call float vector")
SDVM_INSTRUCTION_DEF(CallIntegerVector256, Call, IntegerVector256, ProcedureHandle, Info, "Call integer vector")

// Returning instruction.
SDVM_INSTRUCTION_DEF(ReturnVoid, Return, Void, Void, Void, "Return void")
SDVM_INSTRUCTION_DEF(ReturnInt8, Return, Void, Int8, Void, "Return int8")
SDVM_INSTRUCTION_DEF(ReturnInt16, Return, Void, Int16, Void, "Return int16")
SDVM_INSTRUCTION_DEF(ReturnInt32, Return, Void, Int32, Void, "Return int32")
SDVM_INSTRUCTION_DEF(ReturnInt64, Return, Void, Int64, Void, "Return int64")
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
