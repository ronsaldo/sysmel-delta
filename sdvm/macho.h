#ifndef SDVM_MACHO_H
#define SDVM_MACHO_H

#include <stdint.h>

// Mach-O structures taken from the mach-o loader header (See https://opensource.apple.com/source/xnu/xnu-2050.18.24/EXTERNAL_HEADERS/mach-o/loader.h).
// This header is the only official "spec" that I could find about this file format.
#define	SDVM_MH_MAGIC 0xfeedface
#define	SDVM_MH_MAGIC_64 0xfeedfacf
#define	SDVM_MH_OBJECT 0x1

#define SDVM_MACHO_N_STAB 0xe0
#define SDVM_MACHO_N_PEXT 0x10
#define SDVM_MACHO_N_TYPE 0xe
#define SDVM_MACHO_N_EXT 0x1

#define SDVM_MACHO_N_UNDEF 0x2
#define SDVM_MACHO_N_ABS 0x2
#define SDVM_MACHO_N_SECT 0xe
#define SDVM_MACHO_N_PBUD 0xc
#define SDVM_MACHO_N_INDR 0xa

typedef enum sdvm_macho_cpu_type_e
{
    SDVM_MACHO_CPU_TYPE_ARCH_ABI64 = 0x01000000, 
    SDVM_MACHO_CPU_TYPE_X86 = 7,
    SDVM_MACHO_CPU_TYPE_I386 = SDVM_MACHO_CPU_TYPE_X86,
    SDVM_MACHO_CPU_TYPE_X86_64 = SDVM_MACHO_CPU_TYPE_X86 | SDVM_MACHO_CPU_TYPE_ARCH_ABI64,

    SDVM_MACHO_CPU_TYPE_ARM = 12,
    SDVM_MACHO_CPU_TYPE_ARM64 = SDVM_MACHO_CPU_TYPE_ARM | SDVM_MACHO_CPU_TYPE_ARCH_ABI64,
} sdvm_macho_cpu_type_t;

typedef enum sdvm_macho_cpu_subtype_e
{
    SDVM_MACHO_CPU_SUBTYPE_X86_ALL = 3, 
    SDVM_MACHO_CPU_SUBTYPE_ARM_ALL = 0,
} sdvm_macho_cpu_subtype_t;

typedef enum sdvm_macho_vmprot_e
{
    SDVM_MACHO_VMPROT_READ = 1,
    SDVM_MACHO_VMPROT_WRITE = 2,
    SDVM_MACHO_VMPROT_EXECUTE = 4,
} sdvm_macho_vmprot_t;

typedef enum sdvm_macho_load_command_e
{
    SDVM_MACHO_LC_REQ_DYLD = 0x80000000,

    SDVM_MACHO_LC_SEGMENT = 0x1,
    SDVM_MACHO_LC_SYMTAB = 0x2,
    SDVM_MACHO_LC_SYMSEG = 0x3,
    SDVM_MACHO_LC_THREAD = 0x4,
    SDVM_MACHO_LC_UNIXTHREAD = 0x5,
    SDVM_MACHO_LC_LOADFVMLIB = 0x6,
    SDVM_MACHO_LC_IDFVMLIB = 0x7,
    SDVM_MACHO_LC_IDENT = 0x8,
    SDVM_MACHO_LC_FVMFILE = 0x9,
    SDVM_MACHO_LC_PREPAGE = 0xa,
    SDVM_MACHO_LC_DYSYMTAB = 0xb,
    SDVM_MACHO_LC_LOAD_DYLIB = 0xc,
    SDVM_MACHO_LC_ID_DYLIB = 0xd,
    SDVM_MACHO_LC_LOAD_DYLINKER = 0xe,
    SDVM_MACHO_LC_ID_DYLINKER = 0xf,
    SDVM_MACHO_LC_PREBOUND_DYLIB = 0x10,

    SDVM_MACHO_LC_ROUTINES = 0x11,
    SDVM_MACHO_LC_SUB_FRAMEWORK = 0x12,
    SDVM_MACHO_LC_SUB_UMBRELLA = 0x13,
    SDVM_MACHO_LC_SUB_CLIENT = 0x14,
    SDVM_MACHO_LC_SUB_LIBRARY = 0x15,
    SDVM_MACHO_LC_TWOLEVEL_HINTS = 0x16,
    SDVM_MACHO_LC_PREBIND_CKSUM = 0x17,

    SDVM_MACHO_LC_SEGMENT_64 = 0x19,
    SDVM_MACHO_LC_ROUTINES_64 = 0x1a,
    SDVM_MACHO_LC_UUID = 0x1b,
    SDVM_MACHO_LC_RPATH = (0x1c | SDVM_MACHO_LC_REQ_DYLD),
    SDVM_MACHO_LC_CODE_SIGNATURE = 0x1d,
    SDVM_MACHO_LC_SEGMENT_SPLIT_INFO = 0x1e,
    SDVM_MACHO_LC_REEXPORT_DYLIB = (0x1f | SDVM_MACHO_LC_REQ_DYLD),
    SDVM_MACHO_LC_LAZY_LOAD_DYLIB = 0x20,
    SDVM_MACHO_LC_ENCRYPTION_INFO = 0x21,
    SDVM_MACHO_LC_DYLD_INFO = 0x22,
    SDVM_MACHO_LC_DYLD_INFO_ONLY = (0x22|SDVM_MACHO_LC_REQ_DYLD),
    SDVM_MACHO_LC_LOAD_UPWARD_DYLIB = (0x23 | SDVM_MACHO_LC_REQ_DYLD),
    SDVM_MACHO_LC_VERSION_MIN_MACOSX = 0x24,
    SDVM_MACHO_LC_VERSION_MIN_IPHONEOS = 0x25,
    SDVM_MACHO_LC_FUNCTION_STARTS = 0x26,
    SDVM_MACHO_LC_DYLD_ENVIRONMENT = 0x27,
    SDVM_MACHO_LC_MAIN = (0x28|SDVM_MACHO_LC_REQ_DYLD),
    SDVM_MACHO_LC_DATA_IN_CODE = 0x29,
    SDVM_MACHO_LC_SOURCE_VERSION = 0x2A,
    SDVM_MACHO_LC_DYLIB_CODE_SIGN_DRS = 0x2B,
} sdvm_macho_load_command_t;

