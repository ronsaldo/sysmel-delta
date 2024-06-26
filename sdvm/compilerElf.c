#include "compiler.h"
#include "elf.h"
#include <stdio.h>
#include <string.h>

static size_t sdvm_compilerElf_computeNameStringSize(const char *name)
{
    if(!name || !*name)
        return 0;

    return strlen(name) + 1;
}

typedef struct sdvm_compilerElfFileLayout_s
{
    size_t size;
    size_t header;
    size_t sectionHeaders;
    size_t sectionHeaderCount;
    size_t sectionContents[SDVM_COMPILER_SECTION_COUNT];
    uint16_t sectionIndices[SDVM_COMPILER_SECTION_COUNT];
    bool writtenSections[SDVM_COMPILER_SECTION_COUNT];
    size_t relocationSectionContents[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionHeaderStringsSize;
    size_t sectionHeaderStrings;

    size_t symbolStringTable;
    size_t symbolStringTableSectionIndex;
    size_t symbolTable;
    size_t symbolTableSectionIndex;
    size_t symbolCount;
    size_t localSymbolCount;

    size_t noteGnuStackSectionIndex;
} sdvm_compilerElfFileLayout_t;

typedef struct sdvm_compilerElfStringSectionState_s
{
    char *writeBuffer;
    size_t size;
} sdvm_compilerElfStringSectionState_t;

static size_t sdvm_compilerElfStringSection_write(sdvm_compilerElfStringSectionState_t *stringSection, const char *string)
{
    if(!string || !*string)
        return 0;
    
    size_t stringLength = strlen(string);
    size_t result = stringSection->size;
    memcpy(stringSection->writeBuffer + result, string, stringLength);
    stringSection->size += stringLength + 1;
    return result;
}

static sdvm_compilerElfFileLayout_t sdvm_compilerElf64_computeObjectFileLayout(sdvm_compiler_t *compiler, bool useRela)
{
    sdvm_compilerElfFileLayout_t layout = {0};
    layout.header = 0;

    layout.size = sizeof(sdvm_elf64_header_t);
    layout.sectionHeaderCount = 1;
    layout.sectionHeaderStringsSize = 1;

    // Section contents.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(section->name);
        layout.sectionIndices[i] = (uint16_t)layout.sectionHeaderCount;
        layout.writtenSections[i] = true;
        ++layout.sectionHeaderCount;

        layout.size = sdvm_compiler_alignSizeTo(layout.size, section->alignment);
        if((section->flags & SdvmCompSectionFlagNoBits) == 0)
        {
            layout.sectionContents[i] = layout.size;
            layout.size += section->contents.size;
        }
    }

    // Section relocations
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0 || section->relocations.size == 0)
            continue;

        ++layout.sectionHeaderCount;
        layout.relocationSectionContents[i] = layout.size;
        if(useRela)
        {
            layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(section->relaSectionName);
            layout.size += sizeof(sdvm_elf64_rela_t)*section->relocations.size;
        }
        else
        {
            layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(section->relSectionName);
            layout.size += sizeof(sdvm_elf64_rel_t)*section->relocations.size;
        }
    }

    // Symbols
    if(compiler->symbolTable.symbols.size != 0)
    {
        // String table
        layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(".strtab");
        layout.symbolStringTable = layout.size;
        layout.symbolStringTableSectionIndex = layout.sectionHeaderCount++;
        layout.size += compiler->symbolTable.strings.size;

        // Symbol table
        layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(".symtab");
        layout.symbolTable = layout.size;
        layout.symbolTableSectionIndex = layout.sectionHeaderCount++;
        layout.localSymbolCount = 1;

        // Count the local symbols.
        size_t compilerSymbolCount = compiler->symbolTable.symbols.size;
        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        for(size_t i = 0; i < compilerSymbolCount; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->binding == SdvmCompSymbolBindingLocal)
            {
                if(symbol->section && layout.writtenSections[symbol->section])
                    symbol->objectSymbolIndex = (uint32_t)layout.localSymbolCount++;
            }
        }

        // Count the non-local symbols.
        layout.symbolCount = layout.localSymbolCount;
        for(size_t i = 0; i < compilerSymbolCount; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->binding != SdvmCompSymbolBindingLocal)
                symbol->objectSymbolIndex = (uint32_t)layout.symbolCount++;
        }

        layout.size += sizeof(sdvm_elf64_symbol_t)*layout.symbolCount;
    }

    // .note.GNU-stack No executable stack flag.
    layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(".note.GNU-stack");
    layout.noteGnuStackSectionIndex = layout.sectionHeaderCount++;

    // Section header strings
    layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(".shstrtab");
    layout.sectionHeaderStrings = layout.size;
    layout.size += layout.sectionHeaderStringsSize;
    ++layout.sectionHeaderCount;

    // Section headers.
    layout.sectionHeaders = layout.size;
    layout.size += sizeof(sdvm_elf64_sectionHeader_t) * layout.sectionHeaderCount;

    return layout;
}

