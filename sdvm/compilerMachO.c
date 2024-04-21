#include "compiler.h"
#include "macho.h"
#include "utils.h"
#include <stdio.h>
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
    uint16_t sectionIndices[SDVM_COMPILER_SECTION_COUNT];
    bool writtenSections[SDVM_COMPILER_SECTION_COUNT];
    size_t commandsSize;
} sdvm_compilerMachOFileLayout_t;


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
