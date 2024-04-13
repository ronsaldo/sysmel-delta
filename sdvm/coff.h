#ifndef SDVM_COFF_H
#define SDVM_COFF_H

#include "common.h"
#include <stdint.h>

enum {
    SDVM_IMAGE_FILE_MACHINE_ARM = 0x1c0,
    SDVM_IMAGE_FILE_MACHINE_ARM64 = 0xaa64,
    SDVM_IMAGE_FILE_MACHINE_I386 = 0x14c,
    SDVM_IMAGE_FILE_MACHINE_AMD64 = 0x8664,
    SDVM_IMAGE_FILE_MACHINE_RISCV32 = 0x5032,
    SDVM_IMAGE_FILE_MACHINE_RISCV64 = 0x5064,
};

enum {
    SDVM_IMAGE_SCN_CNT_CODE = 0x00000020,
    SDVM_IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040,
    SDVM_IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080,

    SDVM_IMAGE_SCN_LNK_INFO = 0x00000200,
    SDVM_IMAGE_SCN_LNK_REMOVE = 0x00000800,
    SDVM_IMAGE_SCN_LNK_COMDAT = 0x00001000,

    SDVM_IMAGE_SCN_ALIGN_1BYTES = 0x00100000,

    SDVM_IMAGE_SCN_MEM_EXECUTE  = 0x20000000,
    SDVM_IMAGE_SCN_MEM_READ  = 0x40000000,
    SDVM_IMAGE_SCN_MEM_WRITE  = 0x80000000,
};

enum {
    SDVM_IMAGE_SYM_CLASS_NULL = 0,
    SDVM_IMAGE_SYM_CLASS_EXTERNAL = 2,
    SDVM_IMAGE_SYM_CLASS_STATIC = 3,
    SDVM_IMAGE_SYM_CLASS_FILE = 103,
    SDVM_IMAGE_SYM_CLASS_WEAK_EXTERNAL = 105,
};

typedef struct sdvm_coff_header_s
{
    uint16_t machine;
    uint16_t numberOfSections;
    uint32_t timeDateStamp;
    uint32_t pointerToSymbolTable;
    uint32_t numberOfSymbols;
    uint16_t sizeOfOptionalHeader;
    uint16_t characteristics;
} sdvm_coff_header_t;

typedef struct sdvm_coff_sectionHeader_s
{
    char name[8];
    uint32_t virtualSize;
    uint32_t virtualAddress;
    uint32_t sizeOfRawData;
    uint32_t pointerToRawData;
    uint32_t pointerToRelocations;
    uint32_t pointerToLineNumbers;
    uint16_t numberOfRelocations;
    uint16_t numberOfLineNumbers;
    uint32_t characteristics;
} sdvm_coff_sectionHeader_t;

#ifdef _MSC_VER
#pragma pack(push, 1)
#endif

typedef struct sdvm_coff_symbol_s
{
    union
    {
        char nameString[8];
        struct
        {
            uint32_t nameZero;
            uint32_t nameOffset;
        };
    };
    uint32_t value;

    uint16_t sectionNumber;
    uint16_t type;

    uint8_t storageClass;
    uint8_t numberOfAuxSymbols;
} SDVM_PACKED sdvm_coff_symbol_t;

#ifdef _MSC_VER
#pragma pack(pop)
#endif

#endif //SDVM_COFF_H