typedef enum sdvm_macho_section_flags_e
{
    SDVM_MACHO_S_ZEROFILL = 1,
    SDVM_MACHO_S_ATTR_SOME_INSTRUCTIONS = 0x00000400,
    SDVM_MACHO_S_ATTR_PURE_INSTRUCTIONS = 0x80000000,
    SDVM_MACHO_S_ATTR_DEBUG = 1<<25,
    SDVM_MACHO_S_ATTR_EXT_RELOC = 1<<9,
    SDVM_MACHO_S_ATTR_LOC_RELOC = 1<<8,
} sdvm_macho_section_flags_t;

typedef enum sdvm_macho_symbol_type_e
{
    SDVM_MACHO_SYMBOL_TYPE_UNDEF = 0,
    SDVM_MACHO_SYMBOL_TYPE_EXTERNAL = 1,
    SDVM_MACHO_SYMBOL_TYPE_ABS = 2,
    SDVM_MACHO_SYMBOL_TYPE_SECTION = 0xe,
    SDVM_MACHO_SYMBOL_TYPE_PREBOUND_UNDEFINED = 0xc,
    SDVM_MACHO_SYMBOL_TYPE_INDIRECT = 0xa,
} sdvm_macho_symbol_type_t;

typedef enum sdvm_reloc_type_generic_e
{
    SDVM_MACHO_GENERIC_RELOC_VANILLA,
    SDVM_MACHO_GENERIC_RELOC_PAIR,
    SDVM_MACHO_GENERIC_RELOC_SECTDIFF,
    SDVM_MACHO_GENERIC_RELOC_PB_LA_PTR,
    SDVM_MACHO_GENERIC_RELOC_LOCAL_SECTDIFF,
} sdvm_reloc_type_generic_t;

typedef enum sdvm_reloc_type_x86_64_e
{
    SDVM_MACHO_X86_64_UNSIGNED,
    SDVM_MACHO_X86_64_SIGNED,
    SDVM_MACHO_X86_64_BRANCH,
    SDVM_MACHO_X86_64_GOT_LOAD,
    SDVM_MACHO_X86_64_GOT,
    SDVM_MACHO_X86_64_SUBTRACTOR,
    SDVM_MACHO_X86_64_SIGNED_1,
    SDVM_MACHO_X86_64_SIGNED_2,
    SDVM_MACHO_X86_64_SIGNED_4,
} sdvm_reloc_type_x86_64_t;

typedef enum sdvm_reloc_type_arm64_e
{
    SDVM_MACHO_ARM64_RELOC_UNSIGNED,
    SDVM_MACHO_ARM64_RELOC_SUBTRACTOR,
    SDVM_MACHO_ARM64_RELOC_BRANCH26,
    SDVM_MACHO_ARM64_RELOC_PAGE21,
    SDVM_MACHO_ARM64_RELOC_PAGEOFF12,
    SDVM_MACHO_ARM64_RELOC_GOT_LOAD_PAGE21,
    SDVM_MACHO_ARM64_RELOC_GOT_LOAD_PAGE12,
    SDVM_MACHO_ARM64_RELOC_POINTER_TO_GOT,
    SDVM_MACHO_ARM64_RELOC_TLVP_LOAD_PAGE21,
    SDVM_MACHO_ARM64_RELOC_TLVP_LOAD_PAGEOFF12,
    SDVM_MACHO_ARM64_RELOC_ADDEND,
} sdvm_reloc_type_arm64_t;

