#ifndef SDVM_COMPILER_H
#define SDVM_COMPILER_H

#include "common.h"
#include "dynarray.h"
#include "instruction.h"
#include "dwarf.h"
#include <stdbool.h>

#define SDVM_COMPILER_SECTION_COUNT 10

typedef struct sdvm_module_s sdvm_module_t;

typedef enum sdvm_compilerSectionFlags_e
{
    SdvmCompSectionFlagNone = 0,
    SdvmCompSectionFlagWrite = 1<<0,
    SdvmCompSectionFlagRead = 1<<1,
    SdvmCompSectionFlagExec = 1<<2,
    SdvmCompSectionFlagNoBits = 1<<3,
    SdvmCompSectionFlagUnwind = 1<<4,
    SdvmCompSectionFlagDebug = 1<<5,
} sdvm_compilerSectionFlags_t;

typedef enum sdvm_compilerSymbolKind_e
{
    SdvmCompSymbolKindNull = 0,
    SdvmCompSymbolKindFile,
    SdvmCompSymbolKindSection,
    SdvmCompSymbolKindFunction,
    SdvmCompSymbolKindVariable,
    SdvmCompSymbolKindTLS,
} sdvm_compilerSymbolKind_t;

typedef enum sdvm_compilerSymbolBinding_e
{
    SdvmCompSymbolBindingLocal = 0,
    SdvmCompSymbolBindingGlobal,
    SdvmCompSymbolBindingWeak,
    SdvmCompSymbolBindingDllImport,
    SdvmCompSymbolBindingDllExport,
} sdvm_compilerSymbolBinding_t;

typedef enum sdvm_compilerRelocationKind_e
{
    SdvmCompRelocationNull = 0,
    SdvmCompRelocationAbsolute8,
    SdvmCompRelocationAbsolute16,
    SdvmCompRelocationAbsolute32,
    SdvmCompRelocationAbsolute64,
    SdvmCompRelocationRelative8,
    SdvmCompRelocationRelative16,
    SdvmCompRelocationRelative32,
    SdvmCompRelocationRelative32AtGot,
    SdvmCompRelocationRelative32AtPlt,
    SdvmCompRelocationRelative64,
    SdvmCompRelocationSectionRelative32,
} sdvm_compilerRelocationKind_t;

typedef enum sdvm_compilerLocationKind_e
{
    SdvmCompLocationNull = 0,
    SdvmCompLocationImmediateS32,
    SdvmCompLocationImmediateU32,
    SdvmCompLocationImmediateS64,
    SdvmCompLocationImmediateU64,
    SdvmCompLocationImmediateF32,
    SdvmCompLocationImmediateF64,
    SdvmCompLocationImmediateLabel,
    SdvmCompLocationConstantSection,
    SdvmCompLocationRegister,
    SdvmCompLocationRegisterPair,
    SdvmCompLocationStack,
    SdvmCompLocationStackPair,
    SdvmCompLocationStackAddress,
    SdvmCompLocationLocalSymbolValue,
    SdvmCompLocationGlobalSymbolValue,
} sdvm_compilerLocationKind_t;

typedef enum sdvm_compilerRegisterKind_e
{
    SdvmCompRegisterKindInteger = 0,
    SdvmCompRegisterKindFloat,
    SdvmCompRegisterKindVectorFloat,
    SdvmCompRegisterKindVectorInteger,
    SdvmCompRegisterKindCount
} sdvm_compilerRegisterKind_t;

typedef enum sdvm_compilerObjectFileType_e
{
    SdvmObjectFileTypeElf = 0,
    SdvmObjectFileTypeCoff,
    SdvmObjectFileTypeMachO,
} sdvm_compilerObjectFileType_t;

typedef enum sdvm_functionStackSegmentName_e
{
    SdvmFunctionStackSegmentArgumentPassing = 0,
    SdvmFunctionStackSegmentPrologue,
    SdvmFunctionStackSegmentFloatCallPreservedRegister,
    SdvmFunctionStackSegmentVectorCallPreservedRegister,
    SdvmFunctionStackSegmentTemporary,
    SdvmFunctionStackSegmentCallout,
    
    SdvmFunctionStackSegmentCount,
    SdvmFunctionStackSegmentFirstAfterPrologue = SdvmFunctionStackSegmentFloatCallPreservedRegister,
} sdvm_functionStackSegmentName_t;

