#include "dwarf.h"
#include "compiler.h"
#include "assert.h"
#include <stdbool.h>
#include <string.h>


SDVM_API size_t sdvm_dwarf_encodeDwarfPointer(sdvm_dynarray_t *buffer, uint32_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeDwarfPointerSectionRelative(sdvm_compilerObjectSection_t *section, sdvm_compilerObjectSection_t *targetSection, uint32_t value)
{
    size_t offset = section->contents.size;
    uint32_t zero = 0;
    sdvm_dynarray_addAll(&section->contents, 4, &zero);

    sdvm_compilerRelocation_t relocation = {
        .kind = SdvmCompRelocationSectionRelative32,
        .symbol = targetSection->symbolIndex,
        .addend = value,
        .offset = offset
    };

    sdvm_dynarray_add(&section->relocations, &relocation);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeDwarfPointerPCRelative(sdvm_dynarray_t *buffer, uint32_t value)
{
    int32_t pcRelativeValue = (int32_t)(buffer->size - value);
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(pcRelativeValue), &pcRelativeValue);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeByte(sdvm_dynarray_t *buffer, uint8_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeWord(sdvm_dynarray_t *buffer, uint16_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeDWord(sdvm_dynarray_t *buffer, uint32_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeQWord(sdvm_dynarray_t *buffer, uint64_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeString(sdvm_dynarray_t *buffer, const char *string, size_t stringSize)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, stringSize, string);
    sdvm_dwarf_encodeByte(buffer, 0);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeCString(sdvm_dynarray_t *buffer, const char *cstring)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, strlen(cstring) + 1, cstring);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeULEB128(sdvm_dynarray_t *buffer, uint64_t value)
{
    size_t offset = buffer->size;
    uint64_t currentValue = value;
    do
    {
        uint8_t byte = currentValue & 127;
        currentValue >>= 7;

        if(currentValue)
            byte |= 128;
        sdvm_dynarray_add(buffer, &byte);
    } while (currentValue != 0);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeSLEB128(sdvm_dynarray_t *buffer, int64_t value)
{
    size_t offset = buffer->size;
    bool more = true;

    int64_t currentValue = value;
    while(more)
    {
        uint8_t byte = currentValue & 127;
        currentValue >>= 7;
        
        bool byteHasSign = byte & 0x40;
        if ((currentValue == 0 && !byteHasSign) || (currentValue == -1 && byteHasSign))
            more = false;
        else
            byte = byte | 0x80;

        sdvm_dynarray_add(buffer, &byte);
    }
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeAlignment(sdvm_dynarray_t *buffer, size_t alignment)
{
    size_t offset = buffer->size;
    size_t alignedSize = (buffer->size + alignment - 1) & (-alignment);
    size_t padding = alignedSize - buffer->size;
    for(size_t i = 0; i < padding; ++i)
        sdvm_dwarf_encodeByte(buffer, 0);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeRelocatablePointer32(sdvm_compilerObjectSection_t *section, sdvm_compilerObjectSection_t *targetSection, uint32_t value)
{
    size_t offset = section->contents.size;
    uint32_t zero = 0;
    sdvm_dynarray_addAll(&section->contents, 4, &zero);

    sdvm_compilerRelocation_t relocation = {
        .kind = SdvmCompRelocationAbsolute32,
        .symbol = targetSection->symbolIndex,
        .addend = value,
        .offset = offset
    };
    sdvm_dynarray_add(&section->relocations, &relocation);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeRelocatablePointer64(sdvm_compilerObjectSection_t *section, sdvm_compilerObjectSection_t *targetSection, uint64_t value)
{
    size_t offset = section->contents.size;
    uint64_t zero = 0;
    sdvm_dynarray_addAll(&section->contents, 8, &zero);

    sdvm_compilerRelocation_t relocation = {
        .kind = SdvmCompRelocationAbsolute64,
        .symbol = targetSection->symbolIndex,
        .addend = value,
        .offset = offset
    };
    sdvm_dynarray_add(&section->relocations, &relocation);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeRelocatablePointer(sdvm_compilerObjectSection_t *section, size_t pointerSize, sdvm_compilerObjectSection_t *targetSection, uint64_t value)
{
    SDVM_ASSERT(pointerSize == 4 || pointerSize == 8);
    if(pointerSize == 4)
        return sdvm_dwarf_encodeRelocatablePointer32(section, targetSection, (uint32_t)value);
    else
        return sdvm_dwarf_encodeRelocatablePointer64(section, targetSection, value);
}

SDVM_API size_t sdvm_dwarf_encodeSectionRelative32(sdvm_compilerObjectSection_t *section, sdvm_compilerObjectSection_t *targetSection, uint32_t value)
{
    size_t offset = section->contents.size;
    uint32_t zero = 0;
    sdvm_dynarray_addAll(&section->contents, 4, &zero);

    sdvm_compilerRelocation_t relocation = {
        .kind = SdvmCompRelocationSectionRelative32,
        .symbol = targetSection->symbolIndex,
        .addend = value,
        .offset = offset
    };
    sdvm_dynarray_add(&section->relocations, &relocation);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeRelocatableRelativePointer32(sdvm_compilerObjectSection_t *section, sdvm_compilerObjectSection_t *targetSection, int32_t value)
{
    size_t offset = section->contents.size;
    sdvm_dynarray_addAll(&section->contents, 4, &value);

    if(targetSection)
    {
        sdvm_compilerRelocation_t relocation = {
            .kind = SdvmCompRelocationRelative32,
            .symbol = targetSection->symbolIndex,
            .addend = value,
            .offset = offset
        };
        sdvm_dynarray_add(&section->relocations, &relocation);
    }

    return offset;
}

SDVM_API void sdvm_dwarf_cfi_create(sdvm_dwarf_cfi_builder_t *cfi, sdvm_compilerObjectSection_t *section)
{
    memset(cfi, 0, sizeof(sdvm_dwarf_cfi_builder_t));
    cfi->version = 1;
    cfi->isEhFrame = true;
    cfi->section = section;
}

SDVM_API void sdvm_dwarf_cfi_destroy(sdvm_dwarf_cfi_builder_t *cfi)
{
    (void)cfi;
}

SDVM_API void sdvm_dwarf_cfi_beginCIE(sdvm_dwarf_cfi_builder_t *cfi, sdvm_dwarf_cie_t *cie)
{
    cfi->cieOffset = sdvm_dwarf_encodeDWord(&cfi->section->contents, 0);
    cfi->cieContentOffset = sdvm_dwarf_encodeDwarfPointer(&cfi->section->contents, cfi->isEhFrame ? 0 : -1 ); // CIE_id
    cfi->cie = *cie;
    sdvm_dwarf_encodeByte(&cfi->section->contents, cfi->version);
    sdvm_dwarf_encodeCString(&cfi->section->contents, cfi->isEhFrame ? "zR" : ""); // Argumentation
    if(!cfi->isEhFrame)
    {
        sdvm_dwarf_encodeByte(&cfi->section->contents, cfi->pointerSize); // Address size
        sdvm_dwarf_encodeByte(&cfi->section->contents, 0); // Segment size
    }
    sdvm_dwarf_encodeULEB128(&cfi->section->contents, cie->codeAlignmentFactor);
    sdvm_dwarf_encodeSLEB128(&cfi->section->contents, cie->dataAlignmentFactor);
    if(cfi->version <= 2 && !cfi->isEhFrame)
        sdvm_dwarf_encodeByte(&cfi->section->contents, (uint8_t)cie->returnAddressRegister);
    else
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, cie->returnAddressRegister);
    if(cfi->isEhFrame)
    {
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, 1);
        sdvm_dwarf_encodeByte(&cfi->section->contents, DW_EH_PE_pcrel | DW_EH_PE_sdata4);
    }
}

SDVM_API void sdvm_dwarf_cfi_endCIE(sdvm_dwarf_cfi_builder_t *cfi)
{
    sdvm_dwarf_encodeAlignment(&cfi->section->contents, cfi->pointerSize);
    uint32_t cieSize = (uint32_t)(cfi->section->contents.size - cfi->cieContentOffset);
    memcpy(cfi->section->contents.data + cfi->cieOffset, &cieSize, 4);
}

SDVM_API void sdvm_dwarf_cfi_beginFDE(sdvm_dwarf_cfi_builder_t *cfi, sdvm_compilerObjectSection_t *targetSection, size_t pc)
{
    cfi->fdeOffset = sdvm_dwarf_encodeDWord(&cfi->section->contents, 0);
    cfi->fdeContentOffset = sdvm_dwarf_encodeDwarfPointerPCRelative(&cfi->section->contents, (uint32_t)cfi->cieOffset);
    cfi->fdeInitialPC = pc;
    if(cfi->isEhFrame)
    {
        cfi->fdeInitialLocationOffset = sdvm_dwarf_encodeRelocatableRelativePointer32(cfi->section, targetSection, (int32_t)pc);
        cfi->fdeAddressingRangeOffset = sdvm_dwarf_encodeDWord(&cfi->section->contents, 0);
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, 0);
    }
    else
    {
        cfi->fdeInitialLocationOffset = sdvm_dwarf_encodeRelocatablePointer(cfi->section, cfi->pointerSize, targetSection, pc);
        cfi->fdeAddressingRangeOffset = sdvm_dwarf_encodeRelocatablePointer(cfi->section, cfi->pointerSize, NULL, 0);
    }
    cfi->currentPC = cfi->fdeInitialPC;
    cfi->stackFrameSize = cfi->initialStackFrameSize;
    cfi->framePointerRegister = 0;
    cfi->hasFramePointerRegister = false;
    cfi->isInPrologue = true;
}

SDVM_API void sdvm_dwarf_cfi_endFDE(sdvm_dwarf_cfi_builder_t *cfi, size_t pc)
{
    sdvm_dwarf_encodeAlignment(&cfi->section->contents, cfi->pointerSize);
    if(cfi->isEhFrame)
    {
        uint32_t pcRange = (uint32_t)(pc - cfi->fdeInitialPC);
        memcpy(cfi->section->contents.data + cfi->fdeAddressingRangeOffset, &pcRange, sizeof(uint32_t));
    }
    else
    {
        if(cfi->pointerSize == 4)
        {
            uint32_t pcRange = pc - cfi->fdeInitialPC;
            memcpy(cfi->section->contents.data + cfi->fdeAddressingRangeOffset, &pcRange, sizeof(uint32_t));
        }
        else
        {
            SDVM_ASSERT(cfi->pointerSize == 8);
            uint64_t pcRange = pc - cfi->fdeInitialPC;
            memcpy(cfi->section->contents.data + cfi->fdeAddressingRangeOffset, &pcRange, sizeof(uint64_t));
        }
    }

    uint32_t fdeSize = (uint32_t)(cfi->section->contents.size - cfi->fdeContentOffset);
    memcpy(cfi->section->contents.data + cfi->fdeOffset, &fdeSize, 4);
}

SDVM_API void sdvm_dwarf_cfi_finish(sdvm_dwarf_cfi_builder_t *cfi)
{
    sdvm_dwarf_encodeDWord(&cfi->section->contents, 0);
}

SDVM_API void sdvm_dwarf_cfi_setPC(sdvm_dwarf_cfi_builder_t *cfi, size_t pc)
{
    size_t advance = pc - cfi->currentPC;
    if(advance)
    {
        size_t advanceFactor = advance / cfi->cie.codeAlignmentFactor;
        if(advanceFactor <= 63)
        {
            sdvm_dwarf_encodeByte(&cfi->section->contents, (DW_OP_CFA_advance_loc << 6) | (uint8_t)advanceFactor);
        }
        else
        {
            if(advanceFactor <= 0xFF)
            {
                sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_advance_loc1);
                sdvm_dwarf_encodeByte(&cfi->section->contents, (uint8_t)advanceFactor);
            }
            else if(advanceFactor <= 0xFFFF)
            {
                sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_advance_loc2);
                sdvm_dwarf_encodeWord(&cfi->section->contents, (uint16_t)advanceFactor);
            }
            else
            {
                SDVM_ASSERT(advanceFactor <= 0xFFFFFFFF);
                sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_advance_loc4);
                sdvm_dwarf_encodeDWord(&cfi->section->contents, (uint32_t)advanceFactor);
            }
        }
    }

    cfi->currentPC = pc;
}

SDVM_API void sdvm_dwarf_cfi_cfaInRegisterWithOffset(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg, uint64_t offset)
{
    sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_def_cfa);
    sdvm_dwarf_encodeULEB128(&cfi->section->contents, reg);
    sdvm_dwarf_encodeULEB128(&cfi->section->contents, offset);
}

SDVM_API void sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg, uint64_t offset)
{
    sdvm_dwarf_cfi_cfaInRegisterWithOffset(cfi, reg, cfi->pointerSize * offset);
}

SDVM_API void sdvm_dwarf_cfi_registerValueAtFactoredOffset(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg, uint64_t offset)
{
    if(reg <= 63)
    {
        sdvm_dwarf_encodeByte(&cfi->section->contents, (DW_OP_CFA_offset << 6) | (uint8_t)reg);
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, offset);
    }
    else
    {
        sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_offset_extended);
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, reg);
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, offset);
    }
}

