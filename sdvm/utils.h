#ifndef SDVM_UTILS_H
#define SDVM_UTILS_H

#include <stdint.h>

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
#endif

#endif //SDVM_UTILS_H