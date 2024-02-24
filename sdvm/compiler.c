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
    sdvm_dynarray_initialize(&compiler->labels, sizeof(sdvm_compilerLabel_t), 512);

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
    sdvm_dynarray_destroy(&compiler->labels);

    sdvm_compilerObjectSection_destroy(&compiler->textSection);
    sdvm_compilerObjectSection_destroy(&compiler->rodataSection);
    sdvm_compilerObjectSection_destroy(&compiler->dataSection);

    free(compiler);
}

void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    state->compiler = compiler;
    state->module = module;
    state->importedValueTableSymbols = calloc(module->functionTableSize, sizeof(sdvm_compilerSymbolHandle_t));
    state->functionTableSymbols = calloc(module->functionTableSize, sizeof(sdvm_compilerSymbolHandle_t));
    state->exportedValueTableSymbols = calloc(module->functionTableSize, sizeof(sdvm_compilerSymbolHandle_t));
}

void sdvm_moduleCompilationState_destroy(sdvm_moduleCompilationState_t *state)
{
    free(state->importedValueTableSymbols);
    free(state->functionTableSymbols);
    free(state->exportedValueTableSymbols);
}

void sdvm_functionCompilationState_destroy(sdvm_functionCompilationState_t *state)
{
    free(state->instructions);
}

static void sdvm_compilerLiveInterval_initialize(sdvm_compilerLiveInterval_t *interval, uint32_t index)
{
    interval->firstUsage = UINT32_MAX;
    interval->lastUsage = 0;
    interval->start = index;
    interval->end = index;
}

static void sdvm_compilerLiveInterval_insertUsage(sdvm_compilerLiveInterval_t *interval, uint32_t usage)
{
    if(usage < interval->firstUsage)
        interval->firstUsage = usage;
    if(usage < interval->start)
        interval->start = usage;
    if(usage > interval->lastUsage)
        interval->lastUsage = usage;
    if(usage > interval->end)
        interval->end = usage;
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

const char *sdvm_compiler_symbolHandleNameCString(sdvm_compiler_t *compiler, sdvm_compilerSymbolHandle_t handle)
{
    if(handle > 0 && handle <= compiler->symbolTable.symbols.size)
    {
        sdvm_compilerSymbol_t *symbol = (sdvm_compilerSymbol_t *)compiler->symbolTable.symbols.data + handle - 1;
        return (const char*)compiler->symbolTable.strings.data + symbol->name;
    }
    return "";
}

void sdvm_compilerLocation_print(sdvm_compiler_t *compiler, sdvm_compilerLocation_t *location)
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
    case SdvmCompLocationGlobalSymbolValue:
        printf("valueOf[%s]", sdvm_compiler_symbolHandleNameCString(compiler, location->symbolHandle));
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
            sdvm_compilerLocation_print(state->compiler, &instruction->location);
            printf(" := %s(%lld)", sdvm_instruction_fullOpcodeToString(instruction->decoding.opcode), (long long)instruction->decoding.constant.signedPayload);
        }
        else
        {
            printf("    $%d : %s @ ", i, sdvm_instruction_typeToString(instruction->decoding.destType));
            sdvm_compilerLocation_print(state->compiler, &instruction->location);

            printf(" := %s(%d : %s @ ",
                sdvm_instruction_fullOpcodeToString(instruction->decoding.opcode),
                instruction->decoding.instruction.arg0, sdvm_instruction_typeToString(instruction->decoding.instruction.arg0Type));
            sdvm_compilerLocation_print(state->compiler, &instruction->arg0Location);

            printf(", %d : %s @ ",
                instruction->decoding.instruction.arg1, sdvm_instruction_typeToString(instruction->decoding.instruction.arg1Type));
            sdvm_compilerLocation_print(state->compiler, &instruction->arg1Location);

            printf(") @ ");
            sdvm_compilerLocation_print(state->compiler, &instruction->destinationLocation);
        }

        printf(" live [%u, %u]", instruction->liveInterval.start, instruction->liveInterval.end);

        if(sdvm_compilerLiveInterval_hasUsage(&instruction->liveInterval))
            printf(" usage [%u, %u]", instruction->liveInterval.firstUsage, instruction->liveInterval.lastUsage);
        else
            printf(" unused");
        
        printf("\n");
    }
}

uint32_t sdvm_compiler_makeLabel(sdvm_compiler_t *compiler)
{
    sdvm_compilerLabel_t label = {0};
    uint32_t labelIndex = 0;
    sdvm_dynarray_add(&compiler->labels, &label);
    return labelIndex;
}

void sdvm_compiler_setLabelValue(sdvm_compiler_t *compiler, uint32_t labelIndex, sdvm_compilerObjectSection_t *section, int64_t value)
{
    SDVM_ASSERT(labelIndex < compiler->labels.size);
    sdvm_compilerLabel_t *label = (sdvm_compilerLabel_t *)compiler->labels.data + labelIndex;
    label->section = section;
    label->value = value;
}