SDVM_API void sdvm_dwarf_cfi_restoreRegister(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg)
{
    if(reg <= 63)
    {
        sdvm_dwarf_encodeByte(&cfi->section->contents, (DW_OP_CFA_restore << 6) | (uint8_t)reg);
    }
    else
    {
        sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_restore_extended);
        sdvm_dwarf_encodeULEB128(&cfi->section->contents, reg);
    }
}

SDVM_API void sdvm_dwarf_cfi_pushRegister(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg)
{
    ++cfi->stackFrameSize;
    if(!cfi->hasFramePointerRegister)
        sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSize);
    sdvm_dwarf_cfi_registerValueAtFactoredOffset(cfi, reg, cfi->stackFrameSize);
}

SDVM_API void sdvm_dwarf_cfi_popRegister(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg)
{
    --cfi->stackFrameSize;
    sdvm_dwarf_cfi_restoreRegister(cfi, reg);
    if(!cfi->hasFramePointerRegister)
        sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSize);
}

SDVM_API void sdvm_dwarf_cfi_saveFramePointerInRegister(sdvm_dwarf_cfi_builder_t *cfi, uint64_t reg, int64_t offset)
{
    SDVM_ASSERT(!cfi->hasFramePointerRegister);
    SDVM_ASSERT((offset % cfi->pointerSize) == 0);

    cfi->hasFramePointerRegister = true;
    cfi->framePointerRegister = reg;
    cfi->stackFrameSizeAtFramePointer = cfi->stackFrameSize - offset / cfi->pointerSize;
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, reg, cfi->stackFrameSizeAtFramePointer);
}

