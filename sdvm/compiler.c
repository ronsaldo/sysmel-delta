#include "compiler.h"
#include "module.h"
#include "assert.h"
#include <stdlib.h>
#include <stdio.h>

bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state);

void sdvm_compilerSymbolTable_initialize(sdvm_compilerSymbolTable_t *symbolTable)
{
    sdvm_dynarray_initialize(&symbolTable->strings, 1, 4096);
    char nulChar = 0;
    sdvm_dynarray_add(&symbolTable->strings, &nulChar);

    sdvm_dynarray_initialize(&symbolTable->symbols, sizeof(sdvm_compilerSymbol_t), 4096);
}

void sdvm_compilerSymbolTable_destroy(sdvm_compilerSymbolTable_t *symbolTable)
{
    sdvm_dynarray_destroy(&symbolTable->strings);
    sdvm_dynarray_destroy(&symbolTable->symbols);
}

sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createSectionSymbol(sdvm_compilerSymbolTable_t *symbolTable, uint32_t sectionIndex)
{
    sdvm_compilerSymbol_t symbol = {
        .kind = SdvmCompSymbolKindSection,
        .binding = SdvmCompSymbolBindingLocal,
        .section = sectionIndex
    };

    return sdvm_dynarray_add(&symbolTable->symbols, &symbol);
}

uint32_t sdvm_compilerSymbolTable_addName(sdvm_compilerSymbolTable_t *symbolTable, const char *name)
{
    if(!name || !*name)
        return 0;

    uint32_t nameIndex = symbolTable->strings.size;
    size_t nameLength = strlen(name);
    sdvm_dynarray_addAll(&symbolTable->strings, nameLength + 1, name);
    return nameIndex;
}

sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createUndefinedSymbol(sdvm_compilerSymbolTable_t *symbolTable, const char *name, sdvm_compilerSymbolKind_t kind, sdvm_compilerSymbolBinding_t binding)
{
    sdvm_compilerSymbol_t symbol = {
        .name = sdvm_compilerSymbolTable_addName(symbolTable, name),
        .kind = kind,
        .binding = binding
    };

    return sdvm_dynarray_add(&symbolTable->symbols, &symbol);
}

void sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolHandle_t symbolHandle, uint32_t sectionSymbolIndex, int64_t offset)
{
    SDVM_ASSERT(0 < symbolHandle && symbolHandle <= symbolTable->symbols.size);
    sdvm_compilerSymbol_t *symbol = (sdvm_compilerSymbol_t*)symbolTable->symbols.data + symbolHandle - 1;
    symbol->section = sectionSymbolIndex;
    symbol->value = offset;
}

void sdvm_compilerSymbolTable_setSymbolSize(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolHandle_t symbolHandle, uint64_t size)
{
    SDVM_ASSERT(0 < symbolHandle && symbolHandle <= symbolTable->symbols.size);
    sdvm_compilerSymbol_t *symbol = (sdvm_compilerSymbol_t*)symbolTable->symbols.data + symbolHandle - 1;
    symbol->size = size;
}

void sdvm_compilerObjectSection_initialize(sdvm_compilerObjectSection_t *section)
{
    section->alignment = 1;
    sdvm_dynarray_initialize(&section->contents, 1, 4096);
    sdvm_dynarray_initialize(&section->relocations, sizeof(sdvm_compilerRelocation_t), 512);
}

void sdvm_compilerObjectSection_destroy(sdvm_compilerObjectSection_t *section)
{
    sdvm_dynarray_destroy(&section->contents);
    sdvm_dynarray_destroy(&section->relocations);
}

sdvm_compiler_t *sdvm_compiler_create(void)
{
    sdvm_compiler_t *compiler = calloc(1, sizeof(sdvm_compiler_t));
    sdvm_compilerSymbolTable_initialize(&compiler->symbolTable);

    sdvm_compilerObjectSection_initialize(&compiler->textSection);
    compiler->textSection.symbolIndex = sdvm_compilerSymbolTable_createSectionSymbol(&compiler->symbolTable, 1);
    compiler->textSection.flags = SdvmCompSectionFlagRead | SdvmCompSectionFlagExec;
    compiler->textSection.name = ".text";
    compiler->textSection.relSectionName = ".text.rel";
    compiler->textSection.relaSectionName = ".text.rela";

    sdvm_compilerObjectSection_initialize(&compiler->rodataSection);
    compiler->rodataSection.symbolIndex = sdvm_compilerSymbolTable_createSectionSymbol(&compiler->symbolTable, 2);
    compiler->rodataSection.flags = SdvmCompSectionFlagRead;
    compiler->rodataSection.name = ".rodata";
    compiler->rodataSection.relSectionName = ".rodata.rel";
    compiler->rodataSection.relaSectionName = ".rodata.rela";

    sdvm_compilerObjectSection_initialize(&compiler->dataSection);
    compiler->dataSection.symbolIndex = sdvm_compilerSymbolTable_createSectionSymbol(&compiler->symbolTable, 3);
    compiler->dataSection.flags = SdvmCompSectionFlagRead | SdvmCompSectionFlagWrite;
    compiler->dataSection.name = ".data";
    compiler->dataSection.relSectionName = ".data.rel";
    compiler->dataSection.relaSectionName = ".data.rela";

    return compiler;
}

