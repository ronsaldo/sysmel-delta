#ifndef SDVM_MODULE_H
#define SDVM_MODULE_H

#include <stdint.h>
#include <stddef.h>

#define SDVM_IM_FOUR_CC(c1, c2, c3, c4) ((c1) | ((c2) << 8) | ((c3) << 16) | ((c4) << 24))

typedef enum sdvm_moduleSectionType_e
{
    SdvmModuleSectionTypeNull = 0,
    SdvmModuleSectionTypeConstant = SDVM_IM_FOUR_CC('c', 'o', 'n', 't'),
    SdvmModuleSectionTypeData = SDVM_IM_FOUR_CC('d', 'a', 't', 'a'),
    SdvmModuleSectionTypeText = SDVM_IM_FOUR_CC('t', 'e', 'x', 't'),
    SdvmModuleSectionTypeString = SDVM_IM_FOUR_CC('s', 't', 'r', 'n'),
    SdvmModuleSectionTypeFunctionTable = SDVM_IM_FOUR_CC('f', 'u', 'n', 't'),
    SdvmModuleSectionTypeObjectTable = SDVM_IM_FOUR_CC('o', 'b', 'j', 't'),
    SdvmModuleSectionTypeMemoryDescriptorTable = SDVM_IM_FOUR_CC('m', 'e', 'm', 'd'),
    SdvmModuleSectionTypeImportModuleTable = SDVM_IM_FOUR_CC('i', 'm', 'p', 'm'),
    SdvmModuleSectionTypeImportModuleValueTable = SDVM_IM_FOUR_CC('i', 'm', 'p', 'v'),
    SdvmModuleSectionTypeExportValueTable = SDVM_IM_FOUR_CC('e', 'x', 'p', 'v'),

    SdvmModuleSectionTypeDebugSourceDirectory = SDVM_IM_FOUR_CC('d', 's', 'r', 'd'),
    SdvmModuleSectionTypeDebugSourceCode = SDVM_IM_FOUR_CC('d', 's', 'r', 'c'),
    SdvmModuleSectionTypeDebugLineData = SDVM_IM_FOUR_CC('d', 'l', 'n', 'd'),
    SdvmModuleSectionTypeDebugFunctionTable = SDVM_IM_FOUR_CC('d', 'f', 'n', 't'),
} sdvm_moduleSectionType_t;

typedef enum sdvm_moduleValueKind_e
{
    SdvmModuleValueKindNull = 0,
    SdvmModuleValueKindFunctionHandle = SDVM_IM_FOUR_CC('f', 'u', 'n', 'h'),
    SdvmModuleValueKindDataSectionValue = SDVM_IM_FOUR_CC('d', 'a', 't', 'a'),
    SdvmModuleValueKindConstantSectionValue = SDVM_IM_FOUR_CC('c', 'o', 'n', 't'),
    SdvmModuleValueKindObjectHandle = SDVM_IM_FOUR_CC('o', 'b', 'j', 'h'),
} sdvm_moduleValueKind_t;

typedef enum sdvm_moduleExternalType_e
{
    SdvmModuleExternalTypeNone = 0,
    SdvmModuleExternalTypeC = SDVM_IM_FOUR_CC('C', ' ', ' ', ' '),
} sdvm_moduleExternalType_t;

typedef struct sdvm_moduleString_s
{
    uint32_t stringSectionOffset;
    uint32_t stringSectionSize;
} sdvm_moduleString_t;

typedef struct sdvm_moduleHeader_s
{
    char magic[4]; // SDVM
    uint32_t headerSize;
    uint32_t version;
    uint32_t pointerSize;
    uint32_t sectionHeaderCount;
    uint32_t entryPoint;
    uint32_t entryPointClosure;
    sdvm_moduleString_t name;
} sdvm_moduleHeader_t;

typedef struct sdvm_moduleSectionHeader_s
{
    uint32_t type;
    uint32_t offset;
    uint32_t size;
} sdvm_moduleSectionHeader_t;

typedef struct sdvm_moduleFunctionTableEntry_s
{
    uint32_t textSectionOffset;
    uint32_t textSectionSize;
    sdvm_moduleString_t name; // Optional
    sdvm_moduleString_t typeDescriptor; // Optional
} sdvm_moduleFunctionTableEntry_t;

