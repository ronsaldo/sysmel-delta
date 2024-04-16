#include "utils.h"
#include <string.h>

SDVM_API bool sdvm_targetDescription_parseTriple(sdvm_targetDescription_t *outParsedDescription, const char *triple)
{
    memset(outParsedDescription, 0, sizeof(sdvm_targetDescription_t));
    if(!triple)
        return false;

    char tripleComponents[SDVM_TARGET_TRIPLE_COMPONENTS][SDVM_TARGET_TRIPLE_COMPONENT_SIZE];
    memset(tripleComponents, 0, sizeof(tripleComponents));
    size_t tripleComponentCount = 0;

    size_t componentStartPosition = 0;
    size_t position = 0;
    for(; triple[position]; ++position)
    {
        char c = triple[position];
        if(c == '-')
        {
            size_t componentSize = position - componentStartPosition;
            if(componentSize + 1 >= SDVM_TARGET_TRIPLE_COMPONENT_SIZE)
                return false;

            if(tripleComponentCount >= SDVM_TARGET_TRIPLE_COMPONENTS)
                return false;

            memcpy(tripleComponents[tripleComponentCount], triple + componentStartPosition, componentSize);
            ++tripleComponentCount;
            componentStartPosition = ++position;
        }
    }

    size_t lastComponentSize = position - componentStartPosition;
    if(lastComponentSize + 1 >= SDVM_TARGET_TRIPLE_COMPONENT_SIZE)
        return false;

    if(tripleComponentCount >= SDVM_TARGET_TRIPLE_COMPONENTS)
        return false;

    memcpy(tripleComponents[tripleComponentCount], triple + componentStartPosition, lastComponentSize);
    ++tripleComponentCount;

    switch(tripleComponentCount)
    {
    case 1:
        memcpy(outParsedDescription->architectureName, tripleComponents[0], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        break;
    case 2:
        memcpy(outParsedDescription->architectureName, tripleComponents[0], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->osName, tripleComponents[1], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        break;
    case 3:
        memcpy(outParsedDescription->architectureName, tripleComponents[0], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->osName, tripleComponents[1], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->abiName, tripleComponents[2], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        break;
    case 4:
        memcpy(outParsedDescription->architectureName, tripleComponents[0], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->vendorName, tripleComponents[1], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->osName, tripleComponents[2], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        memcpy(outParsedDescription->abiName, tripleComponents[3], SDVM_TARGET_TRIPLE_COMPONENT_SIZE);
        break;
    default: abort();
    }

    return sdvm_targetDescription_parseNames(outParsedDescription);
}

SDVM_API bool sdvm_targetDescription_parseNames(sdvm_targetDescription_t *description)
{
    // Architecture and subarchitecture
    if(!strcmp(description->architectureName, "aarch64") || !strncmp(description->architectureName, "arm64", 5))
    {
        description->architecture = SDVM_TARGET_ARCH_AARCH64;
    }
    else if(!strncmp(description->architectureName, "arm", 3))
    {
        description->architecture = SDVM_TARGET_ARCH_ARM;
    }
    else if(!strcmp(description->architectureName, "i686"))
    {
        description->architecture = SDVM_TARGET_ARCH_I686;
    }
    else if(!strcmp(description->architectureName, "x86_64"))
    {
        description->architecture = SDVM_TARGET_ARCH_X86_64;
    }
    else if(!strcmp(description->architectureName, "riscv32"))
    {
        description->architecture = SDVM_TARGET_ARCH_RISC_V_32;
    }
    else if(!strcmp(description->architectureName, "riscv64"))
    {
        description->architecture = SDVM_TARGET_ARCH_RISC_V_64;
    }

    // Operating system name
    if(!strcmp(description->osName, "none"))
    {
        description->os = SDVM_TARGET_OS_NONE;
    }
    else if(!strcmp(description->osName, "windows"))
    {
        description->os = SDVM_TARGET_OS_WINDOWS;
    }
    else if(!strcmp(description->osName, "macos"))
    {
        description->os = SDVM_TARGET_OS_MACOS;
    }
    else if(!strcmp(description->osName, "linux"))
    {
        description->os = SDVM_TARGET_OS_LINUX;
    }

    // ABI
    if(!strcmp(description->abiName, "gnu"))
    {
        description->abi = SDVM_TARGET_ABI_GNU;
    }
    else if(!strcmp(description->abiName, "msvc"))
    {
        description->abi = SDVM_TARGET_ABI_MSVC;
    }
    else if(!strcmp(description->abiName, "eabi"))
    {
        description->abi = SDVM_TARGET_ABI_EABI;
    }

    return true;
}