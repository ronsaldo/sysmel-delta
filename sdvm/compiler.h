#ifndef SDVM_COMPILER_H
#define SDVM_COMPILER_H

#include "common.h"
#include "dynarray.h"
#include "instruction.h"
#include <stdbool.h>

#define SDVM_COMPILER_SECTION_COUNT 4

typedef struct sdvm_module_s sdvm_module_t;

typedef enum sdvm_compilerSymbolKind_e
{
    SdvmCompSymbolKindNull = 0,
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

typedef struct sdvm_compilerSymbol_s
{
    uint8_t kind;
    uint8_t binding;
    uint8_t flags;
    uint8_t reserved;
    uint32_t section;
    int64_t value;
} sdvm_compilerSymbol_t;

typedef uint32_t sdvm_compilerSymbolHandle_t;

typedef struct sdvm_compilerRelocation_s
{
    uint32_t symbol;
    uint32_t offset;
    int64_t addend;
} sdvm_compilerRelocation_t;

typedef struct sdvm_compilerObjectSection_s
{
    uint32_t symbolIndex;
    sdvm_dynarray_t contents;
    sdvm_dynarray_t relocations;
} sdvm_compilerObjectSection_t;

typedef struct sdvm_compilerSymbolTable_s
{
    sdvm_dynarray_t symbols;
} sdvm_compilerSymbolTable_t;

typedef struct sdvm_compiler_s
{
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

typedef struct sdvm_moduleCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_compilerSymbolHandle_t *functionTableSymbols;
} sdvm_moduleCompilationState_t;

typedef struct sdvm_functionCompilationState_s
{
    sdvm_compiler_t *compiler;
    sdvm_module_t *module;
    sdvm_moduleCompilationState_t *moduleState;

    sdvm_constOrInstruction_t *instructions;
    uint32_t instructionCount;
    sdvm_decodedConstOrInstruction_t *decodedInstructions;
} sdvm_functionCompilationState_t;

SDVM_API void sdvm_compilerSymbolTable_initialize(sdvm_compilerSymbolTable_t *symbolTable);
SDVM_API void sdvm_compilerSymbolTable_destroy(sdvm_compilerSymbolTable_t *symbolTable);
SDVM_API sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createSectionSymbol(sdvm_compilerSymbolTable_t *symbolTable, uint32_t sectionIndex);
SDVM_API sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createUndefinedSymbol(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolKind_t kind, sdvm_compilerSymbolBinding_t binding);
SDVM_API void sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolHandle_t symbolHandle, uint32_t sectionSymbolIndex, int64_t offset);

SDVM_API void sdvm_compilerObjectSection_initialize(sdvm_compilerObjectSection_t *section);
SDVM_API void sdvm_compilerObjectSection_destroy(sdvm_compilerObjectSection_t *section);

SDVM_API sdvm_compiler_t *sdvm_compiler_create(void);
SDVM_API void sdvm_compiler_destroy(sdvm_compiler_t *compiler);

SDVM_API void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module);
SDVM_API void sdvm_moduleCompilationState_destroy(sdvm_moduleCompilationState_t *state);

SDVM_API void sdvm_functionCompilationState_destroy(sdvm_functionCompilationState_t *state);

SDVM_API bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module);

#endif //SDVM_COMPILER_H