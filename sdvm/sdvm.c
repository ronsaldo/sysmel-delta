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
    const char *moduleFileName = NULL;

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

    sdvm_module_dump(module);

    sdvm_compiler_t *compiler = sdvm_compiler_create();
    bool compilationSucceeded = sdvm_compiler_compileModule(compiler, module);
    sdvm_module_destroy(module);

    if (!compilationSucceeded)
    {
        sdvm_compiler_destroy(compiler);
        fprintf(stderr, "Failed to compile module from file %s\n", moduleFileName);
        return 1;
    }

    sdvm_compiler_destroy(compiler);

    return 0;
} 
