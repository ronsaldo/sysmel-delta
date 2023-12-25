#include "rc.h"
#include <stdlib.h>

static void sdvm_rc_trivialfinalize(void*)
{
    // Do nothing
}

void *sdvm_rc_allocate(size_t size, sdvm_finalize_t finalize)
{
    sdvm_rc_t *result = calloc(1, size);
    result->count = 1;
    result->finalize = finalize ? finalize : sdvm_rc_trivialfinalize;
    return result;
}

void *sdvm_rc_retain(void *ref)
{
    sdvm_rc_t *rc = (sdvm_rc_t*)ref;
    ++rc->count;
    return ref;
}

void sdvm_rc_release(void *ref)
{
    sdvm_rc_t *rc = (sdvm_rc_t*)ref;
    if(--rc->count == 0)
    {
        rc->finalize(ref);
        free(rc);
    }
}

void *sdvm_rc_assign(void **pointer, void *newRef)
{
    sdvm_rc_retain(newRef);
    sdvm_rc_release(*pointer);
    *pointer = newRef;
    return newRef;
}
