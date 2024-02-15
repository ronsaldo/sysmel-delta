#include "compiler.h"
#include "module.h"
#include "assert.h"
#include <stdlib.h>

void sdvm_compilerSymbolTable_initialize(sdvm_compilerSymbolTable_t *symbolTable)
{
    sdvm_dynarray_initialize(&symbolTable->symbols, sizeof(sdvm_compilerSymbol_t), 4096);
}

void sdvm_compilerSymbolTable_destroy(sdvm_compilerSymbolTable_t *symbolTable)
{
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

sdvm_compilerSymbolHandle_t sdvm_compilerSymbolTable_createUndefinedSymbol(sdvm_compilerSymbolTable_t *symbolTable, sdvm_compilerSymbolKind_t kind, sdvm_compilerSymbolBinding_t binding)
{
    sdvm_compilerSymbol_t symbol = {
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

void sdvm_compilerObjectSection_initialize(sdvm_compilerObjectSection_t *section)
{
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

    sdvm_compilerObjectSection_initialize(&compiler->rodataSection);
    compiler->textSection.symbolIndex = sdvm_compilerSymbolTable_createSectionSymbol(&compiler->symbolTable, 2);

    sdvm_compilerObjectSection_initialize(&compiler->dataSection);
    compiler->textSection.symbolIndex = sdvm_compilerSymbolTable_createSectionSymbol(&compiler->symbolTable, 3);

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
    free(state->decodedInstructions);
}

static bool sdvm_compiler_compileModuleFunction(sdvm_moduleCompilationState_t *moduleState, sdvm_functionTableEntry_t *functionTableEntry)
{
    sdvm_functionCompilationState_t functionState = {
        .compiler = moduleState->compiler,
        .module = moduleState->module,
        .moduleState = moduleState,
        .instructions = (sdvm_constOrInstruction_t*)moduleState->module->textSectionData + functionTableEntry->textSectionOffset,
        .instructionCount = functionTableEntry->textSectionSize / sizeof(sdvm_constOrInstruction_t)
    };

    // Decode all of the instructions.
    functionState.decodedInstructions = calloc(functionState.instructionCount, sizeof(sdvm_decodedConstOrInstruction_t));
    for(uint32_t i = 0; i < functionState.instructionCount; ++i)
        functionState.decodedInstructions[i] = sdvm_instruction_decode(functionState.instructions[i]);

    // x86 ret
    uint8_t x86Ret[] = {0xc3};
    sdvm_dynarray_addAll(&functionState.compiler->textSection.contents, sizeof(x86Ret), x86Ret);
    
    return true;
}

bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    sdvm_moduleCompilationState_t state = {0};
    sdvm_moduleCompilationState_initialize(&state, compiler, module);

    // Declare the function symbols.
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        state.functionTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, SdvmCompSymbolKindFunction, SdvmCompSymbolBindingLocal);
    }

    // Compile the function symbols.
    bool hasSucceeded = true;
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        sdvm_functionTableEntry_t *functionTableEntry = module->functionTable + i;
        sdvm_compilerSymbolTable_setSymbolValueToSectionOffset(&compiler->symbolTable, state.functionTableSymbols[i], compiler->textSection.symbolIndex, compiler->textSection.contents.size);        
        if(!sdvm_compiler_compileModuleFunction(&state, functionTableEntry))
            hasSucceeded = false;
    }

    free(state.functionTableSymbols);

    return hasSucceeded;
}

