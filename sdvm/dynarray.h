#ifndef SDVM_DYNARRAY_CONTEXT_H
#define SDVM_DYNARRAY_CONTEXT_H

#include <stddef.h>
#include <stdint.h>
#include "common.h"

typedef struct sdvm_dynarray_s
{
    size_t entrySize;
    size_t size;
    size_t capacity;
    uint8_t *data;
} sdvm_dynarray_t;

SDVM_API void sdvm_dynarray_initialize(sdvm_dynarray_t *dynarray, size_t entrySize, size_t initialCapacity);
SDVM_API size_t sdvm_dynarray_addAll(sdvm_dynarray_t *dynarray, size_t entryCount, const void *newEntries);
SDVM_API size_t sdvm_dynarray_add(sdvm_dynarray_t *dynarray, const void *newEntry);
SDVM_API void sdvm_dynarray_destroy(sdvm_dynarray_t *dynarray);

#define sdvm_dynarray_entryOfTypeAt(dynarray, entryType, index) (((entryType*)(dynarray).data) + index)

#endif //SDVM_DYNARRAY_CONTEXT_H