static uint32_t sdvm_compilerElf64_mapSymbolBinding(sdvm_compilerSymbolBinding_t binding)
{
    switch(binding)
    {
    case SdvmCompSymbolBindingLocal: return SDVM_STB_LOCAL;
    case SdvmCompSymbolBindingWeak: return SDVM_STB_WEAK;
    default: return SDVM_STB_GLOBAL;
    }
}

static uint32_t sdvm_compilerElf64_mapSymbolKind(sdvm_compilerSymbolKind_t kind)
{
    switch(kind)
    {
    case SdvmCompSymbolKindFile: return SDVM_STT_FILE;
    case SdvmCompSymbolKindSection: return SDVM_STT_SECTION;
    case SdvmCompSymbolKindFunction: return SDVM_STT_FUNC;
    case SdvmCompSymbolKindVariable: return SDVM_STT_OBJECT;

    case SdvmCompSymbolKindNull:
    default: return SDVM_STT_NOTYPE;
    }
}

sdvm_compilerObjectFile_t *sdvm_compilerElf64_encode(sdvm_compiler_t *compiler)
{
    bool useRela = true;
    sdvm_compilerElfFileLayout_t layout = sdvm_compilerElf64_computeObjectFileLayout(compiler, useRela);
    sdvm_compilerObjectFile_t *objectFile = sdvm_compileObjectFile_allocate(layout.size);
    if(!objectFile)
        return NULL;

    sdvm_elf64_header_t *header = (sdvm_elf64_header_t *)(objectFile->data + layout.header);

    header->ident[SDVM_EI_MAG0] = 0x7f;
    header->ident[SDVM_EI_MAG1] = 'E';
    header->ident[SDVM_EI_MAG2] = 'L';
    header->ident[SDVM_EI_MAG3] = 'F';
    header->ident[SDVM_EI_CLASS] = SDVM_ELFCLASS64;
    header->ident[SDVM_EI_DATA] = SDVM_ELFDATA2LSB;
    header->ident[SDVM_EI_VERSION] = SDVM_ELFCURRENT_VERSION;
    header->type = SDVM_ET_REL;
    header->machine = (sdvm_elf64_half_t)compiler->target->elfMachine;
    header->flags = compiler->target->elfFlags;
    header->elfHeaderSize = sizeof(sdvm_elf64_header_t);
    header->version = SDVM_ELFCURRENT_VERSION;
    header->sectionHeaderEntrySize = sizeof(sdvm_elf64_sectionHeader_t);
    header->sectionHeaderNum = (sdvm_elf64_half_t)layout.sectionHeaderCount;
    header->sectionHeaderNameStringTableIndex = (sdvm_elf64_half_t)(layout.sectionHeaderCount - 1);
    header->sectionHeadersOffset = layout.sectionHeaders;

    sdvm_compilerElfStringSectionState_t sectionHeaderStrings = {
        .size = 1,
        .writeBuffer = (char*)(objectFile->data + layout.sectionHeaderStrings)
    };

    size_t writtenSectionHeaderCount = 1;

    // Section contents.
    sdvm_elf64_sectionHeader_t *sectionHeaders = (sdvm_elf64_sectionHeader_t*)(objectFile->data + layout.sectionHeaders);

    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        sdvm_elf64_sectionHeader_t *elfSection = sectionHeaders + writtenSectionHeaderCount++;
        elfSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, section->name);
        elfSection->type = SDVM_SHT_PROGBITS;
        elfSection->addressAlignment = section->alignment;
        elfSection->offset = layout.sectionContents[i];
        elfSection->size = section->contents.size;
        elfSection->entrySize = section->entrySize;

        if(section->flags & SdvmCompSectionFlagWrite)
            elfSection->flags |= SDVM_SHF_WRITE;
        if(section->flags & SdvmCompSectionFlagRead)
            elfSection->flags |= SDVM_SHF_ALLOC;
        if(section->flags & SdvmCompSectionFlagExec)
            elfSection->flags |= SDVM_SHF_EXECINSTR;
        if(section->flags & SdvmCompSectionFlagNoBits)
            elfSection->type = SDVM_SHT_NOBITS;
        if(section->flags & SdvmCompSectionFlagCStrings)
            elfSection->flags = SDVM_SHF_MERGE | SDVM_SHF_STRINGS;
        if(section->flags & SdvmCompSectionFlagUnwind)
        {
            if(compiler->target->elfMachine == SDVM_EM_X86_64)
                elfSection->type = SDVM_SHT_X86_64_UNWIND;
        }
        if(section->flags & SdvmCompSectionFlagTargetSpecificAttributes)
        {
            if(compiler->target->elfMachine == SDVM_EM_RISCV)
                elfSection->type = SDVM_SHT_RISCV_ATTRIBUTES;
        }

        if((section->flags & SdvmCompSectionFlagNoBits) == 0)
            memcpy(objectFile->data + layout.sectionContents[i], section->contents.data, section->contents.size);
    }

    // Section relocations.
    size_t relocatedSectionHeaderIndex = 1;
    sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        ++relocatedSectionHeaderIndex;
        if (section->relocations.size == 0)
            continue;

        sdvm_elf64_sectionHeader_t *elfSection = sectionHeaders + writtenSectionHeaderCount++;
        elfSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, useRela ? section->relaSectionName : section->relSectionName);
        elfSection->type = useRela ? SDVM_SHT_RELA : SDVM_SHT_REL;
        elfSection->addressAlignment = section->alignment;
        elfSection->offset = layout.relocationSectionContents[i];
        elfSection->info = (sdvm_elf64_word_t)relocatedSectionHeaderIndex - 1;
        elfSection->link = (sdvm_elf64_word_t)layout.symbolTableSectionIndex;
        elfSection->entrySize = useRela ? sizeof(sdvm_elf64_rela_t) : sizeof(sdvm_elf64_rel_t);
        elfSection->size = section->relocations.size * elfSection->entrySize;

        sdvm_compilerRelocation_t *relocationTable = (sdvm_compilerRelocation_t *)section->relocations.data;

        if(useRela)
        {
            sdvm_elf64_rela_t *relaTable = (sdvm_elf64_rela_t*) (objectFile->data + layout.relocationSectionContents[i]);
            for(size_t j = 0; j < section->relocations.size; ++j)
            {
                sdvm_compilerRelocation_t *relocationEntry = relocationTable + j;
                sdvm_elf64_rela_t *relaEntry = relaTable + j;
                uint32_t mappedRelocationType = compiler->target->mapElfRelocation(relocationEntry->kind);
                relaEntry->info = SDVM_ELF64_R_INFO(relocationEntry->symbol ? symbols[relocationEntry->symbol - 1].objectSymbolIndex : 0, mappedRelocationType);
                relaEntry->offset = relocationEntry->offset;
                relaEntry->addend = relocationEntry->addend;
            }
        }
        else
        {
            sdvm_elf64_rel_t *relTable = (sdvm_elf64_rel_t*) (objectFile->data + layout.relocationSectionContents[i]);
            (void)relTable;
        }
    }

    // Symbols
    if(compiler->symbolTable.symbols.size != 0)
    {
        sdvm_elf64_sectionHeader_t *symbolStringTableSection = sectionHeaders + layout.symbolStringTableSectionIndex;
        symbolStringTableSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, ".strtab");
        symbolStringTableSection->type = SDVM_SHT_STRTAB;
        symbolStringTableSection->offset = layout.symbolStringTable;
        symbolStringTableSection->size = compiler->symbolTable.strings.size;
        symbolStringTableSection->addressAlignment = 1;
        memcpy(objectFile->data + layout.symbolStringTable, compiler->symbolTable.strings.data, compiler->symbolTable.strings.size);

        sdvm_elf64_sectionHeader_t *symbolTableSection = sectionHeaders + layout.symbolTableSectionIndex;
        symbolTableSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, ".symtab");
        symbolTableSection->type = SDVM_SHT_SYMTAB;
        symbolTableSection->offset = layout.symbolTable;
        symbolTableSection->size = layout.symbolCount * sizeof(sdvm_elf64_symbol_t);
        symbolTableSection->entrySize = sizeof(sdvm_elf64_symbol_t);
        symbolTableSection->info = (sdvm_elf64_word_t)layout.localSymbolCount;
        symbolTableSection->link = (sdvm_elf64_word_t)layout.symbolStringTableSectionIndex;
        symbolTableSection->addressAlignment = 1;

        sdvm_elf64_symbol_t *elfSymbols = (sdvm_elf64_symbol_t*)(objectFile->data + layout.symbolTable);
        
        size_t compilerSymbolCount = compiler->symbolTable.symbols.size;
        for(size_t i = 0; i < compilerSymbolCount; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->binding == SdvmCompSymbolBindingLocal && symbol->section && !layout.writtenSections[symbol->section])
                continue;

            sdvm_elf64_symbol_t *elfSymbol = elfSymbols + symbol->objectSymbolIndex;
            elfSymbol->info = (uint8_t)(SDVM_ELF64_SYM_INFO(sdvm_compilerElf64_mapSymbolKind(symbol->kind), sdvm_compilerElf64_mapSymbolBinding(symbol->binding)));
            if(symbol->section && symbol->section < SDVM_COMPILER_SECTION_COUNT)
                elfSymbol->sectionHeaderIndex = layout.sectionIndices[symbol->section];
            elfSymbol->value = symbol->value;
            elfSymbol->name = symbol->name;
            elfSymbol->size = symbol->size;
        }
    }

    // Extra sections.
    sdvm_elf64_sectionHeader_t *noteGnuStackSection = sectionHeaders + layout.noteGnuStackSectionIndex;
    noteGnuStackSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, ".note.GNU-stack");
    noteGnuStackSection->type = SDVM_SHT_PROGBITS;
    noteGnuStackSection->addressAlignment = 1;

    // Section header strings
    sdvm_elf64_sectionHeader_t *sectionHeaderStringsSection = sectionHeaders + header->sectionHeaderNameStringTableIndex;
    sectionHeaderStringsSection->name = (sdvm_elf64_word_t)sdvm_compilerElfStringSection_write(&sectionHeaderStrings, ".shstrtab");
    sectionHeaderStringsSection->type = SDVM_SHT_STRTAB;
    sectionHeaderStringsSection->offset = layout.sectionHeaderStrings;
    sectionHeaderStringsSection->size = layout.sectionHeaderStringsSize;
    sectionHeaderStringsSection->addressAlignment = 1;

    return objectFile;
}

bool sdvm_compilerElf64_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerElf64_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, objectFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}

SDVM_API sdvm_compilerObjectFile_t *sdvm_compilerElf32_encode(sdvm_compiler_t *compiler)
{
    (void)compiler;
    abort();
}

SDVM_API bool sdvm_compilerElf32_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerElf32_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, objectFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}