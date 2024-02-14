#ifndef SDVM_ELF_H
#define SDVM_ELF_H

#include <stdint.h>

typedef uint64_t sdvm_elf64_addr_t;
typedef uint64_t sdvm_elf64_off_t;
typedef uint16_t sdvm_elf64_half_t;
typedef uint32_t sdvm_elf64_word_t;
typedef int32_t sdvm_elf64_sword_t;
typedef uint64_t sdvm_elf64_xword_t;
typedef int64_t sdvm_elf64_xsword_t;

enum {
    SDVM_EI_MAG0 = 0,
    SDVM_EI_MAG1 = 1,
    SDVM_EI_MAG2 = 2,
    SDVM_EI_MAG3 = 3,
    SDVM_EI_CLASS = 4,
    SDVM_EI_DATA = 5,
    SDVM_EI_VERSION = 6,
    SDVM_EI_OSABI = 7,
    SDVM_EI_ABIVERSION = 8,
    SDVM_EI_PAD = 9,
    SDVM_EI_NIDENT = 16,
};

enum {
    SDVM_ELFCLASS32 = 1,
    SDVM_ELFCLASS64 = 2,
};

enum {
    SDVM_ELFDATA2LSB = 1,
    SDVM_ELFDATA2MSB = 2,
};

enum {
    SDVM_ELFCURRENT_VERSION = 1
};

enum {
    SDVM_EM_X86_64 = 62
};

enum {
    SDVM_ET_NONE = 0,
    SDVM_ET_REL = 1,
    SDVM_ET_EXEC = 2,
    SDVM_ET_DYN = 3,
    SDVM_ET_CORE = 4,
};

enum {
    SDVM_SHF_WRITE = 1,
    SDVM_SHF_ALLOC = 2,
    SDVM_SHF_EXECINSTR = 4,
};

enum {
    SDVM_SHN_UNDEF = 0,
    SDVM_SHN_ABS = 0xFFF1,
    SDVM_SHN_COMMON = 0xFFF2,
};

enum {
    SDVM_SHT_NULL = 0,
    SDVM_SHT_PROGBITS = 1,
    SDVM_SHT_SYMTAB = 2,
    SDVM_SHT_STRTAB = 3,
    SDVM_SHT_RELA = 4,
    SDVM_SHT_HASH = 5,
    SDVM_SHT_DYNAMIC = 6,
    SDVM_SHT_NOTE = 7,
    SDVM_SHT_NOBITS = 8,
    SDVM_SHT_REL = 9,
    SDVM_SHT_SHLIB = 10,
    SDVM_SHT_DYNSYM = 11,

    SHT_X86_64_UNWIND = 0x70000001,
};

enum {
    SDVM_STB_LOCAL = 0,
    SDVM_STB_GLOBAL = 1,
    SDVM_STB_WEAK = 2,
};

enum {
    SDVM_STT_NOTYPE = 0,
    SDVM_STT_OBJECT = 1,
    SDVM_STT_FUNC = 2,
    SDVM_STT_SECTION = 3,
    SDVM_STT_FILE = 4,
};

#define SDVM_ELF64_SYM_INFO(type, binding) (((binding) << 4) | (type))

typedef struct sdvm_elf64_header_s
{
    uint8_t ident[16];
    sdvm_elf64_half_t type;
    sdvm_elf64_half_t machine;
    sdvm_elf64_word_t version;
    sdvm_elf64_addr_t entry;
    sdvm_elf64_off_t programHeadersOffset;
    sdvm_elf64_off_t sectionHeadersOffset;
    sdvm_elf64_word_t flags;
    sdvm_elf64_half_t elfHeaderSize;
    sdvm_elf64_half_t programHeaderEntrySize;
    sdvm_elf64_half_t programHeaderCount;
    sdvm_elf64_half_t sectionHeaderEntrySize;
    sdvm_elf64_half_t sectionHeaderNum;
    sdvm_elf64_half_t sectionHeaderNameStringTableIndex;
} sdvm_elf64_header_t;

typedef struct sdvm_elf64_sectionHeader_s
{
    sdvm_elf64_word_t name;
    sdvm_elf64_word_t type;
    sdvm_elf64_xword_t flags;
    sdvm_elf64_addr_t address;
    sdvm_elf64_off_t offset;
    sdvm_elf64_xword_t size;
    sdvm_elf64_word_t link;
    sdvm_elf64_word_t info;
    sdvm_elf64_xword_t addressAlignment;
    sdvm_elf64_xword_t entrySize;
} sdvm_elf64_sectionHeader_t;

typedef struct sdvm_elf64_symbol_s
{
    sdvm_elf64_word_t name;
    uint8_t info;
    uint8_t other;
    sdvm_elf64_half_t sectionHeaderIndex;
    sdvm_elf64_addr_t value;
    sdvm_elf64_xword_t size;
} sdvm_elf64_symbol_t;

#endif //SDVM_ELF_H