SDVM_API void sdvm_dwarf_cfi_restoreFramePointer(sdvm_dwarf_cfi_builder_t *cfi, int64_t offset)
{
    SDVM_ASSERT(cfi->hasFramePointerRegister);
    SDVM_ASSERT((offset % cfi->pointerSize) == 0);

    cfi->hasFramePointerRegister = false;
    cfi->stackFrameSize = cfi->stackFrameSizeAtFramePointer - offset / cfi->pointerSize;
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSize);
}

SDVM_API void sdvm_dwarf_cfi_stackSizeAdvance(sdvm_dwarf_cfi_builder_t *cfi, size_t pc, size_t increment)
{
    if(!cfi->isInPrologue) return;
    if(!increment) return;
    
    cfi->stackFrameSize += increment / cfi->pointerSize;
    if(!cfi->hasFramePointerRegister)
    {
        sdvm_dwarf_cfi_setPC(cfi, pc);
        sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSizeAtFramePointer);
    }
}

SDVM_API void sdvm_dwarf_cfi_stackSizeRestore(sdvm_dwarf_cfi_builder_t *cfi, size_t pc, size_t increment)
{
    if(!cfi->isInPrologue) return;
    if(!increment) return;
    
    cfi->stackFrameSize -= increment / cfi->pointerSize;
    if(!cfi->hasFramePointerRegister)
    {
        sdvm_dwarf_cfi_setPC(cfi, pc);
        sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSizeAtFramePointer);
    }
}

