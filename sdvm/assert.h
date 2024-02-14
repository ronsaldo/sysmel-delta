#ifndef SDVM_ASSERT_H
#define SDVM_ASSERT_H

#pragma once

#include "errors.h"

#define SDVM_ASSERT_LINE_TO_STRING__(x) #x
#define SDVM_ASSERT_LINE_TO_STRING_(x) SDVM_ASSERT_LINE_TO_STRING__(x)
#define SDVM_ASSERT_LINE_TO_STRING(x) SDVM_ASSERT_LINE_TO_STRING_(x)
#define SDVM_ASSERT(x) if(!(x)) sdvm_error_assertionFailure(__FILE__ ":" SDVM_ASSERT_LINE_TO_STRING_(__LINE__)": assertion failure: " #x)

#ifdef NDEBUG
#   define SDVM_DASSERT(x) while(false)
#else
#   define SDVM_DASSERT(x) if(!(x)) sdvm_error_fatalAssertionFailure(__FILE__ ":" SDVM_ASSERT_LINE_TO_STRING_(__LINE__)": assertion failure: " #x)
#endif

#endif //SDVM_ASSERT_H