typedef struct sdvm_compilerTarget_s sdvm_compilerTarget_t;
typedef struct sdvm_functionCompilationState_s sdvm_functionCompilationState_t;
typedef struct sdvm_compilerCallingConvention_s sdvm_compilerCallingConvention_t;
typedef struct sdvm_compilerInstruction_s sdvm_compilerInstruction_t;
typedef struct sdvm_compilerInstructionPattern_s sdvm_compilerInstructionPattern_t;

typedef struct sdvm_compilerSymbol_s
{
    uint32_t name;
    uint32_t section;
    uint32_t objectSymbolIndex;

    sdvm_compilerSymbolKind_t kind;
    sdvm_compilerSymbolBinding_t binding;
    uint8_t flags;
    uint8_t reserved;

    int64_t value;
    uint64_t size;
} sdvm_compilerSymbol_t;

#define SDVM_LINEAR_SCAN_MAX_AVAILABLE_REGISTERS 32

typedef uint32_t sdvm_compilerSymbolHandle_t;

typedef struct sdvm_compilerRelocation_s
{
    sdvm_compilerRelocationKind_t kind;
    sdvm_compilerSymbolHandle_t symbol;
    uint32_t offset;
    int64_t addend;
} sdvm_compilerRelocation_t;

typedef struct sdvm_compilerObjectSection_s
{
    uint32_t symbolIndex;
    uint32_t alignment;
    uint32_t flags;
    const char *name;
    const char *relSectionName;
    const char *relaSectionName;

    sdvm_dynarray_t contents;
    sdvm_dynarray_t relocations;
    sdvm_dynarray_t pendingLabelRelocations;
} sdvm_compilerObjectSection_t;

typedef struct sdvm_compilerLabel_s
{
    sdvm_compilerObjectSection_t *section;
    int64_t value;
} sdvm_compilerLabel_t;

typedef struct sdvm_compilerPendingLabelRelocation_s
{
    sdvm_compilerRelocationKind_t kind;
    uint32_t labelIndex;
    uint32_t offset;
    int64_t addend;
} sdvm_compilerPendingLabelRelocation_t;

typedef struct sdvm_compilerSymbolTable_s
{
    sdvm_dynarray_t strings;
    sdvm_dynarray_t symbols;
} sdvm_compilerSymbolTable_t;

typedef struct sdvm_compiler_s
{
    uint32_t pointerSize;
    const sdvm_compilerTarget_t *target;
    sdvm_compilerSymbolTable_t symbolTable;
    sdvm_dynarray_t labels;
    bool verbose;

    union {
        struct {
            sdvm_compilerObjectSection_t nullSection;
            sdvm_compilerObjectSection_t textSection;
            sdvm_compilerObjectSection_t rodataSection;
            sdvm_compilerObjectSection_t dataSection;
            sdvm_compilerObjectSection_t bssSection;

            sdvm_compilerObjectSection_t ehFrameSection;
            sdvm_compilerObjectSection_t debugAbbrevSection;
            sdvm_compilerObjectSection_t debugInfoSection;
            sdvm_compilerObjectSection_t debugLineSection;
            sdvm_compilerObjectSection_t debugStrSection;
        };

        sdvm_compilerObjectSection_t sections[SDVM_COMPILER_SECTION_COUNT];
    };
} sdvm_compiler_t;

typedef struct sdvm_compilerInstructionPatternTable_s
{
    bool isSorted;

    uint32_t patternCount;
    sdvm_compilerInstructionPattern_t *patterns;
} sdvm_compilerInstructionPatternTable_t;

struct sdvm_compilerTarget_s
{
    uint32_t pointerSize;
    sdvm_compilerObjectFileType_t objectFileType;
    uint32_t elfMachine;
    uint16_t coffMachine;
    bool usesUnderscorePrefix;
    bool hasSeparateFloatFromVectorRegisters;
    bool usesCET;