SDVM_API void sdvm_dwarf_cfi_endPrologue(sdvm_dwarf_cfi_builder_t *cfi)
{
    SDVM_ASSERT(cfi->isInPrologue);
    cfi->isInPrologue = false;
}


SDVM_API void sdvm_dwarf_cfi_beginEpilogue(sdvm_dwarf_cfi_builder_t *cfi)
{
    SDVM_ASSERT(!cfi->isInPrologue);
    SDVM_ASSERT(!cfi->isInEpilogue);
    cfi->isInEpilogue = true;

    sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_remember_state);
    cfi->storedStackFrameSize = cfi->stackFrameSize;
    cfi->storedStackFrameSizeAtFramePointer = cfi->stackFrameSizeAtFramePointer;
    cfi->storedHasFramePointerRegister = cfi->hasFramePointerRegister;
}

SDVM_API void sdvm_dwarf_cfi_endEpilogue(sdvm_dwarf_cfi_builder_t *cfi)
{    SDVM_ASSERT(!cfi->isInPrologue);
    SDVM_ASSERT(cfi->isInEpilogue);
    cfi->isInEpilogue = false;

    sdvm_dwarf_encodeByte(&cfi->section->contents, DW_OP_CFA_restore_state);
    cfi->stackFrameSize = cfi->storedStackFrameSize;
    cfi->stackFrameSizeAtFramePointer = cfi->storedStackFrameSizeAtFramePointer;
    cfi->hasFramePointerRegister = cfi->storedHasFramePointerRegister;
}

