#include "image.h"
#include "instruction.h"
#include "scanner.h"
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

void printHelp(void)
{
    printf(
"sdvm-as <options> [input]*\n"
"-h\t\tPrint this message.\n"
"-o\t\tOutput file name.\n"
"-v\t\tPrint the version information.\n"
    );
}

void printVersion(void)
{
    printf("sdvm-as version 0.1\n");
}

void processInputFile(FILE *inputFile, const char *fileName)
{
    sdvm_sourceCollection_t *sourceCollection = sdvm_sourceCollection_readFromFile(inputFile, fileName);
    sdvm_scannerState_t scannerState = sdvm_scanner_initialize(sourceCollection);
    sdvm_tokenList_t tokenList = {0};
    sdvm_scanner_scanUntilEndInto(&scannerState, &tokenList);
    for(size_t i = 0; i < tokenList.size; ++i)
    {
        sdvm_token_t token = tokenList.elements[i];
        printf("%s:%d.%d-%d.%d: %s %s\n",
            token.sourcePosition.sourceCollection->fileName,
            token.sourcePosition.startLine, token.sourcePosition.startColumn,
            token.sourcePosition.endLine, token.sourcePosition.endColumn,
            sdvm_scanner_getTokenKindName(token.kind),
            token.message ? token.message : ""
        );
    }

    sdvm_tokenList_destroy(&tokenList);
    sdvm_rc_release(sourceCollection);
}

int main(int argc, const char *argv[])
{
    const char *outputFileName = NULL;

    for(int i = 1; i < argc; ++i)
    {
        if(argv[i][0] == '-' && argv[i][1])
        {
            if(!strcmp(argv[i], "-h"))
            {
                printHelp();
                return 0;
            }
            else if(!strcmp(argv[i], "-v"))
            {
                printVersion();
                return 0;
            }
            else if(!strcmp(argv[i], "-o"))
            {
                outputFileName = argv[++i];
            }
            else
            {
                printHelp();
                return 1;
            }
        }
        else
        {
            bool isStdin = !strcmp(argv[i], "-");
            const char *inputFileName = isStdin ? argv[0] : argv[i];
            FILE *inputFile = isStdin ? stdin : fopen(inputFileName, "r");
            if(!inputFile)
            {
                perror("Failed to open input file");
                return 1;
            }

            processInputFile(inputFile, inputFileName);

            if(!isStdin)
                fclose(inputFile);
        }
    }

    return 0;
}