typedef struct sdvm_moduleObjectTableEntry_s
{
    uint32_t dataSectionOffset;
    uint32_t dataSectionSize;
} sdvm_moduleObjectTableEntry_t;

typedef struct sdvm_moduleImportTableEntry_s
{
    sdvm_moduleString_t name;
} sdvm_moduleImportTableEntry_t;

typedef struct sdvm_moduleImportValueTableEntry_s
{
    uint32_t module; // One based.
    uint32_t externalType;
    sdvm_moduleString_t name;
    sdvm_moduleString_t typeDescriptor;
} sdvm_moduleImportValueTableEntry_t;

typedef struct sdvm_moduleExportValueTableEntry_s
{
    uint32_t kind;
    uint32_t externalType;
    uint64_t firstValue;
    uint64_t secondValue;
    sdvm_moduleString_t name;
    sdvm_moduleString_t typeDescriptor;
} sdvm_moduleExportValueTableEntry_t;

typedef struct sdvm_moduleMemoryDescriptorTableEntry_s
{
    uint64_t alignment;
    uint64_t size;
    uint32_t gcDescriptorOffset;
    uint32_t gcDescriptorSize;
} sdvm_moduleMemoryDescriptorTableEntry_t;

typedef struct sdvm_debugSourceDirectoryTableEntry_s
{
    uint32_t directoryIndex;
    sdvm_moduleString_t name;
} sdvm_debugSourceDirectoryTableEntry_t;

typedef struct sdvm_debugSourceCodeTableEntry_s
{
    uint32_t kind;
    sdvm_moduleString_t language;
    sdvm_moduleString_t name;
    sdvm_moduleString_t sourceCode;
} sdvm_debugSourceCodeTableEntry_t;

typedef struct sdvm_debugFunctionTableEntry_s
{
    uint32_t sourceCode;
    uint32_t startIndex;
    uint32_t endIndex;
    uint32_t startLine;
    uint32_t endLine;
    uint32_t startColumn;
    uint32_t endColumn;
} sdvm_debugFunctionTableEntry_t;

typedef struct sdvm_module_s
{
    sdvm_moduleHeader_t *header;

    size_t sectionHeaderCount;
    sdvm_moduleSectionHeader_t *sectionHeaders;

    size_t constSectionSize;
    uint8_t *constSectionData;

    size_t dataSectionSize;
    uint8_t *dataSectionData;

    size_t stringSectionSize;
    uint8_t *stringSectionData;

    size_t textSectionSize;
    uint8_t *textSectionData;

    size_t importTableSize;
    sdvm_moduleImportTableEntry_t *importTable;

    size_t importValueTableSize;
    sdvm_moduleImportValueTableEntry_t *importValueTable;

    size_t functionTableSize;
    sdvm_moduleFunctionTableEntry_t *functionTable;

    size_t objectTableSize;
    sdvm_moduleObjectTableEntry_t *objectTable;

    size_t exportValueTableSize;
    sdvm_moduleExportValueTableEntry_t *exportValueTable;

    size_t memoryDescriptorTableSize;
    sdvm_moduleMemoryDescriptorTableEntry_t *memoryDescriptorTable;

    size_t moduleDataSize;
    uint8_t *moduleData;

    size_t debugSourceDirectoryTableSize;
    sdvm_debugSourceDirectoryTableEntry_t *debugSourceDirectoryTable;

    size_t debugSourceCodeTableSize;
    sdvm_debugSourceCodeTableEntry_t *debugSourceCodeTable;

    size_t debugFunctionTableSize;
    sdvm_debugFunctionTableEntry_t *debugFunctionTable;
} sdvm_module_t;

sdvm_module_t *sdvm_module_loadFromMemory(size_t dataSize, uint8_t *data);
sdvm_module_t *sdvm_module_loadFromFileNamed(const char *fileName);
void sdvm_module_destroy(sdvm_module_t *module);
void sdvm_module_dumpFunction(sdvm_module_t *module, size_t index);
void sdvm_module_dump(sdvm_module_t *module);

#endif //SDVM_MODULE_H