    const sdvm_compilerCallingConvention_t *defaultCC;
    const sdvm_compilerCallingConvention_t *cdecl;
    const sdvm_compilerCallingConvention_t *stdcall;
    const sdvm_compilerCallingConvention_t *apicall;
    const sdvm_compilerCallingConvention_t *thiscall;
    const sdvm_compilerCallingConvention_t *vectorcall;

    bool (*compileModuleFunction) (sdvm_functionCompilationState_t *state);
    uint32_t (*mapElfRelocation) (sdvm_compilerRelocationKind_t kind);
    uint16_t (*mapCoffRelocationApplyingAddend) (sdvm_compilerRelocation_t *relocation, uint8_t *target);

    sdvm_compilerInstructionPatternTable_t *instructionPatterns;
};

typedef struct sdvm_compilerObjectFile_s
{
    size_t size;
    uint8_t *data;
} sdvm_compilerObjectFile_t;

typedef struct sdvm_moduleCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_compilerSymbolHandle_t *importedValueTableSymbols;
    sdvm_compilerSymbolHandle_t *functionTableSymbols;
    sdvm_compilerSymbolHandle_t *exportedValueTableSymbols;

    sdvm_dwarf_cfi_builder_t cfi;
    sdvm_dwarf_debugInfo_builder_t dwarf;

    bool hasEmittedCIE;
    size_t startPC;
    size_t endPC;
} sdvm_moduleCompilationState_t;

typedef struct sdvm_compilerLiveInterval_s
{
    uint32_t firstUsage;
    uint32_t lastUsage;
    uint32_t start;
    uint32_t end;
} sdvm_compilerLiveInterval_t;

typedef uint8_t sdvm_compilerRegisterValue_t;

typedef struct sdvm_compilerRegister_s
{
    sdvm_compilerRegisterKind_t kind;
    uint8_t isPending : 1;
    uint8_t isDestroyed : 1;
    uint8_t size;
    sdvm_compilerRegisterValue_t value;
} sdvm_compilerRegister_t;

typedef struct sdvm_compilerStackLocation_s
{
    bool isValid;
    sdvm_compilerRegisterValue_t framePointerRegister;

    uint32_t size;
    uint32_t alignment;
    uint32_t segment;
    uint32_t segmentOffset;
    int32_t framePointerOffset;
} sdvm_compilerStackLocation_t;

typedef struct sdvm_compilerLocation_s
{
    sdvm_compilerLocationKind_t kind;
    uint8_t isSigned : 1;

    union {
        int32_t immediateS32;
        int64_t immediateS64;
        uint32_t immediateU32;
        uint64_t immediateU64;
        uint32_t immediateLabel;
        float immediateF32;
        double immediateF64;
        int64_t constantSectionOffset;

        struct {
            sdvm_compilerRegister_t firstRegister;
            sdvm_compilerRegister_t secondRegister;
        };

        struct {
            sdvm_compilerStackLocation_t firstStackLocation;
            sdvm_compilerStackLocation_t secondStackLocation;
        };

        struct {
            sdvm_compilerSymbolHandle_t symbolHandle;
            int64_t symbolOffset;
        };
    };
} sdvm_compilerLocation_t;

#define SDVM_REGISTER_SET_WORD_COUNT ((SDVM_LINEAR_SCAN_MAX_AVAILABLE_REGISTERS + 31) / 32)
typedef struct sdvm_registerSet_s
{
    uint32_t masks[SDVM_REGISTER_SET_WORD_COUNT];
} sdvm_registerSet_t;

typedef bool (*sdvm_compiler_instructionPatternPredicate_t)(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions);
typedef void (*sdvm_compiler_instructionPatternConstraints_t)(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions);
typedef bool (*sdvm_compiler_instructionPatternGenerator_t)(sdvm_functionCompilationState_t *state, uint32_t count, sdvm_compilerInstruction_t *instructions);

#define SDVM_INSTRUCTION_PATTERN_MAX_SIZE 8

