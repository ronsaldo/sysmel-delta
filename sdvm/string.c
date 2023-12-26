#include "string.h"
#include <string.h>

sdvm_string_t *sdvm_string_create(uint32_t size, const char *data)
{
    sdvm_string_t *string = SDVM_RC_ALLOCATE_WITH_VARIABLE_SIZE(sdvm_string_t, size, NULL);
    string->size = size;
    memcpy(string + 1, data, size);
    return string;   
}

sdvm_string_t *sdvm_string_fromCString(const char *cstring)
{
    return sdvm_string_create(strlen(cstring), cstring);
}