SDVM_API void sdvm_dwarf_debugInfo_create(sdvm_dwarf_debugInfo_builder_t *builder, sdvm_compiler_t *compiler)
{
    memset(builder, 0, sizeof(sdvm_dwarf_debugInfo_builder_t));
    builder->version = 4;
    builder->pointerSize = compiler->pointerSize;
    builder->lineProgramHeader.minimumInstructionLength = 1;
    builder->lineProgramHeader.maximumOperationsPerInstruction = 1;
    builder->lineProgramHeader.opcodeBase = 13;
    builder->lineProgramHeader.defaultIsStatement = true;

    builder->lineSection = &compiler->debugLineSection;
    builder->strSection = &compiler->debugStrSection;
    builder->abbrevSection = &compiler->debugAbbrevSection;
    builder->infoSection = &compiler->debugInfoSection;

    sdvm_dynarray_initialize(&builder->locationExpression, 1, 256);

    // Null string.
    sdvm_dwarf_encodeByte(&builder->strSection->contents, 0);

    // Info header
    sdvm_dwarf_encodeDwarfPointer(&builder->infoSection->contents, 0);
    sdvm_dwarf_encodeWord(&builder->infoSection->contents, builder->version);
    sdvm_dwarf_encodeDwarfPointerSectionRelative(builder->infoSection, builder->abbrevSection, 0); // Debug abbrev offset
    sdvm_dwarf_encodeByte(&builder->infoSection->contents, builder->pointerSize); // Address size.
}

SDVM_API void sdvm_dwarf_debugInfo_destroy(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dynarray_destroy(&builder->locationExpression);
}

