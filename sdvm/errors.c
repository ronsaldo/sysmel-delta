#include "errors.h"
#include <stdio.h>
#include <stdlib.h>

SDVM_API void sdvm_error(const char *message)
{
    fprintf(stderr, "%s\n", message);
    abort();
}

SDVM_API void sdvm_error_assertionFailure(const char *message)
{
    sdvm_error(message);
}

SDVM_API void sdvm_error_fatalAssertionFailure(const char *message)
{
    fprintf(stderr, "%s\n", message);
    abort();
}
