#include "module.h"
#include "instruction.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>

static bool sdvm_module_validateModuleHeaderData(size_t dataSize, uint8_t *data)
{
    if(dataSize < sizeof(sdvm_moduleHeader_t))
        return false;

    sdvm_moduleHeader_t *header = (sdvm_moduleHeader_t*)data;
    if (memcmp(header->magic, "SDVM", 4))
        return false;

    
    if (header->headerSize < sizeof(sdvm_moduleHeader_t) || (header->pointerSize != 4 && header->pointerSize != 8))
        return false;

    return true;
}

static bool sdvm_module_fetchAndValidateDataStructures(sdvm_module_t *module)
{
    module->header = (sdvm_moduleHeader_t*)module->moduleData;
    module->sectionHeaderCount = module->header->sectionHeaderCount;
    module->sectionHeaders = (sdvm_moduleSectionHeader_t*)(module->header + 1);

    // Bounds check the headers.
    if(sizeof(sdvm_moduleHeader_t) + sizeof(sdvm_moduleSectionHeader_t)*module->sectionHeaderCount > module->moduleDataSize)
        return false;

    // Check the section headers.
    for(size_t i = 0; i < module->sectionHeaderCount; ++i)
    {
        sdvm_moduleSectionHeader_t *header = module->sectionHeaders + i;

        // Ignore sections with size of zero.
        if(header->size == 0)
            continue;

        // Check the bounds.
        if(header->offset + header->size > module->moduleDataSize)
            return false;

        switch(header->type)
        {
        case SdvmModuleSectionTypeConstant:
            module->constSectionSize = header->size;
            module->constSectionData = module->moduleData + header->offset;
            break;
        case SdvmModuleSectionTypeData:
            module->dataSectionSize = header->size;
            module->dataSectionData = module->moduleData + header->offset;
            break;
        case SdvmModuleSectionTypeText:
            module->textSectionSize = header->size;
            module->textSectionData = module->moduleData + header->offset;
            break;
        case SdvmModuleSectionTypeString:
            module->stringSectionSize = header->size;
            module->stringSectionData = module->moduleData + header->offset;
            break;
        case SdvmModuleSectionTypeImportModuleTable:
            module->importTableSize = header->size / sizeof(sdvm_moduleImportTableEntry_t);
            module->importTable = (sdvm_moduleImportTableEntry_t*)(module->moduleData + header->offset);
            break;
        case SdvmModuleSectionTypeImportModuleValueTable:
            module->importValueTableSize = header->size / sizeof(sdvm_moduleImportValueTableEntry_t);
            module->importValueTable = (sdvm_moduleImportValueTableEntry_t*)(module->moduleData + header->offset);
            break;
        case SdvmModuleSectionTypeFunctionTable:
            module->functionTableSize = header->size / sizeof(sdvm_moduleFunctionTableEntry_t);
            module->functionTable = (sdvm_moduleFunctionTableEntry_t*)(module->moduleData + header->offset);
            break;
        case SdvmModuleSectionTypeExportValueTable:
            module->exportValueTableSize = header->size / sizeof(sdvm_moduleExportValueTableEntry_t);
            module->exportValueTable = (sdvm_moduleExportValueTableEntry_t*)(module->moduleData + header->offset);
            break;
        case SdvmModuleSectionTypeMemoryDescriptorTable:
            module->memoryDescriptorTableSize = header->size / sizeof(sdvm_moduleMemoryDescriptorTableEntry_t);
            module->memoryDescriptorTable = (sdvm_moduleMemoryDescriptorTableEntry_t*)(module->moduleData + header->offset);
            break;
        default:
            // Ignored by default
        }
    }

    // Validate the function table.
    for(size_t i = 0; i < module->functionTableSize; ++i)
    {
        sdvm_moduleFunctionTableEntry_t *function = module->functionTable + i;
        if(function->textSectionSize != 0 && function->textSectionOffset + function->textSectionSize > module->textSectionSize)
            return false;

        if(function->textSectionSize == 0)
            continue; 
    }

    return true;
}

sdvm_module_t *sdvm_module_loadFromMemory(size_t dataSize, uint8_t *data)
{
    if(!sdvm_module_validateModuleHeaderData(dataSize, data))
        return NULL;

    sdvm_module_t *module = (sdvm_module_t*)calloc(sizeof(sdvm_module_t), 1);
    module->moduleData = malloc(dataSize);
    module->moduleDataSize = dataSize;
    memcpy(module->moduleData, data, module->moduleDataSize);

    if(!sdvm_module_fetchAndValidateDataStructures(module))
    {
        sdvm_module_destroy(module);
        return NULL;
    }

    return module;
}

sdvm_module_t *sdvm_module_loadFromFileNamed(const char *fileName)
{
    FILE *moduleFile = fopen(fileName, "rb");
    if(!moduleFile) return NULL;

    fseek(moduleFile, 0, SEEK_END);
    size_t moduleFileSize = ftell(moduleFile);
    fseek(moduleFile, 0, SEEK_SET);

    uint8_t *moduleData = malloc(moduleFileSize);
    bool readSucceeded = fread(moduleData, moduleFileSize, 1, moduleFile) == 1;
    fclose(moduleFile);

    if(!readSucceeded || !sdvm_module_validateModuleHeaderData(moduleFileSize, moduleData))
    {
        free(moduleData);
        return NULL;
    }

    sdvm_module_t *module = (sdvm_module_t*)calloc(sizeof(sdvm_module_t), 1);
    module->moduleData = moduleData;
    module->moduleDataSize = moduleFileSize;

    if(!sdvm_module_fetchAndValidateDataStructures(module))
    {
        sdvm_module_destroy(module);
        return NULL;
    }

    return module;
}

void sdvm_module_destroy(sdvm_module_t *module)
{
    if(!module) return;
    free(module->moduleData);
    free(module);
}

void sdvm_module_dumpFunction(sdvm_module_t *module, size_t index)
{
    if(index == 0) return;
    if(index > module->functionTableSize) return;

    sdvm_moduleFunctionTableEntry_t *function = module->functionTable + index - 1;
    sdvm_constOrInstruction_t *instructions = (sdvm_constOrInstruction_t *)(module->textSectionData + function->textSectionOffset);
    uint32_t instructionCount = function->textSectionSize / sizeof(sdvm_constOrInstruction_t);

    printf("%d:\n", (int)index);
    for(uint32_t i = 0; i < instructionCount; ++i)
    {
        sdvm_decodedConstOrInstruction_t decodedInstruction = sdvm_instruction_decode(instructions[i]);
        
        // Is this a constant?
        if(decodedInstruction.isConstant)
        {
            printf("    $%d : %s := %s(%lld)\n", i, sdvm_instruction_typeToString(decodedInstruction.destType), sdvm_instruction_fullOpcodeToString(decodedInstruction.opcode), (long long)decodedInstruction.constant.signedPayload);
        }
        else
        {
            printf("    $%d : %s := %s(%d : %s, %d : %s)\n",
                i, sdvm_instruction_typeToString(decodedInstruction.destType),
                sdvm_instruction_fullOpcodeToString(decodedInstruction.opcode),
                decodedInstruction.instruction.arg0, sdvm_instruction_typeToString(decodedInstruction.instruction.arg0Type),
                decodedInstruction.instruction.arg1, sdvm_instruction_typeToString(decodedInstruction.instruction.arg1Type));
        }
    }
}

void sdvm_module_dump(sdvm_module_t *module)
{
    for(size_t i = 1; i <= module->functionTableSize; ++i)
        sdvm_module_dumpFunction(module, i);
}