typedef struct sdvm_macho_header_s
{
	uint32_t	magic;
	uint32_t	cputype;
	uint32_t	cpusubtype;
	uint32_t	filetype;
	uint32_t	ncmds;
	uint32_t	sizeofcmds;
	uint32_t	flags;
} sdvm_macho_header_t;

typedef struct sdvm_macho64_header_s
{
	uint32_t	magic;
	uint32_t	cputype;
	uint32_t	cpusubtype;
	uint32_t	filetype;
	uint32_t	ncmds;
	uint32_t	sizeofcmds;
	uint32_t	flags;
	uint32_t	reserved;
} sdvm_macho64_header_t;

typedef struct sdvm_macho_load_command_header_s
{
	uint32_t cmd;
	uint32_t cmdsize;
} sdvm_macho_load_command_header_t;

typedef struct sdvm_segment_command_s
{
	uint32_t	cmd;
	uint32_t	cmdsize;
	char		segname[16];
	uint32_t	vmaddr;
	uint32_t	vmsize;
	uint32_t	fileoff;
	uint32_t	filesize;
	uint32_t    maxprot;
	uint32_t    initprot;
	uint32_t	nsects;
	uint32_t	flags;
} sdvm_segment_command_t;

typedef struct sdvm_macho64_segment_command_s
{
	uint32_t	cmd;
	uint32_t	cmdsize;
	char		segname[16];
	uint64_t	vmaddr;
	uint64_t	vmsize;
	uint64_t	fileoff;
	uint64_t	filesize;
	uint32_t	maxprot;
	uint32_t	initprot;
	uint32_t	nsects;
	uint32_t	flags;
} sdvm_macho64_segment_command_t;

typedef struct sdvm_macho_section_s {
	char		sectname[16];
	char		segname[16];
	uint32_t	addr;
	uint32_t	size;
	uint32_t	offset;
	uint32_t	align;
	uint32_t	reloff;
	uint32_t	nreloc;
	uint32_t	flags;
	uint32_t	reserved1;
	uint32_t	reserved2;
} sdvm_macho_section_t;

typedef struct sdvm_macho64_section_s {
	char		sectname[16];
	char		segname[16];
	uint64_t	addr;
	uint64_t	size;
	uint32_t	offset;
	uint32_t	align;
	uint32_t	reloff;
	uint32_t	nreloc;
	uint32_t	flags;
	uint32_t	reserved1;
	uint32_t	reserved2;
	uint32_t	reserved3;
} sdvm_macho64_section_t;

typedef struct sdvm_symtab_command_s
{
	uint32_t	cmd;
	uint32_t	cmdsize;
	uint32_t	symoff;
	uint32_t	nsyms;
	uint32_t	stroff;
	uint32_t	strsize;
} sdvm_symtab_command_t;

typedef struct sdvm_dysymtab_command_s
{
    uint32_t cmd;
    uint32_t cmdsize;

    uint32_t ilocalsym;
    uint32_t nlocalsym;

    uint32_t iextdefsym;
    uint32_t nextdefsym;

    uint32_t iundefsym;
    uint32_t nundefsym;

    uint32_t tocoff;
    uint32_t ntoc;

    uint32_t modtaboff;
    uint32_t nmodtab;

    uint32_t extrefsymoff;
    uint32_t nextrefsyms;

    uint32_t indirectsymoff;
    uint32_t nindirectsyms;

    uint32_t extreloff;
    uint32_t nextrel;

    uint32_t locreloff;
    uint32_t nlocrel;
} sdvm_dysymtab_command_t;

typedef struct sdvm_macho_nlist_s
{
	uint32_t n_strx;
	uint8_t  n_type;
	uint8_t  n_sect;
	int16_t  n_desc;
	uint32_t n_value;
} sdvm_macho_nlist_t;

typedef struct sdvm_macho64_nlist_s
{
    uint32_t n_strx;
    uint8_t  n_type;
    uint8_t  n_sect;
    uint16_t n_desc;
    uint64_t n_value;
} sdvm_macho64_nlist_t;

typedef struct sdvm_macho_relocation_info_s
{
    int32_t r_address;
    uint32_t r_symbolnum: 24, r_pcrel: 1, r_length: 2, r_extern: 1, r_type: 4;
} sdvm_macho_relocation_info_t;

#endif //SDVM_MACHO_H