SDVM_API void sdvm_dwarf_debugInfo_finish(sdvm_dwarf_debugInfo_builder_t *builder)
{
    // End the abbreviations.
    sdvm_dwarf_encodeByte(&builder->abbrevSection->contents, 0);

    // Info initial length.
    {
        uint32_t infoInitialLength = (uint32_t)(builder->infoSection->contents.size - 4);
        memcpy(builder->infoSection->contents.data, &infoInitialLength, 4);
    }
}

SDVM_API void sdvm_dwarf_debugInfo_beginLineInformation(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeDWord(&builder->lineSection->contents, 0);
    sdvm_dwarf_encodeWord(&builder->lineSection->contents, builder->version);
    builder->lineHeaderLengthOffset = (uint32_t)sdvm_dwarf_encodeDWord(&builder->lineSection->contents, 0); // Header length
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.minimumInstructionLength);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.maximumOperationsPerInstruction);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.defaultIsStatement);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.lineBase);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.lineRange);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, builder->lineProgramHeader.opcodeBase);

    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_copy
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_advance_pc
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_advance_line
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_set_file
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_set_column
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_negate_stmt
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_set_basic_block
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_const_add_pc
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_fixed_advance_pc
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_set_prologue_end
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0); // DW_LNS_set_epilogue_begin
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 1); // DW_LNS_set_isa

    builder->lineProgramState.regAddress = 0;
    builder->lineProgramState.regOpIndex = 0;
    builder->lineProgramState.regFile = 1;
    builder->lineProgramState.regLine = 1;
    builder->lineProgramState.regColumn = 0;
    builder->lineProgramState.regIsStatement = builder->lineProgramHeader.defaultIsStatement;
    builder->lineProgramState.regBasicBlock = false;
    builder->lineProgramState.regEndSequence = false;
    builder->lineProgramState.regPrologueEnd = false;
    builder->lineProgramState.regEpilogueBegin = false;
    builder->lineProgramState.regISA = 0;
    builder->lineProgramState.regDiscriminator = false;
}

SDVM_API void sdvm_dwarf_debugInfo_addDirectory(sdvm_dwarf_debugInfo_builder_t *builder, const char *name, size_t nameSize)
{
    if(nameSize == 0)
        sdvm_dwarf_encodeCString(&builder->lineSection->contents, ".");
    else
        sdvm_dwarf_encodeString(&builder->lineSection->contents, name, nameSize);
}

SDVM_API void sdvm_dwarf_debugInfo_endDirectoryList(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_addFile(sdvm_dwarf_debugInfo_builder_t *builder, uint32_t directoryIndex, const char *name, size_t nameSize, const char *source, size_t sourceSize)
{
    (void)source;
    (void)sourceSize;
    if(nameSize == 0)
        sdvm_dwarf_encodeCString(&builder->lineSection->contents, ".");
    else
        sdvm_dwarf_encodeString(&builder->lineSection->contents, name, nameSize);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, directoryIndex);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, 0); // Last modification time.
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, 0); // Size in bytes.
}

SDVM_API void sdvm_dwarf_debugInfo_endFileList(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_endLineInformationHeader(sdvm_dwarf_debugInfo_builder_t *builder)
{
    uint32_t headerSize = (uint32_t)(builder->lineSection->contents.size - builder->lineHeaderLengthOffset - 4);
    memcpy(builder->lineSection->contents.data + builder->lineHeaderLengthOffset, &headerSize, 4);
}

SDVM_API void sdvm_dwarf_debugInfo_line_setAddress(sdvm_dwarf_debugInfo_builder_t *builder, sdvm_compilerObjectSection_t *section, size_t pc)
{
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, 1 + builder->pointerSize);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNE_set_address);

    sdvm_dwarf_encodeRelocatablePointer(builder->lineSection, builder->pointerSize, section, pc);
    builder->lineProgramState.regAddress = (uint32_t)pc;
}

