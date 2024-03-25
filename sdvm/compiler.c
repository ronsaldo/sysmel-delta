#include "compiler.h"
#include "module.h"
#include "assert.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

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
    sdvm_dynarray_initialize(&section->pendingLabelRelocations, sizeof(sdvm_compilerPendingLabelRelocation_t), 512);
}

void sdvm_compilerObjectSection_destroy(sdvm_compilerObjectSection_t *section)
{
    sdvm_dynarray_destroy(&section->contents);
    sdvm_dynarray_destroy(&section->relocations);
    sdvm_dynarray_destroy(&section->pendingLabelRelocations);
}

sdvm_compiler_t *sdvm_compiler_create(const sdvm_compilerTarget_t *target)
{
    sdvm_compiler_t *compiler = calloc(1, sizeof(sdvm_compiler_t));
    compiler->target = target;
    compiler->pointerSize = target->pointerSize;

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

SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_getDefault(void)
{
    return sdvm_compilerTarget_getNamed(sdvm_compilerTarget_getDefaultTargetName());
}

SDVM_API const char *sdvm_compilerTarget_getDefaultTargetName(void)
{
#ifdef SDVM_DEFAULT_TARGET_NAME
    return SDVM_DEFAULT_TARGET_NAME;
#else
    return "x86_64-linux-gnu";
#endif 
}

SDVM_API const sdvm_compilerTarget_t *sdvm_compilerTarget_getNamed(const char *targetName)
{
    return sdvm_compilerTarget_x64_linux();
}

void sdvm_moduleCompilationState_initialize(sdvm_moduleCompilationState_t *state, sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    state->compiler = compiler;
    state->module = module;
    state->importedValueTableSymbols = calloc(module->importValueTableSize, sizeof(sdvm_compilerSymbolHandle_t));
    state->functionTableSymbols = calloc(module->functionTableSize, sizeof(sdvm_compilerSymbolHandle_t));
    state->exportedValueTableSymbols = calloc(module->exportValueTableSize, sizeof(sdvm_compilerSymbolHandle_t));
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
        printf("stack %d", location->firstStackLocation.framePointerOffset);
        return;
    case SdvmCompLocationStackPair:
        printf("stack %d:%d", location->firstStackLocation.framePointerOffset, location->secondStackLocation.framePointerOffset);
        return;
    case SdvmCompLocationLocalSymbolValue:
        printf("localValueOf[%s]", sdvm_compiler_symbolHandleNameCString(compiler, location->symbolHandle));
        return;
    case SdvmCompLocationGlobalSymbolValue:
        printf("globalValueOf[%s]", sdvm_compiler_symbolHandleNameCString(compiler, location->symbolHandle));
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
    uint32_t labelIndex = compiler->labels.size;
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

void sdvm_compiler_applyPendingLabelRelocationsInSection(sdvm_compiler_t *compiler, sdvm_compilerObjectSection_t *section)
{
    for(size_t i = 0; i < section->pendingLabelRelocations.size; ++i)
    {
        sdvm_compilerPendingLabelRelocation_t *relocation = (sdvm_compilerPendingLabelRelocation_t*)section->pendingLabelRelocations.data + i;
        sdvm_compilerLabel_t *label = (sdvm_compilerLabel_t*)compiler->labels.data + relocation->labelIndex;
        SDVM_ASSERT(label->section == section);

        switch(relocation->kind)
        {
        case SdvmCompRelocationRelative32:
            {
                int32_t value = label->value - relocation->offset + relocation->addend;
                memcpy(section->contents.data + relocation->offset, &value, 4);
            }
            break;
        default: abort();
        }
    }
    sdvm_dynarray_clear(&section->pendingLabelRelocations);
}

void sdvm_compiler_applyPendingLabelRelocations(sdvm_compiler_t *compiler)
{
    for(int i = 0; i < SDVM_COMPILER_SECTION_COUNT; ++i)
        sdvm_compiler_applyPendingLabelRelocationsInSection(compiler, compiler->sections + i);
        
    sdvm_dynarray_clear(&compiler->textSection.pendingLabelRelocations);
    sdvm_dynarray_clear(&compiler->labels);
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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_localSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle, int64_t offset)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationLocalSymbolValue,
        .symbolHandle = symbolHandle,
        .symbolOffset = offset
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_globalSymbolValue(sdvm_compilerSymbolHandle_t symbolHandle, int64_t offset)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationGlobalSymbolValue,
        .symbolHandle = symbolHandle,
        .symbolOffset = offset
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

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stackSignedInteger(uint32_t size)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationStack,
        .isSigned = true,
        .firstStackLocation = {
            .size = size,
            .alignment = size
        }
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stack(uint32_t size, uint32_t alignment)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationStack,
        .firstStackLocation = {
            .size = size,
            .alignment = alignment
        }
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_stackPair(uint32_t firstSize, uint32_t firstAlignment, uint32_t secondSize, uint32_t secondAlignment)
{
    sdvm_compilerLocation_t location = {
        .kind = SdvmCompLocationStackPair,
        .firstStackLocation = {
            .size = firstSize,
            .alignment = firstAlignment
        },
        .secondStackLocation = {
            .size = secondSize,
            .alignment = secondAlignment
        }
    };

    return location;
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_forOperandType(sdvm_compiler_t *compiler, sdvm_compilerInstruction_t *argument, sdvm_type_t type)
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

    case SdvmTypeBoolean:
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
        if(argument && argument->location.kind == SdvmCompLocationImmediateLabel)
            return argument->location;
        return sdvm_compilerLocation_integerRegister(compiler->pointerSize);

    case SdvmTypeGCPointer:
        return sdvm_compilerLocation_integerRegisterPair(compiler->pointerSize, compiler->pointerSize);

    default:
        abort();
    }
}

SDVM_API sdvm_compilerLocation_t sdvm_compilerLocation_spillForOperandType(sdvm_compiler_t *compiler, sdvm_type_t type)
{
    switch(type)
    {
    case SdvmTypeVoid:
    case SdvmTypeInfo:
        return sdvm_compilerLocation_null();

    case SdvmTypeInt8:
        return sdvm_compilerLocation_stackSignedInteger(1);
    case SdvmTypeInt16:
        return sdvm_compilerLocation_stackSignedInteger(2);
    case SdvmTypeInt32:
        return sdvm_compilerLocation_stackSignedInteger(4);
    case SdvmTypeInt64:
        return sdvm_compilerLocation_stackSignedInteger(8);

    case SdvmTypeUInt8:
        return sdvm_compilerLocation_stack(1, 1);
    case SdvmTypeUInt16:
        return sdvm_compilerLocation_stack(2, 2);
    case SdvmTypeUInt32:
        return sdvm_compilerLocation_stack(4, 4);
    case SdvmTypeUInt64:
        return sdvm_compilerLocation_stack(8, 8);

    case SdvmTypePointer:
    case SdvmTypeProcedureHandle:
    case SdvmTypeLabel:
        return sdvm_compilerLocation_stack(compiler->pointerSize, compiler->pointerSize);

    case SdvmTypeGCPointer:
        return sdvm_compilerLocation_stackPair(compiler->pointerSize, compiler->pointerSize, compiler->pointerSize, compiler->pointerSize);

    default:
        abort();
    }
}

SDVM_API bool sdvm_compilerLocation_isStackOrPair(const sdvm_compilerLocation_t *location)
{
    return location->kind == SdvmCompLocationStack || location->kind == SdvmCompLocationStackPair;
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

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_calledFunction(sdvm_functionCompilationState_t *functionState, sdvm_compilerCallingConventionState_t *state, sdvm_compilerInstruction_t *operand)
{
    functionState->hasCallout = true;
    if(state->convention->supportsLocalSymbolValueCall && operand->location.kind == SdvmCompLocationLocalSymbolValue)
        return operand->location;
    if(state->convention->supportsGlobalSymbolValueCall && operand->location.kind == SdvmCompLocationGlobalSymbolValue)
        return operand->location;

    return sdvm_compilerLocation_integerRegister(state->convention->integerRegisterSize);
}

sdvm_compilerLocation_t sdvm_compilerCallingConventionState_calledClosure(sdvm_functionCompilationState_t *functionState, sdvm_compilerCallingConventionState_t *state)
{
    functionState->hasCallout = true;
    return sdvm_compilerLocation_specificRegisterPair(*state->convention->closureRegister, *state->convention->closureGCRegister);
}

sdvm_compilerInstructionClobberSets_t sdvm_compilerCallingConventionState_getClobberSets(const sdvm_compilerCallingConvention_t *convention)
{
    sdvm_compilerInstructionClobberSets_t sets = {0};
    for(uint32_t i = 0; i < convention->callTouchedIntegerRegisterCount; ++i)
        sdvm_registerSet_set(&sets.integerSet, convention->callTouchedIntegerRegisters[i]);
    for(uint32_t i = 0; i < convention->callTouchedFloatRegisterCount; ++i)
        sdvm_registerSet_set(&sets.floatSet, convention->callTouchedFloatRegisters[i]);
    for(uint32_t i = 0; i < convention->callTouchedVectorRegisterCount; ++i)
        sdvm_registerSet_set(&sets.vectorSet, convention->callTouchedVectorRegisters[i]);
    return sets;
}

void sdvm_functionCompilationState_computeLabelLocations(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;

    for(uint32_t i = 0; i < state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        if(instruction->decoding.isConstant)
        {
            switch(instruction->decoding.opcode)
            {
            case SdvmConstLabel:
                instruction->location = sdvm_compilerLocation_immediateLabel(sdvm_compiler_makeLabel(compiler));
                break;
            default:
                break;
            }
        }
    }
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
            SDVM_ASSERT(instruction->location.kind == SdvmCompLocationImmediateLabel);
            break;
        case SdvmConstImportPointer:
        case SdvmConstImportProcedureHandle:
            {
                uint32_t importValueIndex = instruction->decoding.constant.unsignedPayload;
                SDVM_ASSERT(importValueIndex <= state->module->importValueTableSize);
                if(importValueIndex > 0)
                {
                    sdvm_compilerSymbolHandle_t symbolHandle = state->moduleState->importedValueTableSymbols[importValueIndex - 1];
                    instruction->location = sdvm_compilerLocation_globalSymbolValue(symbolHandle, 0);
                }
                else
                {
                    instruction->location = sdvm_compilerLocation_null();
                }
            }
            break;
        case SdvmConstLocalProcedureHandle:
            {
                uint32_t functionIndex = instruction->decoding.constant.unsignedPayload;
                SDVM_ASSERT(functionIndex <= state->module->functionTableSize);
                if(functionIndex > 0)
                {
                    sdvm_compilerSymbolHandle_t symbolHandle = state->moduleState->functionTableSymbols[functionIndex - 1];
                    instruction->location = sdvm_compilerLocation_localSymbolValue(symbolHandle, 0);
                }
                else
                {
                    instruction->location = sdvm_compilerLocation_null();
                }
            }
            break;
        case SdvmConstPointerCString:
        case SdvmConstPointerString:
        case SdvmConstGCPointerCString:
        case SdvmConstGCPointerString:
            {
                bool nullTerminated = instruction->decoding.baseOpcode == SdvmConstOpConstCString;
                uint32_t stringOffset = instruction->decoding.constant.unsignedPayload & SDVM_CONSTANT_PAYLOAD_HALF_BITS_MASK;
                uint32_t stringSize = (instruction->decoding.constant.unsignedPayload >> SDVM_CONSTANT_PAYLOAD_HALF_BITS) & SDVM_CONSTANT_PAYLOAD_HALF_BITS_MASK;
                if(stringSize > 0 || nullTerminated)
                {
                    size_t rodataOffset = compiler->rodataSection.contents.size;
                    sdvm_dynarray_addAll(&compiler->rodataSection.contents, stringSize, state->module->stringSectionData + stringOffset);
                    
                    if(nullTerminated)
                    {
                        uint8_t terminator = 0;
                        sdvm_dynarray_add(&compiler->rodataSection.contents, &terminator);
                    }

                    instruction->location = sdvm_compilerLocation_localSymbolValue(compiler->rodataSection.symbolIndex, rodataOffset);
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

    sdvm_compilerInstruction_t *arg0 = instruction->decoding.arg0IsInstruction ? state->instructions + instruction->decoding.instruction.arg0 : NULL;
    sdvm_compilerInstruction_t *arg1 = instruction->decoding.arg1IsInstruction ? state->instructions + instruction->decoding.instruction.arg1 : NULL;
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
        instruction->arg0Location = sdvm_compilerCallingConventionState_signedInteger32(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgUInt8:
    case SdvmInstCallArgUInt16:
    case SdvmInstCallArgUInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_integer32(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgInt64:
    case SdvmInstCallArgUInt64:
        instruction->arg0Location = sdvm_compilerCallingConventionState_integer64(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgPointer:
    case SdvmInstCallArgProcedureHandle:
        instruction->arg0Location = sdvm_compilerCallingConventionState_pointer(&state->currentCallCallingConventionState);
        return;
    case SdvmInstCallArgGCPointer:
        instruction->arg0Location = sdvm_compilerCallingConventionState_pointerPair(&state->currentCallCallingConventionState);
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
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallInt8:
    case SdvmInstCallInt16:
    case SdvmInstCallInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        instruction->destinationLocation = sdvm_compilerLocation_specificSignedRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallInt64:
    case SdvmInstCallUInt64:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        if(state->callingConvention->integerRegisterSize >= 8)
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger64ResultRegister);
        else
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstInteger32ResultRegister, *state->currentCallCallingConvention->secondInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallUInt8:
    case SdvmInstCallUInt16:
    case SdvmInstCallUInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallPointer:
    case SdvmInstCallProcedureHandle:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstIntegerResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallGCPointer:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledFunction(state, &state->currentCallCallingConventionState, arg0);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstIntegerResultRegister, *state->currentCallCallingConvention->secondIntegerResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;
#pragma endregion CallConstraints

#pragma region CallClosureConstraints
    case SdvmInstCallClosureVoid:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallClosureInt8:
    case SdvmInstCallClosureInt16:
    case SdvmInstCallClosureInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificSignedRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallClosureInt64:
    case SdvmInstCallClosureUInt64:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->closureRegister, *state->currentCallCallingConvention->closureGCRegister);
        if(state->callingConvention->integerRegisterSize >= 8)
            instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger64ResultRegister);
        else
            instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstInteger32ResultRegister, *state->currentCallCallingConvention->secondInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallClosureUInt8:
    case SdvmInstCallClosureUInt16:
    case SdvmInstCallClosureUInt32:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstInteger32ResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallClosurePointer:
    case SdvmInstCallClosureProcedureHandle:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegister(*state->currentCallCallingConvention->firstIntegerResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;

    case SdvmInstCallClosureGCPointer:
        instruction->arg0Location = sdvm_compilerCallingConventionState_calledClosure(state, &state->currentCallCallingConventionState);
        instruction->destinationLocation = sdvm_compilerLocation_specificRegisterPair(*state->currentCallCallingConvention->firstIntegerResultRegister, *state->currentCallCallingConvention->secondIntegerResultRegister);
        instruction->clobberSets = sdvm_compilerCallingConventionState_getClobberSets(state->currentCallCallingConventionState.convention);
        return;
#pragma endregion CallClosureConstraints

    default:
        if(instruction->decoding.arg0IsInstruction)
            instruction->arg0Location = sdvm_compilerLocation_forOperandType(compiler, arg0, instruction->decoding.instruction.arg0Type);

        if(instruction->decoding.arg1IsInstruction)
            instruction->arg1Location = sdvm_compilerLocation_forOperandType(compiler, arg1, instruction->decoding.instruction.arg1Type);

        instruction->destinationLocation = sdvm_compilerLocation_forOperandType(compiler, NULL, instruction->decoding.destType);
        return;
    }
}

void sdvm_registerSet_clear(sdvm_registerSet_t *set)
{
    memset(set->masks, 0, sizeof(set->masks));
}

bool sdvm_registerSet_includes(const sdvm_registerSet_t *set, uint8_t value)
{
    uint8_t wordIndex = value / 32;
    uint8_t bitIndex = value % 32;
    return set->masks[wordIndex] & (1<<bitIndex);
}

bool sdvm_registerSet_hasIntersection(const sdvm_registerSet_t *a, const sdvm_registerSet_t *b)
{
    for(int i = 0; i < SDVM_REGISTER_SET_WORD_COUNT; ++i)
    {
        if((a->masks[i] & b->masks[i]) != 0)
            return true;
    }
    
    return false;
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

bool sdvm_registerSet_isEmpty(const sdvm_registerSet_t *set)
{
    for(int i = 0; i < SDVM_REGISTER_SET_WORD_COUNT; ++i)
    {
        if(set->masks[i] != 0)
            return false;
    }

    return true;
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

    registerFile->currentInstructionIndex = instruction->index;
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

void sdvm_linearScanRegisterAllocatorFile_spillInterval(sdvm_compiler_t *compiler, sdvm_linearScanRegisterAllocatorFile_t *registerFile, sdvm_linearScanActiveInterval_t *interval)
{
    interval->instruction->location = sdvm_compilerLocation_spillForOperandType(compiler, interval->instruction->decoding.destType);
    sdvm_registerSet_unset(&registerFile->allocatedRegisterSet, interval->registerValue);
}

void sdvm_linearScanRegisterAllocatorFile_spillOrExpireClobberedInterval(sdvm_compiler_t *compiler, sdvm_linearScanRegisterAllocatorFile_t *registerFile, sdvm_linearScanActiveInterval_t *interval)
{
    if(interval->end > (uint32_t)registerFile->currentInstructionIndex)
        interval->instruction->location = sdvm_compilerLocation_spillForOperandType(compiler, interval->instruction->decoding.destType);
    sdvm_registerSet_unset(&registerFile->allocatedRegisterSet, interval->registerValue);
}

void sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(sdvm_compiler_t *compiler, sdvm_linearScanRegisterAllocatorFile_t *registerFile, uint8_t registerValue)
{
    if(sdvm_registerSet_includes(&registerFile->allocatedRegisterSet, registerValue))
    {
        uint32_t destIndex = 0;
        for(uint32_t i = 0; i < registerFile->activeIntervalCount; ++i)
        {
            sdvm_linearScanActiveInterval_t *interval = registerFile->activeIntervals + i;
            if(interval->registerValue == registerValue)
                sdvm_linearScanRegisterAllocatorFile_spillInterval(compiler, registerFile, interval);
            else
                registerFile->activeIntervals[destIndex++] = *interval;
        }

        SDVM_ASSERT(!sdvm_registerSet_includes(&registerFile->allocatedRegisterSet, registerValue));
    }

    sdvm_registerSet_set(&registerFile->activeRegisterSet, registerValue);
    sdvm_registerSet_set(&registerFile->usedRegisterSet, registerValue);
}

sdvm_compilerRegisterValue_t sdvm_linearScanRegisterAllocatorFile_allocate(sdvm_compiler_t *compiler, sdvm_linearScanRegisterAllocatorFile_t *registerFile)
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

    // Spill the last active interval.
    SDVM_ASSERT(registerFile->activeIntervalCount > 0);
    --registerFile->activeIntervalCount;
    sdvm_linearScanActiveInterval_t *interval = registerFile->activeIntervals + registerFile->activeIntervalCount;
    sdvm_compilerRegisterValue_t spilledRegister = interval->registerValue;
    sdvm_linearScanRegisterAllocatorFile_spillInterval(compiler, registerFile, interval);

    sdvm_registerSet_set(&registerFile->activeRegisterSet, spilledRegister);
    sdvm_registerSet_set(&registerFile->usedRegisterSet, spilledRegister);

    return spilledRegister;
}

void sdvm_linearScanRegisterAllocatorFile_spillClobberSets(sdvm_compiler_t *compiler, sdvm_linearScanRegisterAllocatorFile_t *registerFile, const sdvm_registerSet_t *set)
{
    if(!sdvm_registerSet_hasIntersection(&registerFile->allocatedRegisterSet, set))
        return;

    uint32_t destIndex = 0;
    for(uint32_t i = 0; i < registerFile->activeIntervalCount; ++i)
    {
        sdvm_linearScanActiveInterval_t *interval = registerFile->activeIntervals + i;
        if(sdvm_registerSet_includes(set, interval->registerValue))
            sdvm_linearScanRegisterAllocatorFile_spillOrExpireClobberedInterval(compiler, registerFile, interval);
        else
            registerFile->activeIntervals[destIndex++] = *interval;
    }
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
            sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(registerAllocator->compiler, registerAllocator->registerFiles[location->firstRegister.kind], location->firstRegister.value);
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
            sdvm_linearScanRegisterAllocatorFile_spillAndActivateRegister(registerAllocator->compiler, registerAllocator->registerFiles[location->secondRegister.kind], location->secondRegister.value);
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
            location->firstRegister.value = sdvm_linearScanRegisterAllocatorFile_allocate(registerAllocator->compiler, registerAllocator->registerFiles[location->firstRegister.kind]);
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
            location->secondRegister.value = sdvm_linearScanRegisterAllocatorFile_allocate(registerAllocator->compiler, registerAllocator->registerFiles[location->secondRegister.kind]);
        }
        
        location->secondRegister.isPending = false;
    }
}

void sdvm_linearScanRegisterAllocator_spillClobberSets(sdvm_linearScanRegisterAllocator_t *registerAllocator, const sdvm_compilerInstructionClobberSets_t *clobberSet)
{
    if(!sdvm_registerSet_isEmpty(&clobberSet->integerSet))
        sdvm_linearScanRegisterAllocatorFile_spillClobberSets(registerAllocator->compiler, registerAllocator->integerRegisterFile, &clobberSet->integerSet);

    if(!sdvm_registerSet_isEmpty(&clobberSet->floatSet))
        sdvm_linearScanRegisterAllocatorFile_spillClobberSets(registerAllocator->compiler, registerAllocator->floatRegisterFile, &clobberSet->floatSet);

    if(!sdvm_registerSet_isEmpty(&clobberSet->vectorSet))
    {
        sdvm_linearScanRegisterAllocatorFile_spillClobberSets(registerAllocator->compiler, registerAllocator->vectorFloatRegisterFile, &clobberSet->vectorSet);
        sdvm_linearScanRegisterAllocatorFile_spillClobberSets(registerAllocator->compiler, registerAllocator->vectorIntegerRegisterFile, &clobberSet->vectorSet);
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

    sdvm_linearScanRegisterAllocator_spillClobberSets(registerAllocator, &instruction->clobberSets);

    sdvm_linearScanRegisterAllocator_endInstruction(registerAllocator, instruction);
}

void sdvm_compiler_allocateFunctionRegisters(sdvm_functionCompilationState_t *state, sdvm_linearScanRegisterAllocator_t *registerAllocator)
{
    for(uint32_t i = 0; i <state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_allocateInstructionRegisters(state, registerAllocator, instruction);
    }

    // Store a copy of the used register sets. We need it for preserving called saved registers.
    state->usedIntegerRegisterSet = registerAllocator->integerRegisterFile->usedRegisterSet;
    state->usedFloatRegisterSet = registerAllocator->floatRegisterFile->usedRegisterSet;
    state->usedVectorFloatRegisterSet = registerAllocator->vectorFloatRegisterFile->usedRegisterSet;
    state->usedVectorIntegerRegisterSet = registerAllocator->vectorIntegerRegisterFile->usedRegisterSet;

    const sdvm_compilerCallingConvention_t *convention = state->callingConvention;
    for(uint32_t i = 0; i < convention->callPreservedIntegerRegisterCount; ++i)
    {
        if(sdvm_registerSet_includes(&state->usedIntegerRegisterSet, convention->callPreservedIntegerRegisters[i]))
            sdvm_registerSet_set(&state->usedCallPreservedIntegerRegisterSet, convention->callPreservedIntegerRegisters[i]);
    }

    for(uint32_t i = 0; i < convention->callPreservedFloatRegisterCount; ++i)
    {
        if(sdvm_registerSet_includes(&state->usedFloatRegisterSet, convention->callPreservedFloatRegisters[i]))
            sdvm_registerSet_set(&state->usedCallPreservedFloatRegisterSet, convention->callPreservedFloatRegisters[i]);
    }

    for(uint32_t i = 0; i < convention->callPreservedVectorRegisterCount; ++i)
    {
        if(sdvm_registerSet_includes(&state->usedVectorFloatRegisterSet, convention->callPreservedVectorRegisters[i]) ||
           sdvm_registerSet_includes(&state->usedVectorIntegerRegisterSet, convention->callPreservedVectorRegisters[i]))
            sdvm_registerSet_set(&state->usedCallPreservedVectorRegisterSet, convention->callPreservedVectorRegisters[i]);
    }
}

void sdvm_compiler_allocateNewStackLocationIfNeeded(sdvm_functionCompilationState_t *state, sdvm_compilerStackLocation_t *location, bool isGC)
{
    if(location->isValid)
        return;

    location->segment = isGC ? SdvmFunctionStackSegmentGCSpilling : SdvmFunctionStackSegmentSpilling;
    
    sdvm_functionCompilationStackSegment_t *segment = state->stackSegments + location->segment;
    if(location->alignment > segment->alignment)
        segment->alignment = location->alignment;
    
    location->segmentOffset = (segment->size + location->alignment - 1) & (-location->alignment);
    segment->size = location->segmentOffset + location->size;
    location->isValid = true;
}

void sdvm_compiler_allocateNewStackLocationsIfNeeded(sdvm_functionCompilationState_t *state, sdvm_compilerLocation_t *location, sdvm_type_t type)
{
    if(location->kind == SdvmCompLocationStack)
    {
        sdvm_compiler_allocateNewStackLocationIfNeeded(state, &location->firstStackLocation, false);
    }
    else if(location->kind == SdvmCompLocationStack)
    {
        sdvm_compiler_allocateNewStackLocationIfNeeded(state, &location->firstStackLocation, false);
        sdvm_compiler_allocateNewStackLocationIfNeeded(state, &location->secondStackLocation, type == SdvmTypeGCPointer);
    }
}

void sdvm_compiler_allocateInstructionSpillLocations(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(!sdvm_compilerLocation_isStackOrPair(&instruction->location) && !sdvm_compilerLocation_isStackOrPair(&instruction->stackLocation))
        return;

    if(sdvm_compilerLocation_isStackOrPair(&instruction->stackLocation))
    {
        sdvm_compiler_allocateNewStackLocationsIfNeeded(state, &instruction->stackLocation, instruction->decoding.destType);
        instruction->location = instruction->stackLocation;
    }
    else if(sdvm_compilerLocation_isStackOrPair(&instruction->location))
    {
        sdvm_compiler_allocateNewStackLocationsIfNeeded(state, &instruction->location, instruction->decoding.destType);
        if(!sdvm_compilerLocation_isStackOrPair(&instruction->stackLocation))
            instruction->stackLocation = instruction->location;
    }
}

void sdvm_compiler_allocateFunctionSpillLocations(sdvm_functionCompilationState_t *state)
{
    for(uint32_t i = 0; i < state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_allocateInstructionSpillLocations(state, instruction);
    }
}

void sdvm_compiler_computeStackSegmentLayouts(sdvm_functionCompilationState_t *state)
{
    if(state->calloutStackSegment.alignment < state->callingConvention->stackAlignment)
        state->calloutStackSegment.alignment = state->callingConvention->stackAlignment;

    uint32_t offset = 0;

    // Argument segment
    {
        state->argumentPassingStackSegment.startOffset = -state->argumentPassingStackSegment.size;
        state->argumentPassingStackSegment.endOffset = 0;
    }

    // Prologue segment.
    {
        state->prologueStackSegment.startOffset = offset;
        offset += state->prologueStackSegment.size;
        state->prologueStackSegment.endOffset = offset;
    }

    for(int i = SdvmFunctionStackSegmentFirstAfterPrologue; i < SdvmFunctionStackSegmentCount; ++i)
    {
        sdvm_functionCompilationStackSegment_t *segment = state->stackSegments + i;
        segment->endOffset = (offset + segment->size + segment->alignment - 1) & (-segment->alignment);
        segment->startOffset = offset - segment->size;
        offset = segment->endOffset;
    }
}

void sdvm_compiler_computeStackFrameLocation(sdvm_functionCompilationState_t *state, sdvm_compilerStackLocation_t *location)
{
    sdvm_functionCompilationStackSegment_t *segment = state->stackSegments + location->segment;
    location->framePointerRegister = state->stackFrameRegister;
    location->framePointerOffset = state->stackFramePointerAnchorOffset - segment->endOffset + location->segmentOffset;
}

void sdvm_compiler_computeStackFrameLocations(sdvm_functionCompilationState_t *state, sdvm_compilerLocation_t *location)
{
    if(location->kind == SdvmCompLocationStack)
    {
        sdvm_compiler_computeStackFrameLocation(state, &location->firstStackLocation);
    }
    else if(location->kind == SdvmCompLocationStack)
    {
        sdvm_compiler_computeStackFrameLocation(state, &location->firstStackLocation);
        sdvm_compiler_computeStackFrameLocation(state, &location->secondStackLocation);
    }
}

void sdvm_compiler_computeInstructionStackFrameOffsets(sdvm_functionCompilationState_t *state, sdvm_compilerInstruction_t *instruction)
{
    if(sdvm_compilerLocation_isStackOrPair(&instruction->location))
        sdvm_compiler_computeStackFrameLocations(state, &instruction->location);

    if(sdvm_compilerLocation_isStackOrPair(&instruction->stackLocation))
        sdvm_compiler_computeStackFrameLocations(state, &instruction->stackLocation);
}

void sdvm_compiler_computeStackFrameOffsets(sdvm_functionCompilationState_t *state)
{
    for(uint32_t i = 0; i <state->instructionCount; ++i)
    {
        sdvm_compilerInstruction_t *instruction = state->instructions + i;
        sdvm_compiler_computeInstructionStackFrameOffsets(state, instruction);
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

    // The alignment of the stack segments must be at least one.
    for(int i = 0; i < SdvmFunctionStackSegmentCount; ++i)
        functionState.stackSegments[i].alignment = 1;

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
    bool result = moduleState->compiler->target->compileModuleFunction(&functionState);

    sdvm_compiler_applyPendingLabelRelocations(moduleState->compiler);
    
    // Destroy the function compilation state.
    sdvm_functionCompilationState_destroy(&functionState);
    return result;
}

size_t sdvm_compiler_addInstructionBytes(sdvm_compiler_t *compiler, size_t instructionSize, const void *instruction)
{
    return sdvm_dynarray_addAll(&compiler->textSection.contents, instructionSize, instruction);
}

size_t sdvm_compiler_addInstructionByte(sdvm_compiler_t *compiler, uint8_t byte)
{
    return sdvm_dynarray_add(&compiler->textSection.contents, &byte);
}

void sdvm_compiler_addInstructionRelocation(sdvm_compiler_t *compiler, sdvm_compilerRelocationKind_t kind, sdvm_compilerSymbolHandle_t symbol, int64_t addend)
{
    sdvm_compilerRelocation_t relocation = {
        .kind = kind,
        .symbol = symbol,
        .addend = addend,
        .offset = compiler->textSection.contents.size
    };

    sdvm_dynarray_add(&compiler->textSection.relocations, &relocation);
}

void sdvm_compiler_addInstructionLabelValueRelative32(sdvm_compiler_t *compiler, uint32_t labelIndex, int32_t addend)
{
    uint32_t addressValue = 0;
    sdvm_compilerLabel_t *label = (sdvm_compilerLabel_t*)compiler->labels.data + labelIndex;
    if(label->section == &compiler->textSection)
    {
        addressValue = (int32_t)(label->value - compiler->textSection.contents.size + addend);
    }
    else
    {
        sdvm_compilerPendingLabelRelocation_t pendingRelocation = {
            .kind = SdvmCompRelocationRelative32,
            .labelIndex = labelIndex,
            .addend = addend,
            .offset = compiler->textSection.contents.size
        };

        sdvm_dynarray_add(&compiler->textSection.pendingLabelRelocations, &pendingRelocation);
    }

    sdvm_compiler_addInstructionBytes(compiler, 4, &addressValue);
}

char *sdvm_compile_makeModuleSymbolInterface(sdvm_compiler_t *compiler, sdvm_module_t *module, sdvm_moduleString_t *moduleName, sdvm_t_moduleExternalType_t externalType, sdvm_moduleString_t *valueName, sdvm_moduleString_t *valueTypeDescriptor)
{
    size_t symbolSize = 0;

    // Add the underscore prefix when required.
    bool underscorePrefix = compiler->target->usesUnderscorePrefix;
    if(underscorePrefix)
        symbolSize += 1;

    if(externalType == SdvmModuleExternalTypeC)
    {
        symbolSize += valueName->stringSectionSize;
    }
    else
    {
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
    }

    char *symbol = malloc(symbolSize + 1);
    size_t destIndex = 0;

    // Add the underscore prefix, when is it required.
    if(underscorePrefix)
        symbol[destIndex++] = '_';

    if(externalType == SdvmModuleExternalTypeC)
    {
        // TODO: Add the underscore prefix when required.
        memcpy(symbol + destIndex, module->stringSectionData + valueName->stringSectionOffset, valueName->stringSectionSize); destIndex += valueName->stringSectionSize;
    }
    else
    {
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
    }
    symbol[destIndex] = 0;
    SDVM_ASSERT(symbolSize == destIndex);

    return symbol;
}

bool sdvm_compiler_compileModule(sdvm_compiler_t *compiler, sdvm_module_t *module)
{
    sdvm_moduleCompilationState_t state = {0};
    sdvm_moduleCompilationState_initialize(&state, compiler, module);

    // Declare the exported value symbols.
    for(size_t i = 0; i < module->exportValueTableSize; ++i)
    {
        sdvm_moduleExportValueTableEntry_t *exportValueTableEntry = module->exportValueTable + i;

        char *exportedSymbolName = sdvm_compile_makeModuleSymbolInterface(compiler, module, &module->header->name, exportValueTableEntry->externalType, &exportValueTableEntry->name, &exportValueTableEntry->typeDescriptor);
        sdvm_compilerSymbolKind_t symbolKind = SdvmCompSymbolKindNull;

        switch(exportValueTableEntry->kind)
        {
        case SdvmModuleValueKindFunctionHandle:
            symbolKind = SdvmCompSymbolKindFunction;
            break;

        case SdvmModuleValueKindDataSectionValue:
        case SdvmModuleValueKindConstantSectionValue:
        case SdvmModuleValueKindObjectHandle:
            symbolKind = SdvmCompSymbolKindVariable;
            break;
        default:
            break;
        }

        state.exportedValueTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, exportedSymbolName, symbolKind, SdvmCompSymbolBindingGlobal);

        // If this is a function handle, reuse the symbol for the function table symbols.
        if(exportValueTableEntry->kind == SdvmModuleValueKindFunctionHandle)
        {
            SDVM_ASSERT(1 <= exportValueTableEntry->firstValue && exportValueTableEntry->firstValue <= module->functionTableSize);
            state.functionTableSymbols[exportValueTableEntry->firstValue - 1] = state.exportedValueTableSymbols[i];
        }

        free(exportedSymbolName);
    }

    // Declare the imported value symbols.
    for(size_t i = 0; i < module->importValueTableSize; ++i)
    {
        sdvm_moduleImportValueTableEntry_t *importValueTableEntry = module->importValueTable + i;

        sdvm_moduleString_t *moduleName = NULL;
        if(importValueTableEntry->module != 0)
            moduleName = &module->importTable[importValueTableEntry->module - 1].name;

        char *importedSymbolName = sdvm_compile_makeModuleSymbolInterface(compiler, module, moduleName, importValueTableEntry->externalType, &importValueTableEntry->name, &importValueTableEntry->typeDescriptor);
        state.importedValueTableSymbols[i] = sdvm_compilerSymbolTable_createUndefinedSymbol(&compiler->symbolTable, importedSymbolName, SdvmCompSymbolKindNull, SdvmCompSymbolBindingGlobal);
        free(importedSymbolName);
    }

    // Declare the function symbols.
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        if(state.functionTableSymbols[i])
            continue;

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

    sdvm_moduleCompilationState_destroy(&state);

    return hasSucceeded;
}

SDVM_API bool sdvm_compiler_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    switch(compiler->target->objectFileType)
    {
    case SdvmObjectFileTypeElf:
    default:
        if(compiler->pointerSize <= 4)
            return sdvm_compilerElf32_encodeObjectAndSaveToFileNamed(compiler, objectFileName);
        else
            return sdvm_compilerElf64_encodeObjectAndSaveToFileNamed(compiler, objectFileName);
    }
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