void sdvm_compiler_destroy(sdvm_compiler_t *compiler)
{
    sdvm_compilerSymbolTable_destroy(&compiler->symbolTable);

    sdvm_compilerObjectSection_destroy(&compiler->textSection);
    sdvm_compilerObjectSection_destroy(&compiler->rodataSection);
    sdvm_compilerObjectSection_destroy(&compiler->dataSection);

    free(compiler);
}

void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    state->compiler = compiler;
    state->module = module;
    state->functionTableSymbols = calloc(module->functionTableSize, sizeof(sdvm_compilerSymbolHandle_t));
}

void sdvm_moduleCompilationState_destroy(sdvm_moduleCompilationState_t *state)
{
    free(state->functionTableSymbols);
}

void sdvm_functionCompilationState_destroy(sdvm_functionCompilationState_t *state)
{
    free(state->instructions);
}

static bool sdvm_compiler_compileModuleFunction(sdvm_moduleCompilationState_t *moduleState, sdvm_functionTableEntry_t *functionTableEntry)
{
    sdvm_functionCompilationState_t functionState = {
        .compiler = moduleState->compiler,
        .module = moduleState->module,
        .moduleState = moduleState,
        .sourceInstructions = (sdvm_constOrInstruction_t*)moduleState->module->textSectionData + functionTableEntry->textSectionOffset,
        .instructionCount = functionTableEntry->textSectionSize / sizeof(sdvm_constOrInstruction_t)
    };

    // Decode all of the instructions.
    functionState.instructions = calloc(functionState.instructionCount, sizeof(sdvm_compilerInstruction_t));
    for(uint32_t i = 0; i < functionState.instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = functionState.instructions + i;
        instruction->decoding = sdvm_instruction_decode(functionState.sourceInstructions[i]);
        instruction->index = UINT32_MAX;
        instruction->firstUsageIndex = UINT32_MAX;
        instruction->lastUsageIndex = 0;
    }

    // TODO: Compute the live ranges.

    // Ask the backend to compile the function.
    sdvm_compiler_x64_compileModuleFunction(&functionState);
    
    // Destroy the function compilation state.
    sdvm_functionCompilationState_destroy(&functionState);
    return true;
}

SDVM_API size_t sdvm_compiler_addInstruction(sdvm_compiler_t *compiler, size_t instructionSize, const void *instruction)
{
    return sdvm_dynarray_addAll(&compiler->textSection.contents, instructionSize, instruction);
}

bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    sdvm_moduleCompilationState_t state = {0};
    sdvm_moduleCompilationState_initialize(&state, compiler, module);

    // Declare the function symbols.
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        char functionName[32];
        sprintf(functionName, "module.fun%04d", (int)i);
        if(module->header->entryPoint && !module->header->entryPointClosure && module->header->entryPoint == i + 1)
            state.functionTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, "moduleEntry", SdvmCompSymbolKindFunction, SdvmCompSymbolBindingGlobal);
        else
            state.functionTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, functionName, SdvmCompSymbolKindFunction, SdvmCompSymbolBindingLocal);
    }

    // Compile the function symbols.
    bool hasSucceeded = true;
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        sdvm_functionTableEntry_t *functionTableEntry = module->functionTable + i;
        size_t startOffset = compiler->textSection.contents.size;
        sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&compiler->symbolTable, state.functionTableSymbols[i], compiler->textSection.symbolIndex, startOffset);
        if(!sdvm_compiler_compileModuleFunction(&state, functionTableEntry))
            hasSucceeded = false;

        size_t endOffset = compiler->textSection.contents.size;
        sdvm_compilerSymbolTable_setSymbolSize(&compiler->symbolTable, state.functionTableSymbols[i], endOffset - startOffset);
    }

    free(state.functionTableSymbols);

    return hasSucceeded;
}


SDVM_API sdvm_compilerObjectFile_t *sdvm_compileObjectFile_allocate(size_t size)
{
    sdvm_compilerObjectFile_t *objectFile = calloc(1, sizeof(sdvm_compilerObjectFile_t));
    objectFile->size = size;
    objectFile->data = calloc(1, size);
    return objectFile;
}

SDVM_API void sdvm_compileObjectFile_destroy(sdvm_compilerObjectFile_t *objectFile)
{
    free(objectFile->data);
    free(objectFile);
}

SDVM_API bool sdvm_compileObjectFile_saveToFileNamed(sdvm_compilerObjectFile_t *objectFile, const char *fileName)
{
    FILE *outFile = fopen(fileName, "wb");
    if(!outFile)
        return false;

    bool succeeded = fwrite(objectFile->data, objectFile->size, 1, outFile) == 1;
    fclose(outFile);
    
    return succeeded;
}
