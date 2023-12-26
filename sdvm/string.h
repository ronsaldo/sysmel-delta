#ifndef SDVM_STRING_H
#define SDVM_STRING_H

#include "rc.h"

typedef struct sdvm_string_s
{
    sdvm_rc_t super;
    size_t size;
} sdvm_string_t;

typedef sdvm_string_t sdvm_symbol_t;

sdvm_string_t *sdvm_string_create(uint32_t size, const char *data);
sdvm_string_t *sdvm_string_fromCString(const char *cstring);

#endif //SDVM_STRING_H
