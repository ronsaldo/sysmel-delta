#ifndef SDVM_ERRORS_H
#define SDVM_ERRORS_H

#pragma once

#include "common.h"
#include <stddef.h>
#include <stdint.h>

SDVM_API void sdvm_error(const char *message);
SDVM_API void sdvm_error_assertionFailure(const char *message);
SDVM_API void sdvm_error_fatalAssertionFailure(const char *message);

#endif //SDVM_ERRORS_H