SDVM_API void sdvm_dwarf_debugInfo_line_setFile(sdvm_dwarf_debugInfo_builder_t *builder, uint32_t file)
{
    if(builder->lineProgramState.regFile == file)
        return;

    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNS_set_file);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, file);
    builder->lineProgramState.regFile = file;
}

SDVM_API void sdvm_dwarf_debugInfo_line_setColumn(sdvm_dwarf_debugInfo_builder_t *builder, int column)
{
    if(builder->lineProgramState.regColumn == column)
        return;

    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNS_set_column);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, column);
    builder->lineProgramState.regColumn = column;
}

SDVM_API void sdvm_dwarf_debugInfo_line_advanceLine(sdvm_dwarf_debugInfo_builder_t *builder, int deltaLine)
{
    if(deltaLine == 0)
        return;

    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNS_advance_line);
    sdvm_dwarf_encodeSLEB128(&builder->lineSection->contents, deltaLine);
    builder->lineProgramState.regLine += deltaLine;
}

SDVM_API void sdvm_dwarf_debugInfo_line_advancePC(sdvm_dwarf_debugInfo_builder_t *builder, int deltaPC)
{
    if(deltaPC == 0)
        return;

    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNS_advance_pc);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, deltaPC);
    builder->lineProgramState.regAddress += deltaPC;
}

SDVM_API void sdvm_dwarf_debugInfo_line_copyRow(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNS_copy);
    builder->lineProgramState.regDiscriminator = false;
    builder->lineProgramState.regBasicBlock = false;
    builder->lineProgramState.regPrologueEnd = false;
    builder->lineProgramState.regEpilogueBegin = false;
}

SDVM_API void sdvm_dwarf_debugInfo_line_advanceLineAndPC(sdvm_dwarf_debugInfo_builder_t *builder, int deltaLine, int deltaPC)
{
    int operationAdvance = deltaPC / builder->lineProgramHeader.minimumInstructionLength;

    int opcode = (deltaLine - builder->lineProgramHeader.lineBase) + (builder->lineProgramHeader.lineRange * operationAdvance) + builder->lineProgramHeader.opcodeBase;
    if( (0 <= opcode) && (opcode <= 255) 
        && (deltaLine - builder->lineProgramHeader.lineBase < builder->lineProgramHeader.lineRange)
        && (deltaLine >= builder->lineProgramHeader.lineBase) )
    {
        sdvm_dwarf_encodeByte(&builder->lineSection->contents, opcode);
        builder->lineProgramState.regLine += deltaLine;
        builder->lineProgramState.regAddress += deltaPC;
    }
    else
    {
        sdvm_dwarf_debugInfo_line_advanceLine(builder, deltaLine);
        sdvm_dwarf_debugInfo_line_advancePC(builder, deltaPC);
        sdvm_dwarf_debugInfo_line_copyRow(builder);
    }
}

SDVM_API void sdvm_dwarf_debugInfo_line_endSequence(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, 0);
    sdvm_dwarf_encodeULEB128(&builder->lineSection->contents, 1);
    sdvm_dwarf_encodeByte(&builder->lineSection->contents, DW_LNE_end_sequence);
}

SDVM_API void sdvm_dwarf_debugInfo_endLineInformation(sdvm_dwarf_debugInfo_builder_t *builder)
{
    uint32_t lineInfoSize = (uint32_t)(builder->lineSection->contents.size - 4);
    memcpy(builder->lineSection->contents.data, &lineInfoSize, 4);
}

SDVM_API size_t sdvm_dwarf_debugInfo_beginDIE(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t tag, bool hasChildren)
{
    int abbreviationCode = ++builder->abbreviationCount;
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, abbreviationCode);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, tag);
    sdvm_dwarf_encodeByte(&builder->abbrevSection->contents, hasChildren ? DW_CHILDREN_yes : DW_CHILDREN_no);

    return sdvm_dwarf_encodeULEB128(&builder->infoSection->contents, abbreviationCode);
}