typedef struct sdvm_compilerInstructionPattern_s
{
    uint32_t size;
    sdvm_opcode_t opcodes[SDVM_INSTRUCTION_PATTERN_MAX_SIZE];
    sdvm_compiler_instructionPatternPredicate_t predicate;
    sdvm_compiler_instructionPatternConstraints_t constraints; 
    sdvm_compiler_instructionPatternGenerator_t generator;
} sdvm_compilerInstructionPattern_t;

typedef struct sdvm_compilerInstructionClobberSets_s
{
    sdvm_registerSet_t integerSet;
    sdvm_registerSet_t floatSet;
    sdvm_registerSet_t vectorSet;
} sdvm_compilerInstructionClobberSets_t;

struct sdvm_compilerInstruction_s
{
    uint32_t index;
    sdvm_decodedConstOrInstruction_t decoding;
    sdvm_compilerLiveInterval_t liveInterval;
    const sdvm_compilerInstructionPattern_t *pattern;

    sdvm_compilerLocation_t location;
    sdvm_compilerLocation_t stackLocation;
    sdvm_compilerLocation_t destinationLocation;
    sdvm_compilerLocation_t arg0Location;
    sdvm_compilerLocation_t arg1Location;
    sdvm_compilerLocation_t scratchLocation0;
    sdvm_compilerLocation_t scratchLocation1;
    sdvm_compilerInstructionClobberSets_t clobberSets;

    uint8_t allowArg0DestinationShare : 1;
    uint8_t allowArg1DestinationShare : 1;
    uint8_t isBranchDestination : 1;
    uint8_t isBackwardBranchDestination : 1;
    uint8_t isIndirectBranchDestination : 1;
};

struct sdvm_compilerCallingConvention_s
{
    bool supportsLocalSymbolValueCall;
    bool supportsGlobalSymbolValueCall;
    bool anchorsFramePointerAtBottom;
    bool usesSingleRegisterCount;
    bool vectorsArePassedByPointers;
    uint32_t integerRegisterSize;
    uint32_t integerRegisterCount;

    uint32_t stackAlignment;
    uint32_t stackParameterAlignment;
    uint32_t calloutShadowSpace;

    const sdvm_compilerRegister_t **integer32Registers;
    const sdvm_compilerRegister_t **integer64Registers;
    const sdvm_compilerRegister_t **integerRegisters;

    const sdvm_compilerRegister_t *closureRegister;
    const sdvm_compilerRegister_t *closureGCRegister;

    const sdvm_compilerRegister_t *firstInteger32ResultRegister;
    const sdvm_compilerRegister_t *firstInteger64ResultRegister;
    const sdvm_compilerRegister_t *firstIntegerResultRegister;
    const sdvm_compilerRegister_t *secondInteger32ResultRegister;
    const sdvm_compilerRegister_t *secondInteger64ResultRegister;
    const sdvm_compilerRegister_t *secondIntegerResultRegister;

    uint32_t vectorRegisterSize;
    uint32_t vectorRegisterCount;
    const sdvm_compilerRegister_t **vectorFloatRegisters;
    const sdvm_compilerRegister_t **vectorIntegerRegisters;
 
    const sdvm_compilerRegister_t *firstVectorFloatResultRegister;
    const sdvm_compilerRegister_t *firstVectorIntegerResultRegister;
    const sdvm_compilerRegister_t *secondVectorFloatResultRegister;
    const sdvm_compilerRegister_t *secondVectorIntegerResultRegister;

    uint32_t allocatableIntegerRegisterCount;
    const sdvm_compilerRegisterValue_t *allocatableIntegerRegisters;

    uint32_t allocatableFloatRegisterCount;
    const sdvm_compilerRegisterValue_t *allocatableFloatRegisters;

    uint32_t allocatableVectorRegisterCount;
    const sdvm_compilerRegisterValue_t *allocatableVectorRegisters;

    uint32_t callPreservedIntegerRegisterCount;
    const sdvm_compilerRegisterValue_t *callPreservedIntegerRegisters;

    uint32_t callTouchedIntegerRegisterCount;
    const sdvm_compilerRegisterValue_t *callTouchedIntegerRegisters;

