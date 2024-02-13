#ifndef SDVM_MODULE_H
#define SDVM_MODULE_H

#include <stdint.h>

#define SDVM_IM_FOUR_CC(c1, c2, c3, c4) ((c1) | ((c2) << 8) | ((c3) << 16) | ((c4) << 24))

typedef enum sdvm_moduleSectionType_e
{
    SdvmModuleSectionTypeNull = 0,
    SdvmModuleSectionTypeConstant = SDVM_IM_FOUR_CC('c', 'o', 'n', 't'),
    SdvmModuleSectionTypeText = SDVM_IM_FOUR_CC('t', 'e', 'x', 't'),
    SdvmModuleSectionTypeFunctionTable = SDVM_IM_FOUR_CC('f', 'u', 'n', 't'),

    SdvmModuleSectionTypeExportTable = SDVM_IM_FOUR_CC('e', 'x', 'p', 't'),
    SdvmModuleSectionTypeImportTable = SDVM_IM_FOUR_CC('i', 'm', 'p', 't'),

    SdvmModuleSectionTypeDebugLineStart = SDVM_IM_FOUR_CC('d', 'l', 'n', 's'),
    SdvmModuleSectionTypeDebugLineEnd = SDVM_IM_FOUR_CC('d', 'l', 'n', 'e'),
} sdvm_moduleSectionType_t;

typedef struct sdvm_moduleHeader_s
{
    char magic[4]; // SDVM
    uint32_t version;
    uint32_t pointerSize;
    uint32_t sectionHeaderCount;
} sdvm_moduleHeader_t;

typedef struct sdvm_moduleSectionHeader_s
{
    uint32_t type;
    uint32_t offset;
    uint32_t size;
} sdvm_moduleSectionHeader_t;

#endif //SDVM_MODULE_H
