#ifndef SDVM_SCANNER_H
#define SDVM_SCANNER_H

#include <stdint.h>
#include "source.h"

typedef enum sdvm_tokenKind_e
{
#define SDVM_TOKEN_KIND_DEF(name) SdvmTokenKind ## name,
#include "token.inc"
#undef SDVM_TOKEN_KIND_DEF
} sdvm_tokenKind_t;

typedef struct sdvm_token_s
{
    sdvm_tokenKind_t kind;
    sdvm_sourcePosition_t sourcePosition;
    const char *message;
} sdvm_token_t;

typedef struct sdvm_scannerState_s
{
    sdvm_sourceCollection_t *sourceCollection;
    uint32_t position;
    uint32_t column;
    uint32_t line;
    bool isPreviousCR;
} sdvm_scannerState_t;

const char *sdvm_scanner_getTokenKindName(sdvm_tokenKind_t kind);
sdvm_scannerState_t sdvm_scanner_initialize(sdvm_sourceCollection_t *sourceCollection);
sdvm_token_t sdvm_scanner_nextToken(sdvm_scannerState_t *scannerState);

#endif //SDVM_SCANNER_H
