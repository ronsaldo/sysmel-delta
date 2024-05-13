#include "compiler.h"
#include "coff.h"
#include "utils.h"
#include <stdio.h>
#include <string.h>

typedef struct sdvm_compilerCoffFileLayout_s
{
    size_t size;
    size_t header;
    size_t sectionHeaders;
    size_t sectionHeaderCount;
    size_t sectionContents[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionRelocations[SDVM_COMPILER_SECTION_COUNT];
    uint16_t sectionIndices[SDVM_COMPILER_SECTION_COUNT];
    bool writtenSections[SDVM_COMPILER_SECTION_COUNT];
    size_t symbolTable;
    size_t symbolCount;
    size_t stringTableSize;
    size_t stringTable;
} sdvm_compilerCoffFileLayout_t;

static size_t sdvm_compilerCoff_computeNameStringSize(const char *name)
{
    if(!name || !*name)
        return 0;

    size_t nameSize = strlen(name);
    if(nameSize <= 8)
        return 0;

    return nameSize + 1;
}

typedef struct sdvm_compilerCoffStringTableState_s
{
    char *writeBuffer;
    size_t size;
} sdvm_compilerCoffStringTableState_t;

static void sdvm_compilerCoffSectionNameWrite(sdvm_coff_sectionHeader_t *sectionHeader, sdvm_compilerCoffStringTableState_t *stringTable, const char *string)
{
    if(!string || !*string)
        return;
    
    size_t stringLength = strlen(string);
    if(stringLength <= 8)
    {
        memcpy(sectionHeader->name, string, stringLength);
        return;
    }

    snprintf(sectionHeader->name, sizeof(sectionHeader->name), "/%d", (int)stringTable->size);
    memcpy(stringTable->writeBuffer + stringTable->size, string, stringLength);
    stringTable->size += stringLength + 1;
}

static void sdvm_compilerCoffSymbolNameWrite(sdvm_coff_symbol_t *symbol, sdvm_compilerCoffStringTableState_t *stringTable, const char *string)
{
    if(!string || !*string)
    {
        symbol->nameZero = 0;
        symbol->nameOffset = 4;
        return;
    }
    
    size_t stringLength = strlen(string);
    if(stringLength <= 8)
    {
        memcpy(symbol->nameString, string, stringLength);
        return;
    }

    symbol->nameZero = 0;
    symbol->nameOffset = (uint32_t)stringTable->size;

    memcpy(stringTable->writeBuffer + stringTable->size, string, stringLength);
    stringTable->size += stringLength + 1;
}

static sdvm_compilerCoffFileLayout_t sdvm_compilerCoff_computeObjectFileLayout(sdvm_compiler_t *compiler)
{
    sdvm_compilerCoffFileLayout_t layout = {0};
    layout.header = 0;

    layout.size = sizeof(sdvm_coff_header_t);
    layout.sectionHeaders = layout.size;
    layout.sectionHeaderCount = 0;
    layout.stringTableSize = 1; // Start with an empty string.

    // Section headers.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        layout.sectionIndices[i] = (uint16_t)++layout.sectionHeaderCount;
        layout.writtenSections[i] = true;
        layout.size += sizeof(sdvm_coff_sectionHeader_t);

        layout.stringTableSize += sdvm_compilerCoff_computeNameStringSize(section->name);
    }

    // Section relocations
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0 || section->relocations.size == 0)
            continue;

        layout.sectionRelocations[i] = layout.size;
        layout.size += sizeof(sdvm_coff_relocation_t)*section->relocations.size;
    }

    // Section contents.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        layout.size = sdvm_compiler_alignSizeTo(layout.size, section->alignment);
        layout.sectionContents[i] = layout.size;
        layout.size += section->contents.size;
    }

    // Symbol table.
    layout.symbolTable = layout.size;

    // Symbols
    if(compiler->symbolTable.symbols.size != 0)
    {
        // Count the local symbols.
        size_t compilerSymbolCount = compiler->symbolTable.symbols.size;
        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        layout.symbolCount = 0;
        for(size_t i = 0; i < compilerSymbolCount; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->binding == SdvmCompSymbolBindingLocal && symbol->section && !layout.writtenSections[symbol->section])
                continue;

            if(symbol->kind == SdvmCompSymbolKindSection)
                layout.stringTableSize += sdvm_compilerCoff_computeNameStringSize(compiler->sections[symbol->section].name);
            else if(symbol->name)
                layout.stringTableSize += sdvm_compilerCoff_computeNameStringSize((char*)compiler->symbolTable.strings.data + symbol->name);
            symbol->objectSymbolIndex = (uint32_t)layout.symbolCount++;
        }

        layout.size += sizeof(sdvm_coff_symbol_t)*layout.symbolCount;
    }

    // String table.
    layout.stringTable = layout.size;
    layout.size += 4 + layout.stringTableSize;

    return layout;
}

static uint16_t sdvm_compilerCoff_mapType(sdvm_compilerSymbolKind_t kind)
{
    if(kind == SdvmCompSymbolKindFunction)
        return 0x20;

    return 0;
}

static uint8_t sdvm_compilerCoff_mapStorageClass(sdvm_compilerSymbolKind_t kind, sdvm_compilerSymbolBinding_t binding)
{
    if(kind == SdvmCompSymbolKindFile)
        return SDVM_IMAGE_SYM_CLASS_FILE;

    switch(binding)
    {
    case SdvmCompSymbolBindingLocal: return SDVM_IMAGE_SYM_CLASS_STATIC;
    case SdvmCompSymbolBindingWeak: return SDVM_IMAGE_SYM_CLASS_WEAK_EXTERNAL;
    default: return SDVM_IMAGE_SYM_CLASS_EXTERNAL;
    }
}

