#include "source.h"
#include <stdlib.h>
#include <string.h>

void sdvm_sourceCollection_destroy(sdvm_sourceCollection_t *sourceCollection)
{
    free(sourceCollection->fileName);
    free(sourceCollection->sourceText);
    free(sourceCollection);
}

sdvm_sourceCollection_t *sdvm_sourceCollection_readFromFile(FILE *file, const char *fileName)
{
    size_t chunkReadSize = 4096;
    size_t capacity = chunkReadSize*4;
    size_t size = 0;
    char *readBuffer = malloc(capacity);

    // Read chunks until hitting EOF.
    while(!feof(file))
    {
        if(size + chunkReadSize >= capacity)
        {
            size_t newCapacity = capacity * 2;
            readBuffer = realloc(readBuffer, newCapacity);
            capacity = newCapacity;
        }
        
        size += fread(readBuffer + size, 1, chunkReadSize, file);
    }

    // Allocate the resulting collection.
    sdvm_sourceCollection_t *sourceCollection = calloc(1, sizeof(sdvm_sourceCollection_t));

    // Reduce the text size and add the null terminator.
    sourceCollection->sourceText = realloc(readBuffer, size + 1);
    sourceCollection->sourceText[size] = 0;
    sourceCollection->sourceTextSize = size;

    // Copy the file name.
    size_t fileNameSize = strlen(fileName);
    sourceCollection->fileName = malloc(fileNameSize + 1);
    memcpy(sourceCollection->fileName, fileName, fileNameSize + 1);

    return sourceCollection;
}
