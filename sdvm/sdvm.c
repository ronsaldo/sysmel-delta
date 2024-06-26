#include "module.h"
#include "compiler.h"
#include "instruction.h"
#include <stdio.h>
#include <string.h>

void printHelp(void)
{
    printf("sdvm <module>\n");
}

void printVersion(void)
{
    printf("sdvm version 0.1\n");
}

int main(int argc, const char *argv[])
{
    bool verbose = false;
    const char *moduleFileName = NULL;
    const char *outputFileName = NULL;
    const char *targetName = sdvm_compilerTarget_getDefaultTargetName();

    for(int i = 1; i < argc; ++i)
    {
        if(*argv[i] == '-')
        {
            if(!strcmp(argv[i], "-h") || !strcmp(argv[i], "-help"))
            {
                printHelp();
                return 0;
            }
            else if(!strcmp(argv[i], "-version"))
            {
                printVersion();
                return 0;
            }
            else if(!strcmp(argv[i], "-v"))
            {
                verbose = true;
            }
            else if(!strcmp(argv[i], "-target"))
            {
                targetName = argv[++i];
            }
            else if(!strcmp(argv[i], "-o"))
            {
                outputFileName = argv[++i];
            }
        }
        else
        {
            moduleFileName = argv[i];
        }
    }

    if(!moduleFileName)
    {
        printHelp();
        return 0;
    }

    sdvm_module_t *module = sdvm_module_loadFromFileNamed(moduleFileName);
    if(!module)
    {
        fprintf(stderr, "Failed to load module from file %s\n", moduleFileName);
        return 1;
    }

    //sdvm_module_dump(module);

    sdvm_compiler_t *compiler = sdvm_compiler_create(sdvm_compilerTarget_getNamed(targetName));
    compiler->verbose = verbose;
    bool compilationSucceeded = sdvm_compiler_compileModule(compiler, module);
    sdvm_module_destroy(module);

    if (!compilationSucceeded)
    {
        sdvm_compiler_destroy(compiler);
        fprintf(stderr, "Failed to compile module from file %s\n", moduleFileName);
        return 1;
    }

    // Save the object file
    if(outputFileName)
    {
        if(!sdvm_compiler_encodeObjectAndSaveToFileNamed(compiler, outputFileName))
        {
            sdvm_compiler_destroy(compiler);
            fprintf(stderr, "Failed to encode the object file %s\n", outputFileName);
            return 1;

        }

        sdvm_compiler_destroy(compiler);
    }
    else
    {
        printf("TODO: encode and write the object memory, and run it\n");
        sdvm_compiler_destroy(compiler);
    }

    return 0;
} 
