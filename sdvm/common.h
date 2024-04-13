#ifndef SDVM_COMMON_H
#define SDVM_COMMON_H

#define SDVM_API

#ifdef __GNUC__
#   define SDVM_PACKED __attribute__((packed))
#else
#   define SDVM_PACKED
#endif

#endif //SDVM_COMMON_H