void sdvm_compiler_setLabelAtSectionEnd(sdvm_compiler_t *compiler, uint32_t label, sdvm_compilerObjectSection_t *section)
{
    sdvm_compiler_setLabelValue(compiler, label, section, section->contents.size);
}

sdvm_compilerLocation_t sdvm_compilerLocation_null(void)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationNull,
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateLabel(uint32_t label)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateLabel,
        .immediateLabel = label
    };
    return location;
}

sdvm_compilerLocation_t sdvm_compilerLocation_immediateS32(int32_t value)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationImmediateS32,
        .isSigned = true,
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
        .isSigned = true,
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
        .isSigned = true,
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
        .isSigned = true,
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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_globalSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationGlobalSymbolValue,
        .symbolHandle = symbolHandle
    };

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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_integerRegister(uint8_t size)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .firstRegister = {
            .kind = SdvmCompRegisterKindInteger,
            .isPending = true,
            .size = size
        }
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_signedIntegerRegister(uint8_t size)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .isSigned = true,
        .firstRegister = {
            .kind = SdvmCompRegisterKindInteger,
            .isPending = true,
            .size = size
        }
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_integerRegisterPair(uint8_t firstSize, uint8_t secondSize)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegisterPair,
        .firstRegister = {
            .kind = SdvmCompRegisterKindInteger,
            .isPending = true,
            .size = firstSize
        },
        .secondRegister = {
            .kind = SdvmCompRegisterKindInteger,
            .isPending = true,
            .size = secondSize
        },
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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificSignedRegister(sdvm_compilerRegister_t reg)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegister,
        .isSigned = true,
        .firstRegister = reg
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_specificRegisterPair(sdvm_compilerRegister_t firstRegister, sdvm_compilerRegister_t secondRegister)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationRegisterPair,
        .firstRegister = firstRegister,
        .secondRegister = secondRegister,
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_forOperandType(sdvm_compiler_t *compiler, sdvm_type_t type)
{
    switch(type)
    {
    case SdvmTypeVoid:
    case SdvmTypeInfo:
        return sdvm_compilerLocation_null();

    case SdvmTypeInt8:
        return sdvm_compilerLocation_signedIntegerRegister(1);
    case SdvmTypeInt16:
        return sdvm_compilerLocation_signedIntegerRegister(2);
    case SdvmTypeInt32:
        return sdvm_compilerLocation_signedIntegerRegister(4);
    case SdvmTypeInt64:
        return sdvm_compilerLocation_signedIntegerRegister(8);

    case SdvmTypeUInt8:
        return sdvm_compilerLocation_integerRegister(1);
    case SdvmTypeUInt16:
        return sdvm_compilerLocation_integerRegister(2);
    case SdvmTypeUInt32:
        return sdvm_compilerLocation_integerRegister(4);
    case SdvmTypeUInt64:
        return sdvm_compilerLocation_integerRegister(8);

    case SdvmTypePointer:
    case SdvmTypeProcedureHandle:
    case SdvmTypeLabel:
        return sdvm_compilerLocation_integerRegister(compiler->pointerSize);

    case SdvmTypeGCPointer:
        return sdvm_compilerLocation_integerRegisterPair(compiler->pointerSize, compiler->pointerSize);

    default:
        abort();
    }
}