sdvm_compilerObjectFile_t *sdvm_compilerCoff_encode(sdvm_compiler_t *compiler)
{
    sdvm_compilerCoffFileLayout_t layout = sdvm_compilerCoff_computeObjectFileLayout(compiler);
    sdvm_compilerObjectFile_t *objectFile = sdvm_compileObjectFile_allocate(layout.size);
    if(!objectFile)
        return NULL;

    const sdvm_compilerTarget_t *target = compiler->target;

    sdvm_coff_header_t *header = (sdvm_coff_header_t *)(objectFile->data + layout.header);
    header->machine = target->coffMachine;
    header->numberOfSections = (uint16_t)layout.sectionHeaderCount;
    header->numberOfSymbols = (uint32_t)layout.symbolCount;
    header->pointerToSymbolTable = (uint32_t)layout.symbolTable;

    sdvm_compilerCoffStringTableState_t stringTable = {
        .size = 5,
        .writeBuffer = (char*)(objectFile->data + layout.stringTable)
    };

    // Section contents.
    sdvm_coff_sectionHeader_t *sectionHeaders = (sdvm_coff_sectionHeader_t*)(objectFile->data + layout.sectionHeaders);
    size_t writtenSectionHeaderCount = 0;

    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        sdvm_coff_sectionHeader_t *coffSection = sectionHeaders + writtenSectionHeaderCount++;
        sdvm_compilerCoffSectionNameWrite(coffSection, &stringTable, section->name);
        coffSection->pointerToRawData = (uint32_t)layout.sectionContents[i];
        coffSection->sizeOfRawData = (uint32_t)section->contents.size;
        coffSection->characteristics |= sdvm_uint32_log2(section->alignment)*SDVM_IMAGE_SCN_ALIGN_1BYTES;

        if(section->flags & SdvmCompSectionFlagWrite)
            coffSection->characteristics |= SDVM_IMAGE_SCN_MEM_WRITE;
        if(section->flags & SdvmCompSectionFlagRead)
            coffSection->characteristics |= SDVM_IMAGE_SCN_MEM_READ;
        if(section->flags & SdvmCompSectionFlagExec)
        {
            coffSection->characteristics |= SDVM_IMAGE_SCN_MEM_EXECUTE | SDVM_IMAGE_SCN_CNT_CODE;
        }
        else
        {
            if(section->flags & SdvmCompSectionFlagNoBits)
                coffSection->characteristics |= SDVM_IMAGE_SCN_CNT_UNINITIALIZED_DATA;
            else
                coffSection->characteristics |= SDVM_IMAGE_SCN_CNT_INITIALIZED_DATA;
        }

        uint8_t *objectSectionContents = objectFile->data + layout.sectionContents[i];
        memcpy(objectSectionContents, section->contents.data, section->contents.size);

        // Relocations
        if(section->relocations.size != 0)
        {
            coffSection->numberOfRelocations = (uint16_t)section->relocations.size;
            coffSection->pointerToRelocations = (uint32_t)layout.sectionRelocations[i];

            sdvm_coff_relocation_t *coffRelocations = (sdvm_coff_relocation_t*)(objectFile->data + coffSection->pointerToRelocations);
            sdvm_compilerRelocation_t *relocationTable = (sdvm_compilerRelocation_t *)section->relocations.data;
            sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
            for(size_t j = 0; j < section->relocations.size; ++j)
            {
                sdvm_compilerRelocation_t *relocation = relocationTable + j;
                sdvm_coff_relocation_t *coffRelocation = coffRelocations + j;
                coffRelocation->virtualAddress = relocation->offset;
                if(relocation->symbol)
                    coffRelocation->symbolTableIndex = symbols[relocation->symbol - 1].objectSymbolIndex;
                
                uint8_t *relocationTarget = objectSectionContents + relocation->offset;
                coffRelocation->type = target->mapCoffRelocationApplyingAddend(relocation, relocationTarget);
            }
        }
    }

    // Symbols
    if(compiler->symbolTable.symbols.size != 0)
    {
        // Count the local symbols.
        size_t compilerSymbolCount = compiler->symbolTable.symbols.size;
        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        sdvm_coff_symbol_t *coffSymbols = (sdvm_coff_symbol_t*)(objectFile->data + layout.symbolTable);

        for(size_t i = 0; i < compilerSymbolCount; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->binding == SdvmCompSymbolBindingLocal && symbol->section && !layout.writtenSections[symbol->section])
                continue;

            sdvm_coff_symbol_t *coffSymbol = coffSymbols + symbol->objectSymbolIndex;
            if(symbol->kind == SdvmCompSymbolKindSection)
                sdvm_compilerCoffSymbolNameWrite(coffSymbol, &stringTable, compiler->sections[symbol->section].name);
            else
                sdvm_compilerCoffSymbolNameWrite(coffSymbol, &stringTable, (char*)compiler->symbolTable.strings.data + symbol->name);

            if(symbol->section && symbol->section < SDVM_COMPILER_SECTION_COUNT)
                coffSymbol->sectionNumber = layout.sectionIndices[symbol->section];
            coffSymbol->value = (uint32_t)symbol->value;
            coffSymbol->type = sdvm_compilerCoff_mapType(symbol->kind);
            coffSymbol->storageClass = sdvm_compilerCoff_mapStorageClass(symbol->kind, symbol->binding);
        }
    }

    // String table size
    uint32_t *stringTableSize = (uint32_t*)(objectFile->data + layout.stringTable);
    *stringTableSize = (uint32_t)stringTable.size;

    return objectFile;
}

bool sdvm_compilerCoff_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerCoff_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, objectFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}
