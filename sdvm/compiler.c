#include "compiler.h"
#include "module.h"
#include "assert.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

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

sdvm_compiler_t *sdvm_compiler_create(uint32_t pointerSize)
{
    sdvm_compiler_t *compiler = calloc(1, sizeof(sdvm_compiler_t));
    compiler->pointerSize = pointerSize;

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

static void sdvm_compilerLiveInterval_initialize(sdvm_compilerLiveInterval_t *interval, uint32_t index)
{
    interval->index = index;
    interval->firstUsage = UINT32_MAX;
    interval->lastUsage = 0;
}

static void sdvm_compilerLiveInterval_insertUsage(sdvm_compilerLiveInterval_t *interval, uint32_t usage)
{
    if(usage < interval->firstUsage)
        interval->firstUsage = usage;
    if(usage > interval->lastUsage)
        interval->lastUsage = usage;
}

bool sdvm_compilerLiveInterval_hasUsage(sdvm_compilerLiveInterval_t *interval)
{
    return interval->firstUsage <= interval->lastUsage;
}

void sdvm_functionCompilationState_computeLiveIntervals(sdvm_functionCompilationState_t *state)
{
    // Intialize the live intervals
    for(uint32_t i = 0; i < state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compilerLiveInterval_initialize(&instruction->liveInterval, i);
    }

    // Compute the live intervals.
    for(uint32_t i = 0; i < state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        if(instruction->decoding.isConstant)
            continue;

        if(instruction->decoding.arg0IsInstruction)
        {
            sdvm_compilerInstruction_t *arg0Instruction = state->instructions + instruction->decoding.instruction.arg0;
            sdvm_compilerLiveInterval_insertUsage(&arg0Instruction->liveInterval, i);
        }

        if(instruction->decoding.arg1IsInstruction)
        {
            sdvm_compilerInstruction_t *arg1Instruction = state->instructions + instruction->decoding.instruction.arg1;
            sdvm_compilerLiveInterval_insertUsage(&arg1Instruction->liveInterval, i);
        }
    }
}

void sdvm_compilerLocation_print(sdvm_compilerLocation_t *location)
{
    switch(location->kind)
    {
    case SdvmCompLocationNull:
        printf("null");
        return;
    case SdvmCompLocationImmediateS32:
        printf("imm-s32 %d", location->immediateS32);
        return;
    case SdvmCompLocationImmediateU32:
        printf("imm-u32 %u", location->immediateS32);
        return;
    case SdvmCompLocationImmediateS64:
        printf("imm-s64 %lld", (long long)location->immediateS64);
        return;
    case SdvmCompLocationImmediateU64:
        printf("imm-u64 %llu", (unsigned long long)location->immediateU64);
        return;
    case SdvmCompLocationImmediateF32:
        printf("imm-f32 %f", location->immediateF32);
        return;
    case SdvmCompLocationImmediateF64:
        printf("imm-f64 %f", location->immediateF32);
        return;
    case SdvmCompLocationImmediateLabel:
        printf("imm-label <>");
        return;
    case SdvmCompLocationConstantSection:
        printf("const-sec %lld", (long long)location->constantSectionOffset);
        return;
    case SdvmCompLocationRegister:
        printf("reg %d", location->firstRegister.value);
        return;
    case SdvmCompLocationRegisterPair:
        printf("reg %d:%d", location->firstRegister.value, location->secondRegister.value);
        return;
    case SdvmCompLocationStack:
        printf("stack %d", location->firstStackOffset);
        return;
    case SdvmCompLocationStackPair:
        printf("stack %d:%d", location->firstStackOffset, location->secondStackOffset);
        return;
    }
}
void sdvm_functionCompilationState_dump(sdvm_functionCompilationState_t *state)
{
    for(uint32_t i = 0; i < state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        
        // Is this a constant?
        if(instruction->decoding.isConstant)
        {
            printf("    $%d : %s @ ", i, sdvm_instruction_typeToString(instruction->decoding.destType));
            sdvm_compilerLocation_print(&instruction->location);
            printf(" := %s(%lld)", sdvm_instruction_fullOpcodeToString(instruction->decoding.opcode), (long long)instruction->decoding.constant.signedPayload);
        }
        else
        {
            printf("    $%d : %s @ ", i, sdvm_instruction_typeToString(instruction->decoding.destType));
            sdvm_compilerLocation_print(&instruction->location);

            printf(" := %s(%d : %s @ ",
                sdvm_instruction_fullOpcodeToString(instruction->decoding.opcode),
                instruction->decoding.instruction.arg0, sdvm_instruction_typeToString(instruction->decoding.instruction.arg0Type));
            sdvm_compilerLocation_print(&instruction->arg0Location);

            printf(", %d : %s @ ",
                instruction->decoding.instruction.arg1, sdvm_instruction_typeToString(instruction->decoding.instruction.arg1Type));
            sdvm_compilerLocation_print(&instruction->arg1Location);

            printf(") @ ");
            sdvm_compilerLocation_print(&instruction->destinationLocation);
        }

        if(sdvm_compilerLiveInterval_hasUsage(&instruction->liveInterval))
            printf(" usage [%u, %u]", instruction->liveInterval.firstUsage, instruction->liveInterval.lastUsage);
        else
            printf(" unused");
        
        printf("\n");
    }
}

sdvm_compilerLocation_t sdvm_compilerLocation_null(void)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationNull,
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateS32(int32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateS32,
        .immediateS32 = value
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateU32(uint32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateU32,
        .immediateS32 = value
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateS64(int32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateS32,
        .immediateS32 = value
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateU64(uint32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateU32,
        .immediateS32 = value
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionS32(sdvm_compiler_t *compiler, int32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 4, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionU32(sdvm_compiler_t *compiler, uint32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 4, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionS64(sdvm_compiler_t *compiler, int64_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 8, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionU64(sdvm_compiler_t *compiler, uint64_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 8, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionSignedPointer(sdvm_compiler_t *compiler, int64_t value)
{
    if(compiler->pointerSize == 4)
        return sdvm_compilerLocation_constSectionS32(compiler, (int32_t)value);
    else
        return sdvm_compilerLocation_constSectionS64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionUnsignedPointer(sdvm_compiler_t *compiler, int64_t value)
{
    if(compiler->pointerSize == 4)
        return sdvm_compilerLocation_constSectionU32(compiler, (uint32_t)value);
    else
        return sdvm_compilerLocation_constSectionU64(compiler, value);
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionF32(sdvm_compiler_t *compiler, float value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 4, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionF64(sdvm_compiler_t *compiler, double value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, 8, &value);
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_constSectionWithModuleData(sdvm_compiler_t *compiler, sdvm_module_t *module, size_t size, size_t offset)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationConstantSection,
        .constantSectionOffset = compiler->rodataSection.contents.size
    };

    sdvm_dynarray_addAll(&compiler->rodataSection.contents, size, module->constSectionData + offset);
    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_register(sdvm_compilerRegister_t reg)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .firstRegister = reg
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_registerPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .firstRegister = firstRegister,
        .secondRegister = secondRegister,
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegister(sdvm_compilerRegister_t reg)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .firstRegister = reg
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegisterPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .firstRegister = firstRegister,
        .secondRegister = secondRegister,
    };

    return location;
}

void sdvm_functionCompilationState_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_constSectionS32(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64SExt:
            instruction->location = sdvm_compilerLocation_constSectionS64(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
            instruction->location = sdvm_compilerLocation_constSectionU64(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64ConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(state->compiler, state->module, 8, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_constSectionSignedPointer(state->compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_constSectionUnsignedPointer(state->compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstPointerConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(state->compiler, state->module, state->compiler->pointerSize, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstGCPointerNull:
            instruction->location = sdvm_compilerLocation_null();
            break;
        case SdvmConstFloat32:
            {
                float value = 0;
                memcpy(&value, &instruction->decoding.constant.unsignedPayload, 4);
                instruction->location = sdvm_compilerLocation_constSectionF32(state->compiler, value);
            }
            break;
        case SdvmConstFloat64Small32:
            abort();
        case SdvmConstFloat64ConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(state->compiler, state->module, 8, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstLabel:
            abort();
        default:
            abort();
        }

        return;
    }
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
    }

    // Compute the live intervals.
    sdvm_functionCompilationState_computeLiveIntervals(&functionState);

    // Ask the backend to compile the function.
    sdvm_compiler_x64_compileModuleFunction(&functionState);
    
    // Destroy the function compilation state.
    sdvm_functionCompilationState_destroy(&functionState);
    return true;
}

SDVM_API size_t sdvm_compiler_addInstructionBytes(sdvm_compiler_t *compiler, size_t instructionSize, const void *instruction)
{
    return sdvm_dynarray_addAll(&compiler->textSection.contents, instructionSize, instruction);
}

SDVM_API size_t sdvm_compiler_addInstructionByte(sdvm_compiler_t *compiler, uint8_t byte)
{
    return sdvm_dynarray_add(&compiler->textSection.contents, &byte);
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