void sdvm_compilerCallingConventionState_reset(sdvm_compilerCallingConventionState_t *state, const sdvm_compilerCallingConvention_t *convention, uint32_t argumentCount, bool isCallout)
{
    state->convention = convention;

    state->isCallout = isCallout;

    state->argumentCount = argumentCount;
    state->usedArgumentIntegerRegisterCount = 0;
    state->usedArgumentVectorRegisterCount = 0;
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_memory(sdvm_compilerCallingConventionState_t *state, size_t valueSize, size_t valueAlignment)
{
    abort();
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_integer32(sdvm_compilerCallingConventionState_t *state)
{
    if(state->usedArgumentIntegerRegisterCount < state->convention->integerRegisterCount)
        return sdvm_compilerLocation_specificRegister(*state->convention->integer32Registers[state->usedArgumentIntegerRegisterCount++]);
    return sdvm_compilerCallingConventionState_memory(state, 4, 4);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_signedInteger32(sdvm_compilerCallingConventionState_t *state)
{
    sdvm_compilerLocation_t location = sdvm_compilerCallingConventionState_integer32(state);
    location.isSigned = true;
    return location;
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_integer64(sdvm_compilerCallingConventionState_t *state)
{
    if(state->convention->integerRegisterSize >= 8 && state->usedArgumentIntegerRegisterCount < state->convention->integerRegisterCount)
    {
        return sdvm_compilerLocation_specificRegister(*state->convention->integer64Registers[state->usedArgumentIntegerRegisterCount++]);
    }
    else if(state->convention->integerRegisterSize == 4 && state->usedArgumentIntegerRegisterCount + 1 < state->convention->integerRegisterCount)
    {
        sdvm_compilerLocation_t pairLocation = sdvm_compilerLocation_specificRegisterPair(*state->convention->integer32Registers[state->usedArgumentIntegerRegisterCount], *state->convention->integer32Registers[state->usedArgumentIntegerRegisterCount + 1]);
        state->usedArgumentIntegerRegisterCount += 2;
        return pairLocation;
    }

    return sdvm_compilerCallingConventionState_memory(state, 8, 8);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_pointer(sdvm_compilerCallingConventionState_t *state)
{
    if(state->usedArgumentIntegerRegisterCount < state->convention->integerRegisterCount)
        return sdvm_compilerLocation_specificRegister(*state->convention->integerRegisters[state->usedArgumentIntegerRegisterCount++]);
    return sdvm_compilerCallingConventionState_memory(state, state->convention->integerRegisterSize, state->convention->integerRegisterSize);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_pointerPair(sdvm_compilerCallingConventionState_t *state)
{
    if(state->usedArgumentIntegerRegisterCount + 1 < state->convention->integerRegisterCount)
    {
        sdvm_compilerLocation_t pairLocation = sdvm_compilerLocation_specificRegisterPair(*state->convention->integerRegisters[state->usedArgumentIntegerRegisterCount], *state->convention->integerRegisters[state->usedArgumentIntegerRegisterCount + 1]);
        state->usedArgumentIntegerRegisterCount += 2;
        return pairLocation;
    }

    return sdvm_compilerCallingConventionState_memory(state, state->convention->integerRegisterSize, state->convention->integerRegisterSize);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_calledFunction(sdvm_functionCompilationState_t *functionState, sdvm_compilerCallingConventionState_t *state)
{
    (void)functionState;
    return sdvm_compilerLocation_integerRegister(state->convention->integerRegisterSize);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_calledClosure(sdvm_functionCompilationState_t *functionState, sdvm_compilerCallingConventionState_t *state)
{
    (void)functionState;
    return sdvm_compilerLocation_specificRegisterPair(*state->convention->closureRegister, *state->convention->closureGCRegister);
}

void sdvm_functionCompilationState_computeInstructionLocationConstraints(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    sdvm_compiler_t *compiler = state->compiler;

    if(instruction->decoding.isConstant)
    {
        switch(instruction->decoding.opcode)
        {
        case SdvmConstInt32:
            instruction->location = sdvm_compilerLocation_constSectionS32(compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64SExt:
            instruction->location = sdvm_compilerLocation_constSectionS64(compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstInt64ZExt:
            instruction->location = sdvm_compilerLocation_constSectionU64(compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstInt64ConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(compiler, state->module, 8, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstPointerSExt:
            instruction->location = sdvm_compilerLocation_constSectionSignedPointer(compiler, instruction->decoding.constant.signedPayload);
            break;
        case SdvmConstPointerZExt:
            instruction->location = sdvm_compilerLocation_constSectionUnsignedPointer(compiler, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstPointerConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(compiler, state->module, compiler->pointerSize, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstFloat32:
            {
                float value = 0;
                memcpy(&value, &instruction->decoding.constant.unsignedPayload, 4);
                instruction->location = sdvm_compilerLocation_constSectionF32(compiler, value);
            }
            break;
        case SdvmConstFloat64Small:
            abort();
        case SdvmConstFloat64ConstSection:
            instruction->location = sdvm_compilerLocation_constSectionWithModuleData(compiler, state->module, 8, instruction->decoding.constant.unsignedPayload);
            break;
        case SdvmConstLabel:
            instruction->location = sdvm_compilerLocation_immediateLabel(sdvm_compiler_makeLabel(compiler));
            break;
        case SdvmConstImportPointer:
            {
                uint32_t importValueIndex = instruction->decoding.constant.unsignedPayload;
                SDVM_ASSERT(importValueIndex <= state->module->importTableSize);
                if(importValueIndex > 0)
                {
                    sdvm_compilerSymbolHandle_t symbolHandle = state->moduleState->importedValueTableSymbols[importValueIndex - 1];
                    instruction->location = sdvm_compilerLocation_globalSymbolValue(symbolHandle);
                }
                else
                {
                    instruction->location = sdvm_compilerLocation_null();
                }
            }
            break;
        default:
            abort();
        }

        return;
    }

    switch(instruction->decoding.opcode)
    {
    case SdvmInstBeginArguments:
        sdvm_compilerCallingConventionState_reset(&state->callingConventionState, state->callingConvention, instruction->decoding.instruction.arg0, false);
        return;
    case SdvmInstBeginCall:
        sdvm_compilerCallingConventionState_reset(&state->currentCallCallingConventionState, state->currentCallCallingConvention, instruction->decoding.instruction.arg0, true);
        return;

#pragma region ArgumentConstraints
    case SdvmInstArgInt8:
    case SdvmInstArgInt16:
    case SdvmInstArgInt32:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_signedInteger32(&state->callingConventionState);
        return;
    case SdvmInstArgUInt8:
    case SdvmInstArgUInt16:
    case SdvmInstArgUInt32:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_integer32(&state->callingConventionState);
        return;
    case SdvmInstArgInt64:
    case SdvmInstArgUInt64:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_integer64(&state->callingConventionState);
        return;
    case SdvmInstArgPointer:
    case SdvmInstArgProcedureHandle:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_pointer(&state->callingConventionState);
        return;
    case SdvmInstArgGCPointer:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_pointerPair(&state->callingConventionState);
        return;
#pragma endregion ArgumentConstraints

#pragma region CallArgumentConstraints
    case SdvmInstCallArgInt8:
    case SdvmInstCallArgInt16:
    case SdvmInstCallArgInt32:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_signedInteger32(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgUInt8:
    case SdvmInstCallArgUInt16:
    case SdvmInstCallArgUInt32:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_integer32(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgInt64:
    case SdvmInstCallArgUInt64:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_integer64(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgPointer:
    case SdvmInstCallArgProcedureHandle:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_pointer(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgGCPointer:
        instruction->destinationLocation = sdvm_compilerCallingConventionState_pointerPair(&state->currentCallCallingConventionState);
        return;
#pragma endregion CallArgumentConstraints

#pragma region ReturnConstraints
    case SdvmInstReturnInt8:
    case SdvmInstReturnInt16:
    case SdvmInstReturnInt32:
        instruction->arg0Location = sdvm_compilerLocation_specificSignedRegister(*state->callingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstReturnInt64:
    case SdvmInstReturnUInt64:
        if(state->callingConvention->integerRegisterSize >= 8)
            instruction->arg0Location = sdvm_compilerLocation_specificRegister(*state->callingConvention->firstInteger64ResultRegister);
        else
            instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(*state->callingConvention->firstInteger32ResultRegister, *state->callingConvention->secondInteger32ResultRegister);
        return;

    case SdvmInstReturnUInt8:
    case SdvmInstReturnUInt16:
    case SdvmInstReturnUInt32:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(*state->callingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstReturnPointer:
    case SdvmInstReturnProcedureHandle:
        instruction->arg0Location = sdvm_compilerLocation_specificRegister(*state->callingConvention->firstIntegerResultRegister);
        return;

    case SdvmInstReturnGCPointer:
        instruction->arg0Location = sdvm_compilerLocation_specificRegisterPair(*state->callingConvention->firstIntegerResultRegister, *state->callingConvention->secondIntegerResultRegister);
        return;

#pragma endregion ReturnConstraints

#pragma region CallConstraints
    case SdvmInstCallVoid:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        return;

    case SdvmInstCallInt8:
    case SdvmInstCallInt16:
    case SdvmInstCallInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificSignedRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstCallInt64:
    case SdvmInstCallUInt64:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        if(state->callingConvention->integerRegisterSize >= 8)
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger64ResultRegister);
        else
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstInteger32ResultRegister, *state->currentCallCallingConvention->secondInteger32ResultRegister);
        return;

    case SdvmInstCallUInt8:
    case SdvmInstCallUInt16:
    case SdvmInstCallUInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstCallPointer:
    case SdvmInstCallProcedureHandle:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstIntegerResultRegister);
        return;

    case SdvmInstCallGCPointer:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstIntegerResultRegister, *state->currentCallCallingConvention->secondIntegerResultRegister);
        return;
#pragma endregion CallConstraints

#pragma region CallClosureConstraints
    case SdvmInstCallClosureVoid:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        return;

    case SdvmInstCallClosureInt8:
    case SdvmInstCallClosureInt16:
    case SdvmInstCallClosureInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificSignedRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstCallClosureInt64:
    case SdvmInstCallClosureUInt64:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->closureRegister, *state->currentCallCallingConvention->closureGCRegister);
        if(state->callingConvention->integerRegisterSize >= 8)
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger64ResultRegister);
        else
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstInteger32ResultRegister, *state->currentCallCallingConvention->secondInteger32ResultRegister);
        return;

    case SdvmInstCallClosureUInt8:
    case SdvmInstCallClosureUInt16:
    case SdvmInstCallClosureUInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        return;

    case SdvmInstCallClosurePointer:
    case SdvmInstCallClosureProcedureHandle:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstIntegerResultRegister);
        return;

    case SdvmInstCallClosureGCPointer:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstIntegerResultRegister, *state->currentCallCallingConvention->secondIntegerResultRegister);
        return;
#pragma endregion CallClosureConstraints

    default:
        if(instruction->decoding.arg0IsInstruction)
            instruction->arg0Location = sdvm_compilerLocation_forOperandType(compiler, instruction->decoding.instruction.arg0Type);

        if(instruction->decoding.arg1IsInstruction)
            instruction->arg1Location = sdvm_compilerLocation_forOperandType(compiler, instruction->decoding.instruction.arg1Type);

        instruction->destinationLocation = sdvm_compilerLocation_forOperandType(compiler, instruction->decoding.destType);
        return;
    }
}

void sdvm_registerSet_clear(sdvm_registerSet_t *set)
{
    memset(set->masks, 0, sizeof(set->masks));
}

bool sdvm_registerSet_includes(sdvm_registerSet_t *set, uint8_t value)
{
    uint8_t wordIndex = value / 32;
    uint8_t bitIndex = value % 32;
    return set->masks[wordIndex] & (1<<bitIndex);
}

void sdvm_registerSet_set(sdvm_registerSet_t *set, uint8_t value)
{
    uint8_t wordIndex = value / 32;
    uint8_t bitIndex = value % 32;
    set->masks[wordIndex] |= (1<<bitIndex);
}

void sdvm_registerSet_unset(sdvm_registerSet_t *set, uint8_t value)
{
    uint8_t wordIndex = value / 32;
    uint8_t bitIndex = value % 32;
    set->masks[wordIndex] &= ~(1<<bitIndex);
}

bool sdvm_compilerLocationKind_isImmediate(sdvm_compilerLocationKind_t kind)
{
    switch(kind)
    {
    case SdvmCompLocationImmediateS32:
    case SdvmCompLocationImmediateU32:
    case SdvmCompLocationImmediateS64:
    case SdvmCompLocationImmediateU64:
    case SdvmCompLocationImmediateF32:
    case SdvmCompLocationImmediateF64:
    case SdvmCompLocationImmediateLabel:
        return true;
    default:
        return false;
    }
}

bool sdvm_compilerLocationKind_isRegister(sdvm_compilerLocationKind_t kind)
{
    return kind == SdvmCompLocationRegister || kind == SdvmCompLocationRegisterPair;
}

void sdvm_linearScanRegisterAllocatorFile_addAllocatedInterval(sdvm_linearScanRegisterAllocatorFile_t *registerFile, sdvm_compilerInstruction_t *instruction, uint8_t registerValue)
{
    sdvm_linearScanActiveInterval_t interval = {
        .instruction = instruction,
        .registerValue = registerValue,
        .start = instruction->liveInterval.start,
        .end = instruction->liveInterval.end,
    };

    SDVM_ASSERT(registerFile->activeIntervalCount < SDVM_LINEAR_SCAN_MAX_AVAILABLE_REGISTERS);
    SDVM_ASSERT(registerFile->activeIntervalCount < registerFile->allocatableRegisterCount);
    uint32_t destIndex = registerFile->activeIntervalCount++;

    // Sort the intervals by increasing end point.
    while(destIndex > 0 && registerFile->activeIntervals[destIndex].end > interval.end)
    {
        registerFile->activeIntervals[destIndex] = registerFile->activeIntervals[destIndex - 1];
        --destIndex;
    }
    registerFile->activeIntervals[destIndex] = interval;

    // Mark the register as allocated.
    sdvm_registerSet_set(&registerFile->allocatedRegisterSet, registerValue);
}

void sdvm_linearScanRegisterAllocatorFile_expireIntervalsUntil(sdvm_linearScanRegisterAllocatorFile_t *registerFile, uint32_t index)
{
    uint32_t destIndex = 0;
    for(uint32_t i = 0; i < registerFile->activeIntervalCount; ++i)
    {
        sdvm_linearScanActiveInterval_t *interval = registerFile->activeIntervals + i;
        if(interval->end < index || (interval->instruction && !sdvm_compilerLocationKind_isRegister(interval->instruction->location.kind)))
            sdvm_registerSet_unset(&registerFile->allocatedRegisterSet, interval->registerValue);
        else
            registerFile->activeIntervals[destIndex++] = *interval;
    }

    registerFile->activeIntervalCount = destIndex;
}

void sdvm_linearScanRegisterAllocatorFile_beginInstruction(sdvm_linearScanRegisterAllocatorFile_t *registerFile, sdvm_compilerInstruction_t *instruction)
{
    if(!registerFile)
        return;

    sdvm_linearScanRegisterAllocatorFile_expireIntervalsUntil(registerFile, instruction->index);
    sdvm_registerSet_clear(&registerFile->activeRegisterSet);
}

void sdvm_linearScanRegisterAllocator_beginInstruction(sdvm_linearScanRegisterAllocator_t *registerAllocator, sdvm_compilerInstruction_t *instruction)
{
    for(int i = 0; i < SdvmCompRegisterKindCount; ++i)
        sdvm_linearScanRegisterAllocatorFile_beginInstruction(registerAllocator->registerFiles[i], instruction);
}

void sdvm_linearScanRegisterAllocatorFile_ensureRegisterIsActive(sdvm_linearScanRegisterAllocatorFile_t *registerFile, uint8_t registerValue)
{
    sdvm_registerSet_set(&registerFile->activeRegisterSet, registerValue);
    sdvm_registerSet_set(&registerFile->usedRegisterSet, registerValue);
}

void sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(sdvm_linearScanRegisterAllocatorFile_t *registerFile, uint8_t registerValue)
{
    if(sdvm_registerSet_includes(&registerFile->allocatedRegisterSet, registerValue))
    {
        // TODO: spill the register
        abort();
    }

    sdvm_registerSet_set(&registerFile->activeRegisterSet, registerValue);
    sdvm_registerSet_set(&registerFile->usedRegisterSet, registerValue);
}

uint8_t sdvm_linearScanRegisterAllocatorFile_allocate(sdvm_linearScanRegisterAllocatorFile_t *registerFile)
{
    // Find an available allocatable register.
    for(uint32_t i = 0; i < registerFile->allocatableRegisterCount; ++i)
    {
        uint8_t registerValue = registerFile->allocatableRegisters[i];
        if(!sdvm_registerSet_includes(&registerFile->allocatedRegisterSet, registerValue) &&
           !sdvm_registerSet_includes(&registerFile->activeRegisterSet, registerValue))
        
        {
            sdvm_registerSet_set(&registerFile->activeRegisterSet, registerValue);
            sdvm_registerSet_set(&registerFile->usedRegisterSet, registerValue);
            return registerValue;
        }
    }

    SDVM_ASSERT(registerFile->activeIntervalCount > 0);
    // TODO: Expire an available register.
    abort();
}

void sdvm_linearScanRegisterAllocatorFile_endInstruction(sdvm_linearScanRegisterAllocatorFile_t *registerFile)
{
    if(!registerFile)
        return;

    sdvm_registerSet_clear(&registerFile->activeRegisterSet);
}

void sdvm_linearScanRegisterAllocator_endInstruction(sdvm_linearScanRegisterAllocator_t *registerAllocator, sdvm_compilerInstruction_t *instruction)
{
    for(int i = 0; i < SdvmCompRegisterKindCount; ++i)
        sdvm_linearScanRegisterAllocatorFile_endInstruction(registerAllocator->registerFiles[i]);

    instruction->location = instruction->destinationLocation;
    if(!sdvm_compilerLocationKind_isRegister(instruction->location.kind))
        return;

    sdvm_linearScanRegisterAllocatorFile_addAllocatedInterval(registerAllocator->registerFiles[instruction->location.firstRegister.kind], instruction, instruction->location.firstRegister.value);
    if(instruction->location.kind == SdvmCompLocationRegisterPair)
        sdvm_linearScanRegisterAllocatorFile_addAllocatedInterval(registerAllocator->registerFiles[instruction->location.secondRegister.kind], instruction, instruction->location.secondRegister.value);
}

void sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(sdvm_linearScanRegisterAllocator_t *registerAllocator, sdvm_compilerInstruction_t *instruction, sdvm_compilerLocation_t *location, sdvm_compilerInstruction_t *sourceInstruction)
{
    if(!sdvm_compilerLocationKind_isRegister(location->kind))
        return;
    
    if(!location->firstRegister.isPending)
    {
        if(sourceInstruction
            && sdvm_compilerLocationKind_isRegister(sourceInstruction->location.kind)
            && !sourceInstruction->location.firstRegister.isPending
            && (!location->firstRegister.isDestroyed || sourceInstruction->liveInterval.lastUsage <= (uint32_t)instruction->index)
            && location->firstRegister.kind == sourceInstruction->location.firstRegister.kind
            && location->firstRegister.value == sourceInstruction->location.firstRegister.value)
            sdvm_linearScanRegisterAllocatorFile_ensureRegisterIsActive(registerAllocator->registerFiles[location->firstRegister.kind], sourceInstruction->location.firstRegister.value);
        else
            sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(registerAllocator->registerFiles[location->firstRegister.kind], location->firstRegister.value);
    }

    if(location->kind == SdvmCompLocationRegisterPair && !location->secondRegister.isPending)
    {
        if(sourceInstruction && sourceInstruction->location.kind == SdvmCompLocationRegisterPair
            && !sourceInstruction->location.secondRegister.isPending
            && (!location->secondRegister.isDestroyed || sourceInstruction->liveInterval.lastUsage <= (uint32_t)instruction->index)
            && location->secondRegister.kind == sourceInstruction->location.secondRegister.kind
            && location->secondRegister.value == sourceInstruction->location.secondRegister.value)
            sdvm_linearScanRegisterAllocatorFile_ensureRegisterIsActive(registerAllocator->registerFiles[location->secondRegister.kind], sourceInstruction->location.secondRegister.value);
        else
            sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(registerAllocator->registerFiles[location->secondRegister.kind], location->secondRegister.value);
    }
}

void sdvm_linearScanRegisterAllocator_allocateRegisterLocation(sdvm_linearScanRegisterAllocator_t *registerAllocator, sdvm_compilerInstruction_t *instruction, sdvm_compilerLocation_t *location, sdvm_compilerInstruction_t *sourceInstruction)
{
    if(!sdvm_compilerLocationKind_isRegister(location->kind))
        return;

    if(location->firstRegister.isPending)
    {
        if(sourceInstruction
            && sdvm_compilerLocationKind_isRegister(sourceInstruction->location.kind)
            && !sourceInstruction->location.firstRegister.isPending
            && (!location->firstRegister.isDestroyed || sourceInstruction->liveInterval.lastUsage <= (uint32_t)instruction->index)
            && location->firstRegister.kind == sourceInstruction->location.firstRegister.kind)
        {
            sdvm_linearScanRegisterAllocatorFile_ensureRegisterIsActive(registerAllocator->registerFiles[location->firstRegister.kind], sourceInstruction->location.firstRegister.value);
            location->firstRegister.value = sourceInstruction->location.firstRegister.value;
        }
        else
        {
            location->firstRegister.value = sdvm_linearScanRegisterAllocatorFile_allocate(registerAllocator->registerFiles[location->firstRegister.kind]);
        }
        
        location->firstRegister.isPending = false;
    }

    if(location->kind == SdvmCompLocationRegisterPair && location->secondRegister.isPending)
    {
        if(sourceInstruction
            && sourceInstruction->location.kind == SdvmCompLocationRegisterPair
            && !location->secondRegister.isPending
            && (!location->secondRegister.isDestroyed || sourceInstruction->liveInterval.lastUsage <= (uint32_t)instruction->index)
            && location->secondRegister.kind == sourceInstruction->location.secondRegister.kind)
        {
            sdvm_linearScanRegisterAllocatorFile_ensureRegisterIsActive(registerAllocator->registerFiles[location->secondRegister.kind], sourceInstruction->location.secondRegister.value);
            location->secondRegister.value = sourceInstruction->location.secondRegister.value;
        }
        else
        {
            location->secondRegister.value = sdvm_linearScanRegisterAllocatorFile_allocate(registerAllocator->registerFiles[location->secondRegister.kind]);
        }
        
        location->secondRegister.isPending = false;
    }
}

void sdvm_compiler_allocateInstructionRegisters(sdvm_functionCompilationState_t *state, sdvm_linearScanRegisterAllocator_t *registerAllocator, sdvm_compilerInstruction_t *instruction)
{
    if(instruction->decoding.isConstant)
        return;

    sdvm_linearScanRegisterAllocator_beginInstruction(registerAllocator, instruction);

    // Allocate the specific registers.
    if(instruction->decoding.arg0IsInstruction)
    {
        sdvm_compilerInstruction_t *arg0 = state->instructions + instruction->decoding.instruction.arg0;
        sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(registerAllocator, instruction, &instruction->arg0Location, arg0);
    }

    if(instruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + instruction->decoding.instruction.arg1;
        sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(registerAllocator, instruction, &instruction->arg1Location, arg1);
    }
    sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(registerAllocator, instruction, &instruction->destinationLocation, instruction);
    sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(registerAllocator, instruction, &instruction->scratchLocation0, NULL);
    sdvm_linearScanRegisterAllocator_allocateSpecificRegisterLocation(registerAllocator, instruction, &instruction->scratchLocation1, NULL);

    // Allocate the non-specific registers.
    if(instruction->decoding.arg0IsInstruction)
    {
        sdvm_compilerInstruction_t *arg0 = state->instructions + instruction->decoding.instruction.arg0;
        sdvm_linearScanRegisterAllocator_allocateRegisterLocation(registerAllocator, instruction, &instruction->arg0Location, arg0);
    }

    if(instruction->decoding.arg1IsInstruction)
    {
        sdvm_compilerInstruction_t *arg1 = state->instructions + instruction->decoding.instruction.arg1;
        sdvm_linearScanRegisterAllocator_allocateRegisterLocation(registerAllocator, instruction, &instruction->arg1Location, arg1);
    }
    sdvm_linearScanRegisterAllocator_allocateRegisterLocation(registerAllocator, instruction, &instruction->destinationLocation, instruction);
    sdvm_linearScanRegisterAllocator_allocateRegisterLocation(registerAllocator, instruction, &instruction->scratchLocation0, NULL);
    sdvm_linearScanRegisterAllocator_allocateRegisterLocation(registerAllocator, instruction, &instruction->scratchLocation1, NULL);

    sdvm_linearScanRegisterAllocator_endInstruction(registerAllocator, instruction);
}

void sdvm_compiler_allocateFunctionRegisters(sdvm_functionCompilationState_t *state, sdvm_linearScanRegisterAllocator_t *registerAllocator)
{
    for(uint32_t i = 0; i <state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_allocateInstructionRegisters(state, registerAllocator, instruction);
    }
}

static bool sdvm_compiler_compileModuleFunction(sdvm_moduleCompilationState_t *moduleState, sdvm_moduleFunctionTableEntry_t *functionTableEntry)
{
    sdvm_functionCompilationState_t functionState = {
        .compiler = moduleState->compiler,
        .module = moduleState->module,
        .moduleState = moduleState,
        .sourceInstructions = (sdvm_constOrInstruction_t*)(moduleState->module->textSectionData + functionTableEntry->textSectionOffset),
        .instructionCount = functionTableEntry->textSectionSize / sizeof(sdvm_constOrInstruction_t)
    };

    // Decode all of the instructions.
    functionState.instructions = calloc(functionState.instructionCount, sizeof(sdvm_compilerInstruction_t));
    for(uint32_t i = 0; i < functionState.instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = functionState.instructions + i;
        instruction->index = i;
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

SDVM_API void sdvm_compiler_addInstructionRelocation(sdvm_compiler_t *compiler, sdvm_compilerRelocationKind_t kind, sdvm_compilerSymbolHandle_t symbol, int64_t addend)
{
    sdvm_compilerRelocation_t relocation = {
        .kind = kind,
        .symbol = symbol,
        .addend = addend,
        .offset = compiler->textSection.contents.size
    };

    sdvm_dynarray_add(&compiler->textSection.relocations, &relocation);
}

char *sdvm_compile_makeModuleSymbolInterface(sdvm_module_t *module, sdvm_moduleString_t *moduleName, sdvm_moduleString_t *valueName, sdvm_moduleString_t *valueTypeDescriptor)
{
    size_t symbolSize = 0;
    if(moduleName)
    {
        symbolSize += 5; //"'_Sdm_'"
        symbolSize += moduleName->stringSectionSize;
        symbolSize += 2; //"__"
    }

    symbolSize += valueName->stringSectionSize;
    if(valueTypeDescriptor->stringSectionSize)
    {
        symbolSize += 3; //"___";
        symbolSize += valueTypeDescriptor->stringSectionSize;
    }

    char *symbol = malloc(symbolSize);
    size_t destIndex = 0;
    if(moduleName)
    {
        memcpy(symbol + destIndex, "_Sdm_", 5); destIndex += 5;
        memcpy(symbol + destIndex, module->stringSectionData + moduleName->stringSectionOffset, moduleName->stringSectionSize); destIndex += moduleName->stringSectionSize;
        memcpy(symbol + destIndex, "__", 2); destIndex += 2;
    }
    memcpy(symbol + destIndex, module->stringSectionData + valueName->stringSectionOffset, valueName->stringSectionSize); destIndex += valueName->stringSectionSize;
    if(valueTypeDescriptor->stringSectionSize)
    {
        memcpy(symbol + destIndex, "___", 3); destIndex += 3;
        memcpy(symbol + destIndex, module->stringSectionData + valueTypeDescriptor->stringSectionOffset, valueTypeDescriptor->stringSectionSize); destIndex += valueTypeDescriptor->stringSectionSize;
    }
    symbol[destIndex] = 0;
    SDVM_ASSERT(symbolSize == destIndex);

    return symbol;
}

bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    sdvm_moduleCompilationState_t state = {0};
    sdvm_moduleCompilationState_initialize(&state, compiler, module);

    // Declare the imported value symbols.
    for(size_t i = 0; i < module->importValueTableSize; ++i)
    {
        sdvm_moduleImportValueTableEntry_t *importValueTableEntry = module->importValueTable + i;

        sdvm_moduleString_t *moduleName = NULL;
        if(importValueTableEntry->module != 0)
            moduleName = &module->importTable[importValueTableEntry->module - 1].name;

        char *importedSymbolName = sdvm_compile_makeModuleSymbolInterface(module, moduleName, &importValueTableEntry->name, &importValueTableEntry->typeDescriptor);
        state.importedValueTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, importedSymbolName, SdvmCompSymbolKindNull, SdvmCompSymbolBindingGlobal);
        free(importedSymbolName);
    }


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
        sdvm_moduleFunctionTableEntry_t *functionTableEntry = module->functionTable + i;
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
