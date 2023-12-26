#ifndef SDVM_RC_H
#define SDVM_RC_H

#include <stdint.h>
#include <stddef.h>

typedef void (*sdvm_finalize_t)(void *object);
typedef struct sdvm_rc_s
{
    uint32_t count;
    sdvm_finalize_t finalize;
} sdvm_rc_t;

#define SDVM_RC_ALLOCATE(type, destructor) (type*)sdvm_rc_allocate(sizeof(type), (sdvm_finalize_t)(destructor))
#define SDVM_RC_ALLOCATE_WITH_VARIABLE_SIZE(type, variableSize, destructor) (type*)sdvm_rc_allocate(sizeof(type) + variableSize, (sdvm_finalize_t)(destructor))

void *sdvm_rc_allocate(size_t size, sdvm_finalize_t finalize);
void *sdvm_rc_retain(void *ref);
void sdvm_rc_release(void *ref);
void *sdvm_rc_assign(void **pointer, void *newRef);

#endif //SDVM_RC_H
