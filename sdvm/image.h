#ifndef SDVM_IMAGE_H
#define SDVM_IMAGE_H

#include <stdint.h>

typedef enum sdvm_imageSectionType_e
{
    SdvmImageSectionTypeNull = 0,
    SdvmImageSectionTypeConstant = 1,
    SdvmImageSectionTypeText = 2,
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
