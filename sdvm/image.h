#ifndef SDVM_IMAGE_H
#define SDVM_IMAGE_H

#include <stdint.h>

#define SDVM_IM_FOUR_CC(c1, c2, c3, c4) ((c1) | ((c2) << 8) | ((c3) << 16) | ((c4) << 24))

typedef enum sdvm_imageSectionType_e
{
    SdvmImageSectionTypeNull = 0,
    SdvmImageSectionTypeConstant = SDVM_IM_FOUR_CC('c', 'o', 'n', 't'),
    SdvmImageSectionTypeText = SDVM_IM_FOUR_CC('t', 'e', 'x', 't'),
    SdvmImageSectionTypeFunctionTable = SDVM_IM_FOUR_CC('f', 'u', 'n', 't'),

    SdvmImageSectionTypeExportTable = SDVM_IM_FOUR_CC('e', 'x', 'p', 't'),
    SdvmImageSectionTypeImportTable = SDVM_IM_FOUR_CC('i', 'm', 'p', 't'),

    SdvmImageSectionTypeDebugLineStart = SDVM_IM_FOUR_CC('d', 'l', 'n', 's'),
    SdvmImageSectionTypeDebugLineEnd = SDVM_IM_FOUR_CC('d', 'l', 'n', 'e'),
} sdvm_imageSectionType_t;

typedef struct sdvm_imageHeader_s
{
    char magic[4]; // SDVM
    uint32_t version;
    uint32_t pointerSize;
    uint32_t sectionHeaderCount;
} sdvm_imageHeader_t;

typedef struct sdvm_imageSectionHeader_s
{
    uint32_t type;
    uint32_t offset;
    uint32_t size;
} sdvm_imageSectionHeader_t;

#endif //SDVM_IMAGE_H
