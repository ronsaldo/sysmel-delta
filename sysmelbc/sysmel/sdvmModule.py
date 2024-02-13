import struct

def sdvmModuleFourCC(cc):
    assert len(cc) == 4
    return ord(cc[0]) | (ord(cc[1]) << 8) | (ord(cc[2]) << 16) | (ord(cc[3]) << 24)

SdvmModuleMagic = sdvmModuleFourCC('SDVM')
SdvmModuleVersion = 1

SdvmModuleHeaderSize = 16
SdvmModuleSectionHeaderSize = 12

SdvmModuleSectionTypeNull = 0
SdvmModuleSectionTypeConstant = sdvmModuleFourCC('cont')
SdvmModuleSectionTypeText = sdvmModuleFourCC('text')
SdvmModuleSectionTypeFunctionTable = sdvmModuleFourCC('funt')

SdvmModuleSectionTypeExportTable = sdvmModuleFourCC('expt')
SdvmModuleSectionTypeImportTable = sdvmModuleFourCC('impt')

SdvmModuleSectionTypeDebugLineStart = sdvmModuleFourCC('dlns')
SdvmModuleSectionTypeDebugLineEnd = sdvmModuleFourCC('dlne')

class SDVMModule:
    def __init__(self, pointerSize = 8) -> None:
        self.pointerSize = pointerSize
        self.constantSection = SDVMConstantSection()
        self.textSection = SDVMTextSection()
        self.exportTableSection = SDVMExportTableSection()
        self.importTableSection = SDVMImportTableSection()
        self.sections: list[SDVMModuleSection] = [SDVMNullSection(), self.constantSection, self.textSection, self.exportTableSection, self.importTableSection]

    def encode(self) -> bytearray:
        startOffset = SdvmModuleHeaderSize + SdvmModuleSectionHeaderSize * len(self.sections)
        for section in self.sections:
            startOffset += section.finish(startOffset)

        result = bytearray()
        result += struct.pack('<IIII', SdvmModuleMagic, SdvmModuleVersion, self.pointerSize, len(self.sections))
        for section in self.sections:
            result += struct.pack('<III', section.sectionType, section.fileOffset, len(section.contents))
        for section in self.sections:
            result += section.contents        
        return result
    
    def saveToFileNamed(self, fileName):
        encodedModule = self.encode()
        with open(fileName, "wb") as f:
            f.write(encodedModule)

class SDVMModuleSection:
    def __init__(self, sectionType) -> None:
        self.sectionType = sectionType
        self.contents = bytearray()
        self.fileOffset = 0

    def finish(self, fileOffset) -> int:
        self.fileOffset = fileOffset
        return len(self.contents)

class SDVMNullSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeNull)

class SDVMConstantSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeConstant)

class SDVMTextSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeText)

class SDVMFunctionTableSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeFunctionTable)

class SDVMExportTableSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeExportTable)

class SDVMImportTableSection(SDVMModuleSection):
    def __init__(self) -> None:
        super().__init__(SdvmModuleSectionTypeImportTable)

class SDVMFunctionBuilder:
    def __init__(self) -> None:
        pass
