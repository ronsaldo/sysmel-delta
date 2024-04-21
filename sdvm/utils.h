#ifndef SDVM_UTILS_H
#define SDVM_UTILS_H

#include "common.h"
#include <stdint.h>
#include <stdbool.h>

#define SDVM_C_ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

#define SDVM_TARGET_TRIPLE_COMPONENTS 4
#define SDVM_TARGET_TRIPLE_COMPONENT_SIZE 16

typedef enum sdvm_target_archicture_e
{
    SDVM_TARGET_ARCH_UNKNOWN = 0,
    SDVM_TARGET_ARCH_I686,
    SDVM_TARGET_ARCH_X86_64,
    SDVM_TARGET_ARCH_ARM,
    SDVM_TARGET_ARCH_AARCH64,
    SDVM_TARGET_ARCH_RISC_V_32,
    SDVM_TARGET_ARCH_RISC_V_64,
} sdvm_target_archicture_t;

typedef enum sdvm_target_subarchicture_e
{
    SDVM_TARGET_SUBARCH_NONE = 0,
    SDVM_TARGET_SUBARCH_ARMV6,
    SDVM_TARGET_SUBARCH_ARMV6A,
    SDVM_TARGET_SUBARCH_ARMV6K,
    SDVM_TARGET_SUBARCH_ARMV7K,
} sdvm_target_subarchicture_t;

typedef enum sdvm_target_os_e
{
    SDVM_TARGET_OS_UNKNOWN = 0,
    SDVM_TARGET_OS_NONE,
    SDVM_TARGET_OS_LINUX,
    SDVM_TARGET_OS_WINDOWS,
    SDVM_TARGET_OS_MACOSX,
} sdvm_target_os_t;

typedef enum sdvm_target_abi_e
{
    SDVM_TARGET_ABI_UNKNOWN = 0,
    SDVM_TARGET_ABI_MSVC,
    SDVM_TARGET_ABI_GNU,
    SDVM_TARGET_ABI_EABI,
} sdvm_target_abi_t;

typedef struct sdvm_targetDescription_s
{
    char architectureName[16];
    char osName[16];
    char vendorName[16];
    char abiName[16];
    sdvm_target_archicture_t architecture;
    sdvm_target_subarchicture_t subarchitecture;
    sdvm_target_os_t os;
    sdvm_target_abi_t abi;
} sdvm_targetDescription_t;

static inline bool sdvm_uint32_isPowerOfTwo(uint32_t x)
{
    // See https://stackoverflow.com/questions/600293/how-to-check-if-a-number-is-a-power-of-2
    return x != 0 && ((x & (x - 1)) == 0);
}

static inline bool sdvm_uint64_isPowerOfTwo(int32_t x)
{
    return x != 0 && ((x & (x - 1)) == 0);
}

#ifdef _MSC_VER
#error TODO
#else
static inline int sdvm_uint32_log2(uint32_t x)
{
    return 31 - __builtin_clz(x);
}

static inline int sdvm_uint64_log2(uint64_t x)
{
    return 31 - __builtin_clzl(x);
}

static inline int sdvm_uint32_ctz(uint32_t x)
{
    if(x == 0)
        return 32;
    return __builtin_ctz(x);
}

static inline int sdvm_uint64_ctz(uint64_t x)
{
    if(x == 0)
        return 64;
    return __builtin_ctz(x);
}
#endif

static inline size_t sdvm_size_alignedTo(size_t value, size_t alignment)
{
    return (value + alignment - 1) & (-alignment);
}

static inline uint32_t sdvm_uint32_alignedTo(uint32_t value, uint32_t alignment)
{
    return (value + alignment - 1) & (-alignment);
}

static inline uint64_t sdvm_uint64_alignedTo(uint64_t value, uint64_t alignment)
{
    return (value + alignment - 1) & (-alignment);
}

SDVM_API bool sdvm_targetDescription_parseTriple(sdvm_targetDescription_t *outParsedDescription, const char *triple);
SDVM_API bool sdvm_targetDescription_parseNames(sdvm_targetDescription_t *description);

#endif //SDVM_UTILS_H