SDVM_API void sdvm_dwarf_debugInfo_endDIE(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->abbrevSection->contents, 0);
    sdvm_dwarf_encodeByte(&builder->abbrevSection->contents, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_endDIEChildren(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeULEB128(&builder->infoSection->contents, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_uleb128(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, uint32_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_udata);

    sdvm_dwarf_encodeULEB128(&builder->infoSection->contents, value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_secOffset(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, sdvm_compilerObjectSection_t *targetSection, uint32_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_sec_offset);

    sdvm_dwarf_encodeSectionRelative32(builder->infoSection, targetSection, value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_string(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, const char *value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_strp);

    size_t stringOffset = sdvm_dwarf_encodeCString(&builder->strSection->contents, value);
    sdvm_dwarf_encodeSectionRelative32(builder->infoSection, builder->strSection, stringOffset);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_moduleString(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, sdvm_module_t *module, sdvm_moduleString_t string)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_strp);

    size_t stringOffset = builder->strSection->contents.size;
    sdvm_dynarray_addAll(&builder->strSection->contents, string.stringSectionSize, module->stringSectionData + string.stringSectionOffset);
    sdvm_dwarf_encodeByte(&builder->strSection->contents, 0);
    sdvm_dwarf_encodeSectionRelative32(builder->infoSection, builder->strSection, stringOffset);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_optionalModuleString(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, sdvm_module_t *module, sdvm_moduleString_t string)
{
    if(string.stringSectionSize == 0)
        return;

    sdvm_dwarf_debugInfo_attribute_moduleString(builder, attribute, module, string);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_ref1(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, uint8_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_ref1);
    sdvm_dwarf_encodeByte(&builder->infoSection->contents, value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_address(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute, sdvm_compilerObjectSection_t *targetSection, uint64_t offset)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_addr);

    sdvm_dwarf_encodeRelocatablePointer(builder->infoSection, builder->pointerSize, targetSection, offset);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_beginLocationExpression(sdvm_dwarf_debugInfo_builder_t *builder, uint64_t attribute)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrevSection->contents, DW_FORM_exprloc);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_endLocationExpression(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeULEB128(&builder->infoSection->contents, builder->locationExpression.size);
    sdvm_dynarray_addAll(&builder->infoSection->contents, builder->locationExpression.size, builder->locationExpression.data);
    builder->locationExpression.size = 0;
}

SDVM_API void sdvm_dwarf_debugInfo_location_constUnsigned(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t constant)
{
    if(constant <= 31)
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_lit0 + (uint8_t)constant);
        return;
    }

    if(constant <= 0xFF)
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_const1u);
        sdvm_dwarf_encodeByte(&builder->locationExpression, (uint8_t)constant);
        return;
    }

    if(constant <= 0xFFFF)
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_const2u);
        sdvm_dwarf_encodeWord(&builder->locationExpression, (uint16_t)constant);
        return;
    }

    if(constant <= 0xFFFFFFFF)
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_const4u);
        sdvm_dwarf_encodeDWord(&builder->locationExpression, (uint32_t)constant);
        return;
    }

    sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_const8u);
    sdvm_dwarf_encodeQWord(&builder->locationExpression, (uint64_t)constant);
}

SDVM_API void sdvm_dwarf_debugInfo_location_deref(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_deref);
}

SDVM_API void sdvm_dwarf_debugInfo_location_frameBaseOffset(sdvm_dwarf_debugInfo_builder_t *builder, intptr_t offset)
{
    sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_fbreg);
    sdvm_dwarf_encodeSLEB128(&builder->locationExpression, offset);
}

SDVM_API void sdvm_dwarf_debugInfo_location_plus(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_plus);
}

SDVM_API void sdvm_dwarf_debugInfo_location_register(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t reg)
{
    if(reg <= 31)
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_reg0 + (uint8_t)reg);
    }
    else
    {
        sdvm_dwarf_encodeByte(&builder->locationExpression, DW_OP_regx);
        sdvm_dwarf_encodeULEB128(&builder->locationExpression, reg);
    }
}
