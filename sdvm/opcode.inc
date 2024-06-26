// Constant opcodes.
SDVM_CONSTANT_OPCODE_DEF(ConstSExt,           0, "Small signed extended constant")
SDVM_CONSTANT_OPCODE_DEF(ConstZExt,           1, "Small zero extended constant")
SDVM_CONSTANT_OPCODE_DEF(ConstSmallFloat,     2, "Small floating point constant")
SDVM_CONSTANT_OPCODE_DEF(ConstSection,        3, "Constant section")
SDVM_CONSTANT_OPCODE_DEF(ConstImport,         4, "Constant imported value")
SDVM_CONSTANT_OPCODE_DEF(ConstCString,        5, "Constant null terminated C string")
SDVM_CONSTANT_OPCODE_DEF(ConstString,         6, "Constant non-null terminated string")
SDVM_CONSTANT_OPCODE_DEF(ConstLocalProcedure, 7, "Constant local procedure.")
SDVM_CONSTANT_OPCODE_DEF(ConstData,           8, "Constant data section pointer.")
SDVM_CONSTANT_OPCODE_DEF(ConstObject,         9, "Constant object pointer.")

// Constants.
SDVM_CONSTANT_DEF(Boolean,            ConstSExt,    Boolean, "Boolean constant.")
SDVM_CONSTANT_DEF(Int8,               ConstSExt,    Int8,    "Int8 constant.")
SDVM_CONSTANT_DEF(Int16,              ConstSExt,    Int16,   "Int16 constant.")
SDVM_CONSTANT_DEF(Int32,              ConstSExt,    Int32,   "Int32 constant.")
SDVM_CONSTANT_DEF(Int64SExt,          ConstSExt,    Int64,   "Signed extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ZExt,          ConstZExt,    Int64,   "Zero extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ConstSection,  ConstSection, Int64,   "Int64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(UInt8,              ConstSExt,    UInt8,    "Int8 constant.")
SDVM_CONSTANT_DEF(UInt16,             ConstSExt,    UInt16,   "Int16 constant.")
SDVM_CONSTANT_DEF(UInt32,             ConstSExt,    UInt32,   "Int32 constant.")
SDVM_CONSTANT_DEF(UInt64SExt,         ConstSExt,    UInt64,   "Signed extended small Int64 constant.")
SDVM_CONSTANT_DEF(UInt64ZExt,         ConstZExt,    UInt64,   "Zero extended small Int64 constant.")
SDVM_CONSTANT_DEF(UInt64ConstSection, ConstSection, UInt64,   "Int64 literal encoded in const section at zero extended offset.")

SDVM_CONSTANT_DEF(PointerSExt,           ConstSExt,     Pointer,   "Signed extended small pointer constant.")
SDVM_CONSTANT_DEF(PointerZExt,           ConstZExt,     Pointer,   "Zero extended small pointer constant.")
SDVM_CONSTANT_DEF(PointerConstSection,   ConstSection,  Pointer,   "Pointer literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(PointerCString,        ConstCString,  Pointer,   "Pointer into null terminated c string.")
SDVM_CONSTANT_DEF(PointerString,         ConstString,   Pointer,   "Pointer into non-null terminated string.")
SDVM_CONSTANT_DEF(PointerData,           ConstData,     Pointer,   "Pointer into the data section.")
SDVM_CONSTANT_DEF(PointerObject,         ConstObject,   Pointer,   "Pointer into the object section.")
SDVM_CONSTANT_DEF(GCPointerSExt,         ConstSExt,     GCPointer, "Signed extended small gc pointer constant.")
SDVM_CONSTANT_DEF(GCPointerZExt,         ConstZExt,     GCPointer, "Zero extended small gc pointer constant.")
SDVM_CONSTANT_DEF(GCPointerConstSection, ConstSection,  GCPointer, "GC Pointer literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(GCPointerCString,      ConstCString,  GCPointer, "GC Pointer into null terminated c string.")
SDVM_CONSTANT_DEF(GCPointerString,       ConstString,   GCPointer, "GC Pointer into non-null terminated string.")
SDVM_CONSTANT_DEF(GCPointerData,         ConstData,     GCPointer, "GC Pointer into the data section.")
SDVM_CONSTANT_DEF(GCPointerObject,       ConstObject,   GCPointer, "GC Pointer into the object section.")
SDVM_CONSTANT_DEF(ImportPointer,         ConstImport,   Pointer,   "Pointer imported constant.")
SDVM_CONSTANT_DEF(ImportProcedureHandle, ConstImport,   ProcedureHandle, "Procedure handle imported constant.")

SDVM_CONSTANT_DEF(LocalProcedureHandle, ConstLocalProcedure,   ProcedureHandle, "Local procedure handle constant.")

SDVM_CONSTANT_DEF(Float32,             ConstZExt,       Float32, "Float32 constant.")
SDVM_CONSTANT_DEF(Float64Small,        ConstSmallFloat, Float64, "Small float.")
SDVM_CONSTANT_DEF(Float64ConstSection, ConstSection,    Float64, "Float64 in constant section.")

SDVM_CONSTANT_DEF(Label, ConstZExt, Label, "Label constant.")

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
SDVM_OPCODE_DEF(URem, 21, "Unsigned remainder")
SDVM_OPCODE_DEF(Sqrt, 22, "Sqrt")

SDVM_OPCODE_DEF(And, 23, "Bitwise and")
SDVM_OPCODE_DEF(Or, 24, "Bitwise or")
SDVM_OPCODE_DEF(Xor, 25, "Bitwise xor")
SDVM_OPCODE_DEF(Lsl, 26, "Logical shift left")
SDVM_OPCODE_DEF(Lsr, 27, "Logical shift right")
SDVM_OPCODE_DEF(Asr, 28, "Arithmetic shift right")

SDVM_OPCODE_DEF(Equals, 29, "Equals. Unordered if float.")
SDVM_OPCODE_DEF(NotEquals, 30, "Not equals. Unordered if float.")
SDVM_OPCODE_DEF(LessThan, 31, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(LessOrEquals, 32, "Less or equals. Unordered if float.")
SDVM_OPCODE_DEF(GreaterThan, 33, "Less than. Unordered if float.")
SDVM_OPCODE_DEF(GreaterOrEquals, 34, "Greater or equals. Unordered if float.")

SDVM_OPCODE_DEF(Min, 35, "Minimum.")
SDVM_OPCODE_DEF(Max, 36, "Maximum.")

SDVM_OPCODE_DEF(Floor, 38, "Floating point floor.")
SDVM_OPCODE_DEF(Ceil, 39, "Floating point ceiling.")
SDVM_OPCODE_DEF(Truncate, 40, "Floating point truncate.")
SDVM_OPCODE_DEF(Round, 41, "Floating point round.")

SDVM_OPCODE_DEF(Bitcast, 42, "Bit cast.")
SDVM_OPCODE_DEF(SignExtend, 43, "Sign extend.")
SDVM_OPCODE_DEF(ZeroExtend, 44, "Zero extend.")
SDVM_OPCODE_DEF(TruncateCast, 45, "Truncate cast.")
SDVM_OPCODE_DEF(FloatExtend, 46, "Floating point extension.")
SDVM_OPCODE_DEF(FloatToInteger, 47, "Floating point to signed integer.")
SDVM_OPCODE_DEF(IntegerToFloat, 48, "Signed integer to floating point.")

SDVM_OPCODE_DEF(AllocateLocal,  49, "Allocates local only memory.")
SDVM_OPCODE_DEF(AllocateGC,     50, "Allocates Garbage Collected memory")
SDVM_OPCODE_DEF(AllocateManual, 51, "Allocates Manual memory")
SDVM_OPCODE_DEF(FreeManual,     52, "Frees Manual memory")
SDVM_OPCODE_DEF(MemcopyFixed,   53, "Fixed Size Memory Copy")
SDVM_OPCODE_DEF(Memcopy,        53, "Variable Size Memory Copy")

SDVM_OPCODE_DEF(ExtraArguments, 254, "Third and fourth extra arguments")

// Common instructions
SDVM_INSTRUCTION_DEF(Nop, Nop, Void, Void, Void, "No operation")
SDVM_INSTRUCTION_DEF(BeginArguments, BeginArguments, Void, Info, Info, "Begin fetching arguments. Argument count. Calling convention.")
SDVM_INSTRUCTION_DEF(BeginCall, BeginCall, Void, Info, Info, "Begin call. Low 8 bits fixed argument count. High bit set. Calling convention index.")
SDVM_INSTRUCTION_DEF(BeginCaptures, BeginCaptures, GCPointer, Info, Void, "Begin captures.")

// Argument fetching instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(Arg ## type, Arg, type,  Void, Void, "Fetch " #type " argument")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Call argument instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(CallArg ## type, CallArg, Void, type, Void, "Pass call " #type " argument")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Call instructions.
SDVM_INSTRUCTION_DEF(CallVoid, Call, Void, ProcedureHandle, Void, "Call void returning procedure")

#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(Call ## type, Call, type, ProcedureHandle, Info, "Call " #type " returning procedure")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Call gc closure instructions.
SDVM_INSTRUCTION_DEF(CallClosureVoid, Call, Void, GCPointer, Void, "Call void returning procedure")

#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(CallClosure ## type, Call, type, GCPointer, Info, "Call " #type " returning closure")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Returning instructions.
SDVM_INSTRUCTION_DEF(ReturnVoid, Return, Void, Void, Void, "Return void")

#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(Return ## type, Return, Void, type, Void, "Return " #type)
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Load instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(Load ## type, Load, type, Pointer, Void, "Load " #type " value from memory")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Store instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(Store ## type, Store, Void, Pointer, type, "Store " #type " value into memory")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Load gc instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(LoadGC_ ## type, Load, type, GCPointer, Void, "Load " #type " value from memory")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Store gc instructions.
#define SDVM_VALUE_TYPE_INSTRUCTION_DEF(type) SDVM_INSTRUCTION_DEF(StoreGC_ ## type, Store, Void, GCPointer, type, "Store " #type " value into memory")
#include "valueTypeOpcodes.inc"
#undef SDVM_VALUE_TYPE_INSTRUCTION_DEF

// Control flow instructions
SDVM_INSTRUCTION_DEF(Jump, Jump, Void, Label, Void, "Unconditional jump")
SDVM_INSTRUCTION_DEF(JumpIfTrue, JumpIfTrue, Void, Boolean, Label, "Jump if true")
SDVM_INSTRUCTION_DEF(JumpIfFalse, JumpIfFalse, Void, Boolean, Label, "Jump if false")

// Pointer instructions
SDVM_INSTRUCTION_DEF(PointerAddOffsetInt32,  Add, Pointer, Pointer, Int32, "Add int32 offset to pointer.")
SDVM_INSTRUCTION_DEF(PointerAddOffsetInt64,  Add, Pointer, Pointer, Int64, "Add int64 offset to pointer.")
SDVM_INSTRUCTION_DEF(PointerAddOffsetUInt32, Add, Pointer, Pointer, UInt32, "Add uint64 offset to pointer.")
SDVM_INSTRUCTION_DEF(PointerAddOffsetUInt64, Add, Pointer, Pointer, UInt64, "Add int64 offset to pointer.")

SDVM_INSTRUCTION_DEF(GCPointerAddOffsetInt32,  Add, GCPointer, GCPointer, Int32, "Add int32 offset to gc pointer.")
SDVM_INSTRUCTION_DEF(GCPointerAddOffsetInt64,  Add, GCPointer, GCPointer, Int64, "Add int64 offset to gc pointer.")
SDVM_INSTRUCTION_DEF(GCPointerAddOffsetUInt32, Add, GCPointer, GCPointer, UInt32, "Add uint64 offset to gc pointer.")
SDVM_INSTRUCTION_DEF(GCPointerAddOffsetUInt64, Add, GCPointer, GCPointer, UInt64, "Add int64 offset to gc pointer.")

// Memory instructions
SDVM_INSTRUCTION_DEF(AllocateLocal, AllocateLocal, Pointer, Info, Void, "Allocates local only memory.")
SDVM_INSTRUCTION_DEF(AllocateGCNoEscape, AllocateLocal, GCPointer, Info, Void, "Allocates no escape GC memory.")
SDVM_INSTRUCTION_DEF(AllocateGC, AllocateGC, GCPointer, Info, Void, "Allocates no escape GC memory.")
SDVM_INSTRUCTION_DEF(AllocateManual, AllocateManual, Pointer, Info, Void, "Allocates manual memory.")
SDVM_INSTRUCTION_DEF(FreeManual, FreeManual, Void, Pointer, Info, "Frees memory.")
SDVM_INSTRUCTION_DEF(MemcopyFixed, MemcopyFixed, Void, Pointer, Pointer, "Memcopy fixed.")
SDVM_INSTRUCTION_DEF(MemcopyGCFixed, MemcopyFixed, Void, GCPointer, Pointer, "Memcopy gc fixed.")

SDVM_INSTRUCTION_DEF(ExtraArgumentsInfo,   ExtraArguments, Void, Info,   Void, "Info extra arguments.")
SDVM_INSTRUCTION_DEF(ExtraArgumentsInt32,  ExtraArguments, Void, Int32,  Void, "Int32 extra arguments.")
SDVM_INSTRUCTION_DEF(ExtraArgumentsUInt32, ExtraArguments, Void, UInt32, Void, "UInt32 extra arguments.")
SDVM_INSTRUCTION_DEF(ExtraArgumentsInt64,  ExtraArguments, Void, Int64,  Void, "Int64 extra arguments.")
SDVM_INSTRUCTION_DEF(ExtraArgumentsUInt64, ExtraArguments, Void, UInt64, Void, "UInt64 extra arguments.")

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

// Primitive float vector arithmetic
#define VectorType Float32x2
#include "floatVectorOpcodes.inc"
#undef VectorType

#define VectorType Float32x4
#include "floatVectorOpcodes.inc"
#undef VectorType

#define VectorType Float64x2
#include "floatVectorOpcodes.inc"
#undef VectorType

#define VectorType Float64x4
#include "floatVectorOpcodes.inc"
#undef VectorType

// Primitive integer vector arithmetic
#define VectorType Int32x2
#include "integerVectorOpcodes.inc"
#undef VectorType

#define VectorType Int32x4
#include "integerVectorOpcodes.inc"
#undef VectorType

#define VectorType UInt32x2
#include "integerVectorOpcodes.inc"
#undef VectorType

#define VectorType UInt32x4
#include "integerVectorOpcodes.inc"
#undef VectorType

// Casting instructions
SDVM_CAST_INSTRUCTION_DEF( Int8, Bitcast, UInt8)
SDVM_CAST_INSTRUCTION_DEF(UInt8, Bitcast,  Int8)

SDVM_CAST_INSTRUCTION_DEF( Int16, Bitcast, UInt16)
SDVM_CAST_INSTRUCTION_DEF(UInt16, Bitcast,  Int16)

SDVM_CAST_INSTRUCTION_DEF(  Int32, Bitcast,  UInt32)
SDVM_CAST_INSTRUCTION_DEF(  Int32, Bitcast, Float32)
SDVM_CAST_INSTRUCTION_DEF( UInt32, Bitcast,   Int32)
SDVM_CAST_INSTRUCTION_DEF( UInt32, Bitcast, Float32)
SDVM_CAST_INSTRUCTION_DEF(Float32, Bitcast,   Int32)
SDVM_CAST_INSTRUCTION_DEF(Float32, Bitcast,  UInt32)

SDVM_CAST_INSTRUCTION_DEF(  Int64, Bitcast,  UInt64)
SDVM_CAST_INSTRUCTION_DEF(  Int64, Bitcast, Float64)
SDVM_CAST_INSTRUCTION_DEF( UInt64, Bitcast,   Int64)
SDVM_CAST_INSTRUCTION_DEF( UInt64, Bitcast, Float64)
SDVM_CAST_INSTRUCTION_DEF(Float64, Bitcast,   Int64)
SDVM_CAST_INSTRUCTION_DEF(Float64, Bitcast,  UInt64)

SDVM_CAST_INSTRUCTION_DEF( Int8, SignExtend, Int16)
SDVM_CAST_INSTRUCTION_DEF( Int8, SignExtend, Int32)
SDVM_CAST_INSTRUCTION_DEF( Int8, SignExtend, Int64)
SDVM_CAST_INSTRUCTION_DEF(Int16, SignExtend, Int32)
SDVM_CAST_INSTRUCTION_DEF(Int16, SignExtend, Int64)
SDVM_CAST_INSTRUCTION_DEF(Int32, SignExtend, Int64)

SDVM_CAST_INSTRUCTION_DEF( Int8, ZeroExtend, UInt16)
SDVM_CAST_INSTRUCTION_DEF( Int8, ZeroExtend, UInt32)
SDVM_CAST_INSTRUCTION_DEF( Int8, ZeroExtend, UInt64)
SDVM_CAST_INSTRUCTION_DEF(Int16, ZeroExtend, UInt32)
SDVM_CAST_INSTRUCTION_DEF(Int16, ZeroExtend, UInt64)
SDVM_CAST_INSTRUCTION_DEF(Int32, ZeroExtend, UInt64)

SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, UInt16)
SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, UInt32)
SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, UInt64)
SDVM_CAST_INSTRUCTION_DEF(UInt16, ZeroExtend, UInt32)
SDVM_CAST_INSTRUCTION_DEF(UInt16, ZeroExtend, UInt64)
SDVM_CAST_INSTRUCTION_DEF(UInt32, ZeroExtend, UInt64)

SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, Int16)
SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, Int32)
SDVM_CAST_INSTRUCTION_DEF( UInt8, ZeroExtend, Int64)
SDVM_CAST_INSTRUCTION_DEF(UInt16, ZeroExtend, Int32)
SDVM_CAST_INSTRUCTION_DEF(UInt16, ZeroExtend, Int64)
SDVM_CAST_INSTRUCTION_DEF(UInt32, ZeroExtend, Int64)

SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate,  Int32)
SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate,  Int16)
SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate, UInt32)
SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate, UInt16)
SDVM_CAST_INSTRUCTION_DEF(Int64, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate,  Int32)
SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate,  Int16)
SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate, UInt32)
SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate, UInt16)
SDVM_CAST_INSTRUCTION_DEF(UInt64, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(Int32, Truncate,  Int16)
SDVM_CAST_INSTRUCTION_DEF(Int32, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(Int32, Truncate, UInt16)
SDVM_CAST_INSTRUCTION_DEF(Int32, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(UInt32, Truncate,  Int16)
SDVM_CAST_INSTRUCTION_DEF(UInt32, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(UInt32, Truncate, UInt16)
SDVM_CAST_INSTRUCTION_DEF(UInt32, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(Int16, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(Int16, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(UInt16, Truncate,   Int8)
SDVM_CAST_INSTRUCTION_DEF(UInt16, Truncate,  UInt8)

SDVM_CAST_INSTRUCTION_DEF(Float32, FloatExtend, Float64)
SDVM_CAST_INSTRUCTION_DEF(Float64, Truncate, Float32)

SDVM_CAST_INSTRUCTION_DEF( Int8, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(Int16, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(Int32, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(Int64, IntegerToFloat, Float32)

SDVM_CAST_INSTRUCTION_DEF( Int8, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(Int16, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(Int32, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(Int64, IntegerToFloat, Float64)

SDVM_CAST_INSTRUCTION_DEF( UInt8, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(UInt16, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(UInt32, IntegerToFloat, Float32)
SDVM_CAST_INSTRUCTION_DEF(UInt64, IntegerToFloat, Float32)

SDVM_CAST_INSTRUCTION_DEF( UInt8, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(UInt16, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(UInt32, IntegerToFloat, Float64)
SDVM_CAST_INSTRUCTION_DEF(UInt64, IntegerToFloat, Float64)

SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger,  Int8)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, Int16)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, Int32)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, Int64)

SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger,  Int8)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, Int16)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, Int32)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, Int64)

SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger,  UInt8)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, UInt16)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, UInt32)
SDVM_CAST_INSTRUCTION_DEF(Float32, FloatToInteger, UInt64)

SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger,  UInt8)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, UInt16)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, UInt32)
SDVM_CAST_INSTRUCTION_DEF(Float64, FloatToInteger, UInt64)
