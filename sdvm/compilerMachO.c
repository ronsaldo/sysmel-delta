#include "compiler.h"
#include "macho.h"
#include "utils.h"
#include "assert.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct sdvm_compilerMachOFileLayout_s
{
    size_t size;
    size_t header;
    size_t objectSegment;
    size_t objectSegmentCommandSize;
    uint64_t objectSegmentAddress;
    uint64_t objectSegmentAddressSize;
    size_t objectSegmentOffset;
    size_t objectSegmentSize;
    size_t sectionHeaders[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionHeaderCount;
    size_t sectionContents[SDVM_COMPILER_SECTION_COUNT];
    uint64_t sectionAddresses[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionRelocations[SDVM_COMPILER_SECTION_COUNT];
    size_t sectionRelocationCount[SDVM_COMPILER_SECTION_COUNT];
    uint16_t sectionIndices[SDVM_COMPILER_SECTION_COUNT];
    bool writtenSections[SDVM_COMPILER_SECTION_COUNT];
    size_t symbolTableCommand;
    size_t dySymbolTableCommand;
    size_t commandsSize;
    size_t symbolCount;
    size_t symbolTable;
    size_t stringTable;
    size_t stringTableSize;
} sdvm_compilerMachOFileLayout_t;

typedef enum sdvm_compilerMachOSymbolCategory_e
{
    SdvmCompMachOSymbolCategoryLocal = 0,
    SdvmCompMachOSymbolCategoryExternalDefined,
    SdvmCompMachOSymbolCategoryExternalUndefined,
} sdvm_compilerMachOSymbolCategory_t;

typedef struct sdvm_compilerMachOSymbol_s
{
    int category;
    size_t index;
    const char *name;
    sdvm_compilerSymbol_t *symbol;
} sdvm_compilerMachOSymbol_t;

typedef struct sdvm_compilerMachStringTableState_s
{
    char *writeBuffer;
    size_t size;
} sdvm_compilerMachStringTableState_t;

int sdvm_compilerMachOSymbol_sortCompare(const void *a, const void *b)
{
    sdvm_compilerMachOSymbol_t *left = (sdvm_compilerMachOSymbol_t*)a;
    sdvm_compilerMachOSymbol_t *right = (sdvm_compilerMachOSymbol_t*)b;
    if(left->category != right->category)
        return left->category - right->category;
    
    if(!left->name && !right->name)
        return left->index - right->index;
    return strcmp(left->name, right->name);
}

static size_t sdvm_compilerMachO_computeNameStringSize(const char *string)
{
    if(!string)
        return 0;

    size_t stringLength = strlen(string);
    if(stringLength == 0)
        return 0;

    return stringLength + 1;
}

static size_t sdvm_compilerMachOStringTable_write(sdvm_compilerMachStringTableState_t *stringTable, const char *string)
{
    if(!string || !*string)
        return 0;
    
    size_t stringLength = strlen(string);
    size_t result = stringTable->size;
    memcpy(stringTable->writeBuffer + result, string, stringLength);
    stringTable->size += stringLength + 1;
    return result;
}

static sdvm_compilerMachOFileLayout_t sdvm_compilerMachO64_computeObjectFileLayout(sdvm_compiler_t *compiler)
{
    sdvm_compilerMachOFileLayout_t layout = {0};

    layout.header = 0;
    layout.size += sizeof(sdvm_macho64_header_t);

    // __OBJECT segment.
    layout.objectSegment = layout.size;
    layout.size += sizeof(sdvm_macho64_segment_command_t);

    // Count the sections, and write their headers.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0)
            continue;

        layout.sectionIndices[i] = ++layout.sectionHeaderCount;
        layout.writtenSections[i] = true;
        layout.sectionHeaders[i] = layout.size;
        layout.size += sizeof(sdvm_macho64_section_t);
    }

    layout.objectSegmentCommandSize = layout.size - layout.objectSegment;

    // Symbol tables
    if(compiler->symbolTable.symbols.size != 0)
    {
        layout.symbolTableCommand = layout.size;
        layout.size += sizeof(sdvm_symtab_command_t);

        layout.dySymbolTableCommand = layout.size;
        layout.size += sizeof(sdvm_dysymtab_command_t);
    }

    // End the commands size.
    layout.commandsSize = layout.size - layout.objectSegment;

    // Place the section contents.
    uint64_t baseAddress = 0;
    bool isFirstWrittenSection = true;
    layout.objectSegmentAddress = baseAddress;
    layout.objectSegmentOffset = layout.size;
    uint32_t objectSegmentAlignment = 1;
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        if(!layout.writtenSections[i])
            continue;

        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        layout.size = sdvm_size_alignedTo(layout.size, section->alignment);
        baseAddress = sdvm_uint64_alignedTo(baseAddress, section->alignment);
        if(section->alignment > objectSegmentAlignment)
            objectSegmentAlignment = section->alignment;

        if(isFirstWrittenSection)
        {
            layout.objectSegmentAddress = baseAddress;
            layout.objectSegmentOffset = layout.size;
            isFirstWrittenSection = false;
        }

        layout.sectionAddresses[i] = baseAddress;
        baseAddress += section->contents.size;

        if((section->flags & SdvmCompSectionFlagNoBits) == 0)
        {
            layout.sectionContents[i] = layout.size;
            layout.size += section->contents.size;
        }
    }

    layout.size = sdvm_size_alignedTo(layout.size, objectSegmentAlignment);
    baseAddress = sdvm_uint64_alignedTo(baseAddress, objectSegmentAlignment);
    layout.objectSegmentAddressSize = baseAddress - layout.objectSegmentAddress;
    layout.objectSegmentSize = layout.size - layout.objectSegmentOffset;

    // Section relocations
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        if(section->contents.size == 0 || section->relocations.size == 0 || !layout.writtenSections[i])
            continue;

        layout.sectionRelocations[i] = layout.size;
        layout.sectionRelocationCount[i] = 0;
        sdvm_compilerRelocation_t *relocations = (sdvm_compilerRelocation_t*)section->relocations.data;
        for(size_t j = 0; j < section->relocations.size; ++j)
            layout.sectionRelocationCount[i] += compiler->target->countMachORelocations(relocations[j].kind);

        layout.size += layout.sectionRelocationCount[i]*sizeof(sdvm_macho_relocation_info_t);
    }

    // Symbols
    if(compiler->symbolTable.symbols.size != 0)
    {
        layout.symbolCount = 0;
        layout.stringTableSize = 1;
        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        for(size_t i = 0; i < compiler->symbolTable.symbols.size; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->section && (compiler->sections[symbol->section].flags & SdvmCompSectionFlagDebug))
                continue;

            if(symbol->binding == SdvmCompSymbolBindingLocal)
            {
                if(symbol->section && layout.writtenSections[symbol->section])
                {
                    layout.stringTableSize += sdvm_compilerMachO_computeNameStringSize((char*)compiler->symbolTable.strings.data + symbol->name);
                    ++layout.symbolCount;
                }
            }
            else
            {
                layout.stringTableSize += sdvm_compilerMachO_computeNameStringSize((char*)compiler->symbolTable.strings.data + symbol->name);
                ++layout.symbolCount;
            }
        }

        layout.symbolTable = layout.size;
        layout.size += layout.symbolCount * sizeof(sdvm_macho64_nlist_t);
    }

    layout.stringTable = layout.size;
    layout.size += layout.stringTable;

    return layout;
}

