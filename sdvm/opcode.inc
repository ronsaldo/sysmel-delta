// Constants.
SDVM_CONSTANT_DEF(Int32, 0, Integer, "Int32 constant.")
SDVM_CONSTANT_DEF(Int64SExt, 1, Integer, "Signed extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ZExt, 2, Integer, "Zero extended small Int64 constant.")
SDVM_CONSTANT_DEF(Int64ConstSection, 2, Integer, "Int64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(PointerSExt, 0, Pointer, "Signed extended pointer constant")
SDVM_CONSTANT_DEF(PointerZExt, 1, Pointer, "Zero extended pointer constant")
SDVM_CONSTANT_DEF(PointerConstSection, 2, Pointer, "Int64 literal encoded in const section at zero extended offset.")
SDVM_CONSTANT_DEF(FatPointerNull, 0, FatPointer, "Null fat pointer constant")
SDVM_CONSTANT_DEF(Float32, 0, Float, "IEEE 754 single precision floating point constant.")
SDVM_CONSTANT_DEF(Float64Small32, 1, Float, "IEEE 754 double precision floating point constant, encoded by extending IEEE 754 single precision constant.")
SDVM_CONSTANT_DEF(Float64ConstSection, 2, Float, "IEEE 754 double precision floating point encoded in const section at zero extended offset.")

// Opcodes.
SDVM_OPCODE_DEF(Nop, 0, "No operation")
SDVM_OPCODE_DEF(BeginArguments, 1, "Begin fetching arguments")
SDVM_OPCODE_DEF(BeginCall, 2, "Begin call")
SDVM_OPCODE_DEF(Arg, 3, "Fetch argument")
SDVM_OPCODE_DEF(CallArg, 4, "Pass call argument")
SDVM_OPCODE_DEF(Call, 5, "Call procedure")
SDVM_OPCODE_DEF(Return, 6, "Return value")

// Common instructions
SDVM_INSTRUCTION_DEF(Nop, Nop, Void, Void, Void, "No operation")
SDVM_INSTRUCTION_DEF(BeginArguments, BeginArguments, Void, Info, Info, "Begin fetching arguments. Argument count. Calling convention.")
SDVM_INSTRUCTION_DEF(BeginCall, BeginCall, Void, Info, Info, "Begin call. Argument count. Calling convention index.")

// Argument fetching instruction.
SDVM_INSTRUCTION_DEF(ArgInteger, Arg, Integer, Void, Void, "Fetch integer argument")
SDVM_INSTRUCTION_DEF(ArgPointer, Arg, Pointer, Void, Void, "Fetch pointer argument")
SDVM_INSTRUCTION_DEF(ArgProcedureHandle, Arg, ProcedureHandle, Void, Void, "Fetch procedure handle argument")
SDVM_INSTRUCTION_DEF(ArgFatPointer, Arg, FatPointer, Void, Void, "Fetch fat pointer argument")
SDVM_INSTRUCTION_DEF(ArgFloat, Arg, Float, Void, Void, "Fetch float argument")
SDVM_INSTRUCTION_DEF(ArgFloatVector, Arg, FloatVector, Void, Void, "Fetch float vector argument")
SDVM_INSTRUCTION_DEF(ArgIntegerVector, Arg, IntegerVector, Void, Void, "Fetch integer vector argument")

// Call argument instruction.
SDVM_INSTRUCTION_DEF(CallArgInteger, CallArg, Integer, ProcedureHandle, Info, "Pass call integer argument")
SDVM_INSTRUCTION_DEF(CallArgPointer, CallArg, Pointer, ProcedureHandle, Info, "Pass call pointer argument")
SDVM_INSTRUCTION_DEF(CallArgProcedureHandle, CallArg, ProcedureHandle, ProcedureHandle, Info, "Pass call procedure handle argument")
SDVM_INSTRUCTION_DEF(CallArgFatPointer, CallArg, FatPointer, ProcedureHandle, Info, "Pass call fat pointer argument")
SDVM_INSTRUCTION_DEF(CallArgFloat, CallArg, Float, ProcedureHandle, Info, "Pass call float argument")
SDVM_INSTRUCTION_DEF(CallArgFloatVector, CallArg, FloatVector, ProcedureHandle, Info, "Pass call float vector argument")
SDVM_INSTRUCTION_DEF(CallArgIntegerVector, CallArg, IntegerVector, ProcedureHandle, Info, "Pass call integer vector argument")

// Call instruction.
SDVM_INSTRUCTION_DEF(CallVoid, Call, Void, ProcedureHandle, Info, "Call void returning procedure")
SDVM_INSTRUCTION_DEF(CallInteger, Call, Integer, ProcedureHandle, Info, "Call integer returning procedure")
SDVM_INSTRUCTION_DEF(CallPointer, Call, Pointer, ProcedureHandle, Info, "Call pointer returning procedure")
SDVM_INSTRUCTION_DEF(CallProcedureHandle, Call, ProcedureHandle, ProcedureHandle, Info, "Call procedure handle returning procedure")
SDVM_INSTRUCTION_DEF(CallFatPointer, Call, FatPointer, ProcedureHandle, Info, "Call fat pointer")
SDVM_INSTRUCTION_DEF(CallFloat, Call, Float, ProcedureHandle, Info, "Call float")
SDVM_INSTRUCTION_DEF(CallFloatVector, Call, FloatVector, ProcedureHandle, Info, "Call float vector")
SDVM_INSTRUCTION_DEF(CallIntegerVector, Call, IntegerVector, ProcedureHandle, Info, "Call integer vector")

// Returning instruction.
SDVM_INSTRUCTION_DEF(ReturnVoid, Return, Void, Void, Void, "Return void")
SDVM_INSTRUCTION_DEF(ReturnInteger, Return, Void, Integer, Void, "Return void")
SDVM_INSTRUCTION_DEF(ReturnPointer, Return, Void, Pointer, Void, "Return pointer")
SDVM_INSTRUCTION_DEF(ReturnProcedureHandle, Return, Void, ProcedureHandle, Void, "Return procedure handle")
SDVM_INSTRUCTION_DEF(ReturnFatPointer, Return, Void, FatPointer, Void, "Return fat pointer")
SDVM_INSTRUCTION_DEF(ReturnFloat, Return, Void, FloatVector, Void, "Return float vector")
SDVM_INSTRUCTION_DEF(ReturnFloatVector, Return, Void, FloatVector, Void, "Return float vector")
SDVM_INSTRUCTION_DEF(ReturnIntegerVector, Return, Void, IntegerVector, Void, "Return integer vector")