    uint32_t callPreservedFloatRegisterCount;
    const sdvm_compilerRegisterValue_t *callPreservedFloatRegisters;

    uint32_t callTouchedFloatRegisterCount;
    const sdvm_compilerRegisterValue_t *callTouchedFloatRegisters;

    uint32_t callPreservedVectorRegisterCount;
    const sdvm_compilerRegisterValue_t *callPreservedVectorRegisters;

    uint32_t callTouchedVectorRegisterCount;
    const sdvm_compilerRegisterValue_t *callTouchedVectorRegisters;
};

typedef struct sdvm_compilerCallingConventionState_s
{
    const sdvm_compilerCallingConvention_t *convention;

    bool isCallout;

    uint32_t argumentCount;
    uint32_t usedArgumentIntegerRegisterCount;
    uint32_t usedArgumentVectorRegisterCount;

    uint32_t usedCalloutSpace;
    uint32_t usedCalloutSpaceAlignment;
} sdvm_compilerCallingConventionState_t;

typedef struct sdvm_functionCompilationStackSegment_s
{
    uint32_t alignment;
    uint32_t size;
    int32_t startOffset;
    int32_t endOffset;
} sdvm_functionCompilationStackSegment_t;

struct sdvm_functionCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_moduleCompilationState_t *moduleState;
    sdvm_compilerSymbolHandle_t symbol;

    const sdvm_compilerCallingConvention_t *callingConvention;
    sdvm_compilerCallingConventionState_t callingConventionState;

    const sdvm_compilerCallingConvention_t *currentCallCallingConvention;
    sdvm_compilerCallingConventionState_t currentCallCallingConventionState;

    sdvm_constOrInstruction_t *sourceInstructions;
    uint32_t instructionCount;
    sdvm_compilerInstruction_t *instructions;

    sdvm_registerSet_t usedIntegerRegisterSet;
    sdvm_registerSet_t usedFloatRegisterSet;
    sdvm_registerSet_t usedVectorFloatRegisterSet;
    sdvm_registerSet_t usedVectorIntegerRegisterSet;

    sdvm_registerSet_t usedCallPreservedIntegerRegisterSet;
    sdvm_registerSet_t usedCallPreservedFloatRegisterSet;
    sdvm_registerSet_t usedCallPreservedVectorRegisterSet;

    union
    {
        struct
        {
            sdvm_functionCompilationStackSegment_t argumentPassingStackSegment;
            sdvm_functionCompilationStackSegment_t prologueStackSegment;
            sdvm_functionCompilationStackSegment_t floatCallPreservedRegisterStackSegment;
            sdvm_functionCompilationStackSegment_t vectorCallPreservedRegisterStackSegment;
            sdvm_functionCompilationStackSegment_t temporarySegment;
            sdvm_functionCompilationStackSegment_t calloutStackSegment;
        };

        sdvm_functionCompilationStackSegment_t stackSegments[SdvmFunctionStackSegmentCount];
    };

    bool hasCallout;
    bool requiresStackFrame;
    sdvm_compilerRegisterValue_t stackFrameRegister;
    uint32_t stackFramePointerAnchorOffset;
};

typedef struct sdvm_linearScanActiveInterval_s
{
    sdvm_compilerInstruction_t *instruction;
    sdvm_compilerRegisterValue_t registerValue;
    uint32_t start;
    uint32_t end;
} sdvm_linearScanActiveInterval_t;

typedef struct sdvm_linearScanRegisterAllocatorFile_s
{
    int32_t currentInstructionIndex;

    uint32_t allocatableRegisterCount;
    const sdvm_compilerRegisterValue_t *allocatableRegisters;

    uint32_t activeIntervalCount;
    sdvm_linearScanActiveInterval_t activeIntervals[SDVM_LINEAR_SCAN_MAX_AVAILABLE_REGISTERS];

    sdvm_registerSet_t allocatedRegisterSet;
    sdvm_registerSet_t activeRegisterSet;
    sdvm_registerSet_t usedRegisterSet;
} sdvm_linearScanRegisterAllocatorFile_t;