sdvm_compilerObjectFile_t *sdvm_compilerMachO64_encode(sdvm_compiler_t *compiler)
{
    sdvm_compilerMachOFileLayout_t layout = sdvm_compilerMachO64_computeObjectFileLayout(compiler);
    sdvm_compilerObjectFile_t *objectFile = sdvm_compileObjectFile_allocate(layout.size);
    if(!objectFile)
        return NULL;

    const sdvm_compilerTarget_t *target = compiler->target;

    sdvm_macho64_header_t *header = (sdvm_macho64_header_t *)(objectFile->data + layout.header);
    header->magic = SDVM_MH_MAGIC_64;
    header->cputype = target->machoCpuType;
    header->cpusubtype = target->machoCpuSubtype;
    header->filetype = SDVM_MH_OBJECT;
    header->ncmds = 1;
    header->sizeofcmds = layout.commandsSize;

    sdvm_macho64_segment_command_t *objectSegment = (sdvm_macho64_segment_command_t *)(objectFile->data + layout.objectSegment);
    objectSegment->cmd = SDVM_MACHO_LC_SEGMENT_64;
    objectSegment->cmdsize = layout.objectSegmentCommandSize;
    objectSegment->nsects = layout.sectionHeaderCount;
    objectSegment->vmaddr = layout.objectSegmentAddress;
    objectSegment->vmsize = layout.objectSegmentAddressSize;
    objectSegment->fileoff = layout.objectSegmentOffset;
    objectSegment->filesize = layout.objectSegmentSize;
    strncpy(objectSegment->segname, "__OBJECT", sizeof(objectSegment->segname));

    // Write the section headers.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        if(!layout.writtenSections[i])
            continue;

        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        sdvm_macho64_section_t *machoSection = (sdvm_macho64_section_t *)(objectFile->data + layout.sectionHeaders[i]);
        machoSection->addr = layout.sectionAddresses[i];
        machoSection->size = section->contents.size;
        machoSection->align = sdvm_uint32_log2(section->alignment);
        machoSection->nreloc = layout.sectionRelocationCount[i];
        machoSection->reloff = layout.sectionRelocations[i];
        strncpy(machoSection->sectname, section->machoSectionName, sizeof(objectSegment->segname));
        strncpy(machoSection->segname, section->machoSegmentName, sizeof(objectSegment->segname));

        if(section->flags & SdvmCompSectionFlagWrite)
        {
            objectSegment->initprot |= SDVM_MACHO_VMPROT_WRITE;
            objectSegment->maxprot |= SDVM_MACHO_VMPROT_WRITE;
        }

        if(section->flags & SdvmCompSectionFlagRead)
        {
            objectSegment->initprot |= SDVM_MACHO_VMPROT_READ;
            objectSegment->maxprot |= SDVM_MACHO_VMPROT_READ;
        }

        if(section->flags & SdvmCompSectionFlagExec)
        {
            machoSection->flags |= SDVM_MACHO_S_ATTR_SOME_INSTRUCTIONS | SDVM_MACHO_S_ATTR_PURE_INSTRUCTIONS;
            objectSegment->initprot |= SDVM_MACHO_VMPROT_EXECUTE;
            objectSegment->maxprot |= SDVM_MACHO_VMPROT_EXECUTE;
        }

        if(section->flags & SdvmCompSectionFlagNoBits)
        {
            machoSection->flags |= SDVM_MACHO_S_ZEROFILL;
        }
        else
        {
            machoSection->offset = layout.sectionContents[i];
            memcpy(objectFile->data + layout.sectionContents[i], section->contents.data, section->contents.size);
        }

        if(section->flags & SdvmCompSectionFlagDebug)
            machoSection->flags |= SDVM_MACHO_S_ATTR_DEBUG;
    }
    
    // Symbol tables
    if(compiler->symbolTable.symbols.size != 0)
    {
        sdvm_compilerMachStringTableState_t stringTable = {
            .size = 1,
            .writeBuffer = (char*)(objectFile->data + layout.stringTable)
        };

        // Make a list with the symbols so that we can group and sort them.
        sdvm_compilerMachOSymbol_t *sortingSymbols = calloc(layout.symbolCount, sizeof(sdvm_compilerMachOSymbol_t));
        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        size_t sortingSymbolCount = 0;
        for(size_t i = 0; i < compiler->symbolTable.symbols.size; ++i)
        {
            sdvm_compilerSymbol_t *symbol = symbols + i;
            if(symbol->section && (compiler->sections[symbol->section].flags & SdvmCompSectionFlagDebug))
                continue;

            if(symbol->binding == SdvmCompSymbolBindingLocal)
            {
                if(symbol->section && layout.writtenSections[symbol->section])
                {
                    sdvm_compilerMachOSymbol_t *sortingSymbol = sortingSymbols + sortingSymbolCount++;
                    sortingSymbol->category = SdvmCompMachOSymbolCategoryLocal;
                    sortingSymbol->index = i;
                    sortingSymbol->name = (char*)compiler->symbolTable.strings.data + symbol->name;
                    sortingSymbol->symbol = symbol;
                }
            }
            else
            {
                sdvm_compilerMachOSymbol_t *sortingSymbol = sortingSymbols + sortingSymbolCount++;
                sortingSymbol->category = symbol->section ? SdvmCompMachOSymbolCategoryExternalDefined : SdvmCompMachOSymbolCategoryExternalUndefined;
                sortingSymbol->index = i;
                sortingSymbol->name = (char*)compiler->symbolTable.strings.data + symbol->name;
                sortingSymbol->symbol = symbol;
            }
        }
        SDVM_ASSERT(layout.symbolCount == sortingSymbolCount);

        qsort(sortingSymbols, sortingSymbolCount, sizeof(sdvm_compilerMachOSymbol_t), sdvm_compilerMachOSymbol_sortCompare);

        header->ncmds += 2;
        sdvm_symtab_command_t *symtabCommand = (sdvm_symtab_command_t*)(objectFile->data + layout.symbolTableCommand);
        symtabCommand->cmd = SDVM_MACHO_LC_SYMTAB;
        symtabCommand->cmdsize = sizeof(sdvm_symtab_command_t);
        symtabCommand->nsyms = layout.symbolCount;
        symtabCommand->symoff = layout.symbolTable;
        symtabCommand->stroff = layout.stringTable;
        symtabCommand->strsize = layout.stringTableSize;

        sdvm_dysymtab_command_t *dySymtabCommand = (sdvm_dysymtab_command_t*)(objectFile->data + layout.dySymbolTableCommand);
        dySymtabCommand->cmd = SDVM_MACHO_LC_DYSYMTAB;
        dySymtabCommand->cmdsize = sizeof(sdvm_dysymtab_command_t);

        bool hasSeenFirstLocal = false;
        bool hasSeenFirstExternalDefined = false;
        bool hasSeenFirstExternalUndefined = false;
        sdvm_macho64_nlist_t *machoSymbols = (sdvm_macho64_nlist_t*)(objectFile->data + layout.symbolTable);
        for(size_t i = 0; i < sortingSymbolCount; ++i)
        {
            sdvm_compilerMachOSymbol_t *sortingSymbol = sortingSymbols + i;
            sdvm_compilerSymbol_t *symbol = sortingSymbol->symbol;
            sdvm_macho64_nlist_t *machoSymbol = machoSymbols + i;

            machoSymbol->n_value = symbol->value;
            if(symbol->binding != SdvmCompSymbolBindingLocal)
                machoSymbol->n_type |= SDVM_MACHO_N_EXT;

            if(symbol->section)
            {
                machoSymbol->n_sect = layout.sectionIndices[symbol->section];
                machoSymbol->n_type |= SDVM_MACHO_N_SECT;
            }
            symbol->objectSymbolIndex = i;
            machoSymbol->n_strx = sdvm_compilerMachOStringTable_write(&stringTable, sortingSymbol->name);
            switch(sortingSymbol->category)
            {
            case SdvmCompMachOSymbolCategoryLocal:
                if(!hasSeenFirstLocal)
                {
                    dySymtabCommand->ilocalsym = i;
                    hasSeenFirstLocal = true;
                }
                ++dySymtabCommand->nlocalsym;
                break;
            case SdvmCompMachOSymbolCategoryExternalDefined:
                if(!hasSeenFirstExternalDefined)
                {
                    dySymtabCommand->iextdefsym = i;
                    hasSeenFirstExternalDefined = true;
                }
                ++dySymtabCommand->nextdefsym;
                break;
            case SdvmCompMachOSymbolCategoryExternalUndefined:
                if(!hasSeenFirstExternalUndefined)
                {
                    dySymtabCommand->iundefsym = i;
                    hasSeenFirstExternalUndefined = true;
                }
                ++dySymtabCommand->nundefsym;
                break;
            }
        }

        free(sortingSymbols);
    }

    // Convert the relocations.
    for(size_t i = 1; i < SDVM_COMPILER_SECTION_COUNT; ++i)
    {
        if(!layout.writtenSections[i])
            continue;

        sdvm_compilerObjectSection_t *section = compiler->sections + i;
        sdvm_macho64_section_t *machoSection = (sdvm_macho64_section_t *)(objectFile->data + layout.sectionHeaders[i]);
        if(section->relocations.size == 0)
            continue;

        sdvm_compilerSymbol_t *symbols = (sdvm_compilerSymbol_t*)compiler->symbolTable.symbols.data;
        sdvm_macho_relocation_info_t *machRelocations = (sdvm_macho_relocation_info_t*)(objectFile->data + layout.sectionRelocations[i]);

        sdvm_compilerRelocation_t *relocations = (sdvm_compilerRelocation_t*)section->relocations.data;
        for(size_t j = 0; j < section->relocations.size; ++j)
        {
            sdvm_compilerRelocation_t *relocationEntry = relocations + j; 
            machRelocations->r_address = relocationEntry->offset;
            int64_t symbolAddend = 0;
            if(relocations->symbol)
            {
                sdvm_compilerSymbol_t *symbol = symbols + relocationEntry->symbol - 1;
                if(symbol->binding == SdvmCompSymbolBindingLocal && (symbol->objectSymbolIndex == 0 || (section->flags & SdvmCompSectionFlagDebug)))
                {
                    symbolAddend = symbol->value;
                    machRelocations->r_extern = 0;
                    machRelocations->r_symbolnum = layout.sectionIndices[symbol->section];
                }
                else
                {
                    machRelocations->r_extern = 1;
                    machRelocations->r_symbolnum = symbol->objectSymbolIndex;
                }
            }

            if(machRelocations->r_extern)
                machoSection->flags |= SDVM_MACHO_S_ATTR_EXT_RELOC;
            else
                machoSection->flags |= SDVM_MACHO_S_ATTR_LOC_RELOC;
                
            machRelocations += target->mapMachORelocation(relocationEntry, symbolAddend, machoSection->addr, objectFile->data + layout.sectionContents[i] + relocationEntry->offset, machRelocations);
        }
    }

    return objectFile;
}

bool sdvm_compilerMachO64_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerMachO64_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, objectFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}

sdvm_compilerObjectFile_t *sdvm_compilerMachO32_encode(sdvm_compiler_t *compiler)
{
    (void)compiler;
    return NULL;
}

bool sdvm_compilerMachO32_encodeObjectAndSaveToFileNamed(sdvm_compiler_t *compiler, const char *objectFileName)
{
    sdvm_compilerObjectFile_t *objectFile = sdvm_compilerMachO32_encode(compiler);
    if(!objectFile)
        return false;

    bool succeeded = sdvm_compileObjectFile_saveToFileNamed(objectFile, objectFileName);
    sdvm_compileObjectFile_destroy(objectFile);
    return succeeded;
}
