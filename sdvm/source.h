#ifndef SDVM_SOURCE_H
#define SDVM_SOURCE_H

#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include "rc.h"

typedef struct sdvm_sourceCollection_s
{
    sdvm_rc_t super;
    char *sourceText;
    size_t sourceTextSize;
    char *fileName;
} sdvm_sourceCollection_t;

typedef struct sdvm_sourcePosition_s
{
    sdvm_sourceCollection_t *sourceCollection;
    uint32_t startIndex;
    uint32_t endIndex;

    uint32_t startLine;
    uint32_t startColumn;
    uint32_t endLine;
    uint32_t endColumn;
} sdvm_sourcePosition_t;

sdvm_sourceCollection_t *sdvm_sourceCollection_readFromFile(FILE *file, const char *fileName);

#endif //SDVM_SOURCE_H