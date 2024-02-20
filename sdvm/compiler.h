#ifndef SDVM_COMPILER_H
#define SDVM_COMPILER_H

#include "common.h"
#include "dynarray.h"
#include "instruction.h"
#include <stdbool.h>

#define SDVM_COMPILER_SECTION_COUNT 4

typedef struct sdvm_module_s sdvm_module_t;

typedef enum sdvm_compilerSectionFlags_e
{
    SdvmCompSectionFlagNone = 0,
    SdvmCompSectionFlagWrite = 1<<0,
    SdvmCompSectionFlagRead = 1<<1,
    SdvmCompSectionFlagExec = 1<<2,
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
    SdvmCompRelocationRelative64,
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
} sdvm_compilerLocationKind_t;

typedef enum sdvm_compilerRegisterKind_e
{
    SdvmCompRegisterKindInteger = 0,
    SdvmCompRegisterKindVectorFloat,
    SdvmCompRegisterKindVectorInteger,
} sdvm_compilerRegisterKind_t;

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

typedef uint32_t sdvm_compilerSymbolHandle_t;

typedef struct sdvm_compilerRelocation_s
{
    sdvm_compilerRelocationKind_t kind;

    uint32_t symbol;
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
} sdvm_compilerObjectSection_t;

typedef struct sdvm_compilerSymbolTable_s
{
    sdvm_dynarray_t strings;
    sdvm_dynarray_t symbols;
} sdvm_compilerSymbolTable_t;

typedef struct sdvm_compiler_s
{
    uint32_t pointerSize;
    sdvm_compilerSymbolTable_t symbolTable;

    union {
        struct {
            sdvm_compilerObjectSection_t nullSection;
            sdvm_compilerObjectSection_t textSection;
            sdvm_compilerObjectSection_t rodataSection;
            sdvm_compilerObjectSection_t dataSection;
        };

        sdvm_compilerObjectSection_t sections[SDVM_COMPILER_SECTION_COUNT];
    };
} sdvm_compiler_t;

typedef struct sdvm_compilerObjectFile_s
{
    size_t size;
    uint8_t *data;
} sdvm_compilerObjectFile_t;

typedef struct sdvm_moduleCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_compilerSymbolHandle_t *functionTableSymbols;
} sdvm_moduleCompilationState_t;


typedef struct sdvm_compilerLiveInterval_s
{
    uint32_t index;
    uint32_t firstUsage;
    uint32_t lastUsage;
} sdvm_compilerLiveInterval_t;

typedef struct sdvm_compilerRegister_s
{
    sdvm_compilerRegisterKind_t kind;
    uint8_t isPending : 1;
    uint8_t size;
    uint8_t value;
} sdvm_compilerRegister_t;

typedef struct sdvm_compilerLocation_s
{
    sdvm_compilerLocationKind_t kind;
    union {
        int32_t immediateS32;
        int64_t immediateS64;
        uint32_t immediateU32;
        uint64_t immediateU64;
        float immediateF32;
        double immediateF64;
        int64_t constantSectionOffset;

        struct {
            sdvm_compilerRegister_t firstRegister;
            sdvm_compilerRegister_t secondRegister;
        };

        struct {
            int32_t firstStackOffset;
            int32_t secondStackOffset;
        };
    };
} sdvm_compilerLocation_t;

typedef struct sdvm_compilerInstruction_s
{
    int32_t index;
    sdvm_decodedConstOrInstruction_t decoding;
    sdvm_compilerLiveInterval_t liveInterval;

    sdvm_compilerLocation_t location;
    sdvm_compilerLocation_t destinationLocation;
    sdvm_compilerLocation_t arg0Location;
    sdvm_compilerLocation_t arg1Location;
    sdvm_compilerLocation_t scratchLocations;
} sdvm_compilerInstruction_t;

typedef struct sdvm_functionCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_moduleCompilationState_t *moduleState;

    sdvm_constOrInstruction_t *sourceInstructions;
    uint32_t instructionCount;
    sdvm_compilerInstruction_t *instructions;
} sdvm_functionCompilationState_t;

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

SDVM_API sdvm_compiler_t *sdvm_compiler_create(uint32_t pointerSize);
SDVM_API void sdvm_compiler_destroy(sdvm_compiler_t *compiler);

SDVM_API void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module);
SDVM_API void sdvm_moduleCompilationState_destroy(sdvm_moduleCompilationState_t *state);

SDVM_API bool sdvm_compilerLiveInterval_hasUsage(sdvm_compilerLiveInterval_t *interval);

SDVM_API void sdvm_compilerLocation_print(sdvm_compilerLocation_t *location);

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_null(void);
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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_register(sdvm_compilerRegister_t reg);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_registerPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegister(sdvm_compilerRegister_t reg);
SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegisterPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister);

SDVM_API void sdvm_functionCompilationState_computeLiveIntervals(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_destroy(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_dump(sdvm_functionCompilationState_t *state);
SDVM_API void sdvm_functionCompilationState_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction);

SDVM_API size_t sdvm_compiler_addInstructionBytes(sdvm_compiler_t *compiler, size_t instructionSize, const void *instruction);
SDVM_API size_t sdvm_compiler_addInstructionByte(sdvm_compiler_t *compiler, uint8_t byte);

SDVM_API bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compileObjectFile_allocate(size_t size);
SDVM_API void sdvm_compileObjectFile_destroy(sdvm_compilerObjectFile_t *objectFile);
SDVM_API bool sdvm_compileObjectFile_saveToFileNamed(sdvm_compilerObjectFile_t *objectFile, const char *fileName);

SDVM_API sdvm_compilerObjectFile_t *sdvm_compilerElf64_encode(sdvm_compiler_t *compiler);
SDVM_API bool sdvm_compilerElf64_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *elfFileName);

#endif //SDVM_COMPILER_H
