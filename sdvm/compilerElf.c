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
    size_t relocationSectionContents[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionHeaderStringsSize;
    size_t sectionHeaderStrings;
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
        ++layout.sectionHeaderCount;

        layout.size = sdvm_compiler_alignSizeTo(layout.size, section->alignment);
        layout.sectionContents[i] = layout.size;
        layout.size += section->contents.size;
    }

    // Section relocations
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0 || section->relocations.size == 0)
            continue;

        layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(section->name);

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

    // Section header strings
    layout.sectionHeaderStringsSize += sdvm_compilerElf_computeNameStringSize(".shstr");
    layout.sectionHeaderStrings = layout.size;
    layout.size += layout.sectionHeaderStringsSize;
    ++layout.sectionHeaderCount;

    // Section headers.
    layout.sectionHeaders = layout.size;
    layout.size += sizeof(sdvm_elf64_sectionHeader_t) * layout.sectionHeaderCount;

    return layout;
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
    header->machine = SDVM_EM_X86_64;
    header->elfHeaderSize = sizeof(sdvm_elf64_header_t);
    header->version = SDVM_ELFCURRENT_VERSION;
    header->sectionHeaderEntrySize = sizeof(sdvm_elf64_sectionHeader_t);
    header->sectionHeaderNum = layout.sectionHeaderCount;
    header->sectionHeaderNameStringTableIndex = layout.sectionHeaderCount - 1;
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
        elfSection->name = sdvm_compilerElfStringSection_write(&sectionHeaderStrings, section->name);
        elfSection->type = SDVM_SHT_PROGBITS;
        elfSection->addressAlignment = section->alignment;
        elfSection->offset = layout.sectionContents[i];
        elfSection->size = section->contents.size;

        if(section->flags & SdvmCompSectionFlagWrite)
            elfSection->flags |= SDVM_SHF_WRITE;
        if(section->flags & SdvmCompSectionFlagRead)
            elfSection->flags |= SDVM_SHF_ALLOC;
        if(section->flags & SdvmCompSectionFlagExec)
            elfSection->flags |= SDVM_SHF_EXECINSTR;

        memcpy(objectFile->data + layout.sectionContents[i], section->contents.data, section->contents.size);
    }

    // Section relocations.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0 || section->relocations.size == 0)
            continue;

        sdvm_elf64_sectionHeader_t *elfSection = sectionHeaders + writtenSectionHeaderCount++;
        elfSection->name = sdvm_compilerElfStringSection_write(&sectionHeaderStrings, useRela ? section->relaSectionName : section->relSectionName);
        elfSection->type = useRela ? SDVM_SHT_RELA : SDVM_SHT_REL;
        elfSection->addressAlignment = section->alignment;
        elfSection->offset = layout.relocationSectionContents[i];
        elfSection->size = section->relocations.size;

        if(useRela)
        {
            sdvm_elf64_rela_t *relaTable = (sdvm_elf64_rela_t*) (objectFile->data + layout.relocationSectionContents[i]);
            (void)relaTable;
        }
        else
        {
            sdvm_elf64_rel_t *relTable = (sdvm_elf64_rel_t*) (objectFile->data + layout.relocationSectionContents[i]);
            (void)relTable;
        }
    }

    // Section header strings
    sdvm_elf64_sectionHeader_t *sectionHeaderStringsSection = sectionHeaders + header->sectionHeaderNameStringTableIndex;
    sectionHeaderStringsSection->name = sdvm_compilerElfStringSection_write(&sectionHeaderStrings, ".shstr");
    sectionHeaderStringsSection->type = SDVM_SHT_STRTAB;
    sectionHeaderStringsSection->offset = layout.sectionHeaderStrings;
    sectionHeaderStringsSection->size = layout.sectionHeaderStringsSize;

    return objectFile;
}

bool sdvm_compilerElf64_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *elfFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerElf64_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, elfFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}
