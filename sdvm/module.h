#ifndef SDVM_MODULE_H
#define SDVM_MODULE_H

#include <stdint.h>
#include <stddef.h>

#define SDVM_IM_FOUR_CC(c1, c2, c3, c4) ((c1) | ((c2) << 8) | ((c3) << 16) | ((c4) << 24))

typedef enum sdvm_moduleSectionType_e
{
    SdvmModuleSectionTypeNull = 0,
    SdvmModuleSectionTypeConstant = SDVM_IM_FOUR_CC('c', 'o', 'n', 't'),
    SdvmModuleSectionTypeText = SDVM_IM_FOUR_CC('t', 'e', 'x', 't'),
    SdvmModuleSectionTypeFunctionTable = SDVM_IM_FOUR_CC('f', 'u', 'n', 't'),

    SdvmModuleSectionTypeDebugLineStart = SDVM_IM_FOUR_CC('d', 'l', 'n', 's'),
    SdvmModuleSectionTypeDebugLineEnd = SDVM_IM_FOUR_CC('d', 'l', 'n', 'e'),
} sdvm_moduleSectionType_t;

typedef struct sdvm_moduleHeader_s
{
    char magic[4]; // SDVM
    uint32_t version;
    uint32_t pointerSize;
    uint32_t sectionHeaderCount;
    uint32_t entryPoint;
    uint32_t entryPointClosure;
} sdvm_moduleHeader_t;

typedef struct sdvm_moduleSectionHeader_s
{
    uint32_t type;
    uint32_t offset;
    uint32_t size;
} sdvm_moduleSectionHeader_t;

typedef struct sdvm_functionTableEntry_s
{
    uint32_t textSectionOffset;
    uint32_t textSectionSize;
} sdvm_functionTableEntry_t;

typedef struct sdvm_module_s
{
    sdvm_moduleHeader_t *header;

    size_t sectionHeaderCount;
    sdvm_moduleSectionHeader_t *sectionHeaders;

    size_t constSectionSize;
    uint8_t *constSectionData;

    size_t textSectionSize;
    uint8_t *textSectionData;

    size_t functionTableSize;
    sdvm_functionTableEntry_t *functionTable;

    size_t moduleDataSize;
    uint8_t *moduleData;
} sdvm_module_t;

sdvm_module_t *sdvm_module_loadFromMemory(size_t dataSize, uint8_t *data);
sdvm_module_t *sdvm_module_loadFromFileNamed(const char *fileName);
void sdvm_module_destroy(sdvm_module_t *module);
void sdvm_module_dumpFunction(sdvm_module_t *module, size_t index);
void sdvm_module_dump(sdvm_module_t *module);

#endif //SDVM_MODULE_H