typedef struct sdvm_linearScanRegisterAllocator_s
{
    sdvm_compiler_t *compiler;

    union
    {
        struct
        {
            sdvm_linearScanRegisterAllocatorFile_t *integerRegisterFile;
            sdvm_linearScanRegisterAllocatorFile_t *floatRegisterFile;
            sdvm_linearScanRegisterAllocatorFile_t *vectorFloatRegisterFile;
            sdvm_linearScanRegisterAllocatorFile_t *vectorIntegerRegisterFile;
        };

        sdvm_linearScanRegisterAllocatorFile_t *registerFiles[SdvmCompRegisterKindCount];
    };

} sdvm_linearScanRegisterAllocator_t;

static inline size_t sdvm_compiler_alignSizeTo(size_t size, size_t alignment)
{
    return (size + alignment - 1) & (-alignment);
}

SDVM_API void sdvm_compilerSymbolTable_initialize(sdvm_compilerSymbolTable_t *symbolTable);
SDVM_API void sdvm_compilerSymbolTable_destroy(sdvm_compilerSymbolTable_t *symbolTable);
SDVM_API uint32_t sdvm_compilerSymbolTable_addName(sdvm_compilerSymbolTable_t *symbolTable, const char *name);
SDVM_API sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createSectionSymbol(sdvm_compilerSymbolTable_t *symbolTable, uint32_t sectionIndex);
SDVM_API sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createUndefinedSymbol(sdvm_compilerSymbolTable_t *symbolTable, const char *name, sdvm_compilerSymbolKind_t kind, sdvm_compilerSymbolBinding_t binding);
SDVM_API void sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolHandle_t symbolHandle, uint32_t sectionSymbolIndex, int64_t offset);
SDVM_API void sdvm_compilerSymbolTable_setSymbolSize(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolHandle_t symbolHandle, uint64_t size);

SDVM_API void sdvm_compilerObjectSection_initialize(sdvm_compilerObjectSection_t *section);
SDVM_API void sdvm_compilerObjectSection_destroy(sdvm_compilerObjectSection_t *section);

SDVM_API sdvm_compiler_t *sdvm_compiler_create(const sdvm_compilerTarget_t *target);
SDVM_API void sdvm_compiler_destroy(sdvm_compiler_t *compiler);

SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_getDefault(void);
SDVM_API const char *sdvm_compilerTarget_getDefaultTargetName(void);
SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_getNamed(const char *targetName);

SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_get_x64_linux(void);
SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_get_x64_windows(void);

SDVM_API void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module);
SDVM_API void sdvm_moduleCompilationState_destroy(sdvm_moduleCompilationState_t *state);

SDVM_API bool sdvm_compilerLiveInterval_hasUsage(sdvm_compilerLiveInterval_t *interval);

SDVM_API bool sdvm_compilerLocationKind_isRegister(sdvm_compilerLocationKind_t kind);
SDVM_API bool sdvm_compilerLocationKind_isImmediate(sdvm_compilerLocationKind_t kind);

SDVM_API void sdvm_compilerLocation_print(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *location);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_null(void);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_immediateLabel(uint32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_immediateS32(int32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_immediateU32(uint32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_immediateS64(int32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_immediateU64(uint32_t value);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionS32(sdvm_compiler_t *compiler, int32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionU32(sdvm_compiler_t *compiler, uint32_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionS64(sdvm_compiler_t *compiler, int64_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionU64(sdvm_compiler_t *compiler, uint64_t value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionF32(sdvm_compiler_t *compiler, float value);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_constSectionF64(sdvm_compiler_t *compiler, double value);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_signedGlobalSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_localSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle, int64_t offset);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_globalSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle, int64_t offset);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_integerRegister(uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_signedIntegerRegister(uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_floatRegister(uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_integerRegisterPair(uint8_t firstSize, uint8_t secondSize);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_vectorFloatRegister(uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_vectorFloatRegisterPair(uint8_t firstSize, uint8_t secondSize);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_vectorIntegerRegister(uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_vectorIntegerRegisterPair(uint8_t firstSize, uint8_t secondSize);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegister(sdvm_compilerRegister_t reg);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegisterWithSize(sdvm_compilerRegister_t reg, uint8_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificSignedRegister(sdvm_compilerRegister_t reg);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegisterPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stack(uint32_t size, uint32_t alignment);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stackAddress(uint32_t size, uint32_t alignment);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stackSignedInteger(uint32_t size);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stackPair(uint32_t firstSize, uint32_t firstAlignment, uint32_t secondSize, uint32_t secondAlignment);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_forOperandType(sdvm_compiler_t *compiler, sdvm_compilerInstruction_t *argument, sdvm_type_t type);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_spillForOperandType(sdvm_compiler_t *compiler, sdvm_type_t type);

SDVM_API bool sdvm_compilerLocation_isOnStack(const sdvm_compilerLocation_t *location);

SDVM_API void sdvm_functionCompilationState_computeLiveIntervals(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_destroy(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_dump(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_computeLabelLocations(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction);

SDVM_API void sdvm_compiler_allocateFunctionRegisters(sdvm_functionCompilationState_t *state, sdvm_linearScanRegisterAllocator_t *registerAllocator);
SDVM_API void sdvm_compiler_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_compiler_computeStackSegmentLayouts(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_compiler_computeStackFrameOffsets(sdvm_functionCompilationState_t *state);

SDVM_API uint32_t sdvm_compiler_makeLabel(sdvm_compiler_t *compiler);
SDVM_API void sdvm_compiler_setLabelValue(sdvm_compiler_t *compiler, uint32_t label, sdvm_compilerObjectSection_t *section, int64_t value);
SDVM_API void sdvm_compiler_setLabelAtSectionEnd(sdvm_compiler_t *compiler, uint32_t label, sdvm_compilerObjectSection_t *section);
SDVM_API void sdvm_compiler_applyPendingLabelRelocations(sdvm_compiler_t *compiler);

SDVM_API size_t sdvm_compiler_addInstructionBytes(sdvm_compiler_t *compiler, size_t instructionSize, const void *instruction);
SDVM_API size_t sdvm_compiler_addInstructionByte(sdvm_compiler_t *compiler, uint8_t byte);
SDVM_API void sdvm_compiler_addInstructionRelocation(sdvm_compiler_t *compiler, sdvm_compilerRelocationKind_t kind, sdvm_compilerSymbolHandle_t symbol, int64_t addend);
SDVM_API void sdvm_compiler_addInstructionLabelValueRelative32(sdvm_compiler_t *compiler, uint32_t labelIndex, int32_t addend);
SDVM_API size_t sdvm_compiler_getCurrentPC(sdvm_compiler_t *compiler);

SDVM_API bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module);
SDVM_API bool sdvm_compiler_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compileObjectFile_allocate(size_t size);
SDVM_API void sdvm_compileObjectFile_destroy(sdvm_compilerObjectFile_t *objectFile);
SDVM_API bool sdvm_compileObjectFile_saveToFileNamed(sdvm_compilerObjectFile_t *objectFile, const char *fileName);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compilerElf64_encode(sdvm_compiler_t *compiler);
SDVM_API bool sdvm_compilerElf64_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *elfFileName);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compilerElf32_encode(sdvm_compiler_t *compiler);
SDVM_API bool sdvm_compilerElf32_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *elfFileName);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compilerCoff_encode(sdvm_compiler_t *compiler);
SDVM_API bool sdvm_compilerCoff_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *elfFileName);

SDVM_API void sdvm_registerSet_clear(sdvm_registerSet_t *set);
SDVM_API bool sdvm_registerSet_includes(const sdvm_registerSet_t *set, uint8_t value);
SDVM_API void sdvm_registerSet_set(sdvm_registerSet_t *set, uint8_t value);
SDVM_API void sdvm_registerSet_unset(sdvm_registerSet_t *set, uint8_t value);
SDVM_API bool sdvm_registerSet_hasIntersection(const sdvm_registerSet_t *a, const sdvm_registerSet_t *b);
SDVM_API bool sdvm_registerSet_isEmpty(const sdvm_registerSet_t *set);

#endif //SDVM_COMPILER_H
