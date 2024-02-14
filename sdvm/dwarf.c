#include "dwarf.h"
#include "assert.h"
#include <stdbool.h>
#include <string.h>


SDVM_API size_t sdvm_dwarf_encodeDwarfPointer(sdvm_dynarray_t *buffer, uint32_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeDwarfPointerPCRelative(sdvm_dynarray_t *buffer, uint32_t value)
{
    int32_t pcRelativeValue = (int32_t)(buffer->size - value);
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(pcRelativeValue), &pcRelativeValue);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodePointer(sdvm_dynarray_t *buffer, uintptr_t value)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, sizeof(value), &value);
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

SDVM_API size_t sdvm_dwarf_encodeCString(sdvm_dynarray_t *buffer, const char *cstring)
{
    size_t offset = buffer->size;
    sdvm_dynarray_addAll(buffer, strlen(cstring) + 1, cstring);
    return offset;
}

SDVM_API size_t sdvm_dwarf_encodeULEB128(sdvm_dynarray_t *buffer, uintptr_t value)
{
    size_t offset = buffer->size;
    uintptr_t currentValue = value;
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

SDVM_API size_t sdvm_dwarf_encodeSLEB128(sdvm_dynarray_t *buffer, intptr_t value)
{
    size_t offset = buffer->size;
    bool more = true;

    intptr_t currentValue = value;
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

SDVM_API void sdvm_dwarf_cfi_create(sdvm_dwarf_cfi_builder_t *cfi)
{
    memset(cfi, 0, sizeof(sdvm_dwarf_cfi_builder_t));
    cfi->version = 1;
    cfi->isEhFrame = true;
    sdvm_dynarray_initialize(&cfi->buffer, 1, 1024);
}

SDVM_API void sdvm_dwarf_cfi_destroy(sdvm_dwarf_cfi_builder_t *cfi)
{
    sdvm_dynarray_destroy(&cfi->buffer);
}

SDVM_API void sdvm_dwarf_cfi_beginCIE(sdvm_dwarf_cfi_builder_t *cfi, sdvm_dwarf_cie_t *cie)
{
    cfi->cieOffset = sdvm_dwarf_encodeDWord(&cfi->buffer, 0);
    cfi->cieContentOffset = sdvm_dwarf_encodeDwarfPointer(&cfi->buffer, cfi->isEhFrame ? 0 : -1 ); // CIE_id
    cfi->cie = *cie;
    sdvm_dwarf_encodeByte(&cfi->buffer, cfi->version);
    sdvm_dwarf_encodeCString(&cfi->buffer, cfi->isEhFrame ? "zR" : ""); // Argumentation
    if(!cfi->isEhFrame)
    {
        sdvm_dwarf_encodeByte(&cfi->buffer, sizeof(uintptr_t)); // Address size
        sdvm_dwarf_encodeByte(&cfi->buffer, 0); // Segment size
    }
    sdvm_dwarf_encodeULEB128(&cfi->buffer, cie->codeAlignmentFactor);
    sdvm_dwarf_encodeSLEB128(&cfi->buffer, cie->dataAlignmentFactor);
    if(cfi->version <= 2 && !cfi->isEhFrame)
        sdvm_dwarf_encodeByte(&cfi->buffer, (uint8_t)cie->returnAddressRegister);
    else
        sdvm_dwarf_encodeULEB128(&cfi->buffer, cie->returnAddressRegister);
    if(cfi->isEhFrame)
    {
        sdvm_dwarf_encodeULEB128(&cfi->buffer, 1);
        sdvm_dwarf_encodeByte(&cfi->buffer, DW_EH_PE_pcrel | DW_EH_PE_sdata4);
    }
}

SDVM_API void sdvm_dwarf_cfi_endCIE(sdvm_dwarf_cfi_builder_t *cfi)
{
    sdvm_dwarf_encodeAlignment(&cfi->buffer, sizeof(uintptr_t));
    uint32_t cieSize = (uint32_t)(cfi->buffer.size - cfi->cieContentOffset);
    memcpy(cfi->buffer.data + cfi->cieOffset, &cieSize, 4);
}

SDVM_API void sdvm_dwarf_cfi_beginFDE(sdvm_dwarf_cfi_builder_t *cfi, size_t pc)
{
    cfi->fdeOffset = sdvm_dwarf_encodeDWord(&cfi->buffer, 0);
    cfi->fdeContentOffset = sdvm_dwarf_encodeDwarfPointerPCRelative(&cfi->buffer, (uint32_t)cfi->cieOffset);
    cfi->fdeInitialPC = pc;
    if(cfi->isEhFrame)
    {
        cfi->fdeInitialLocationOffset = sdvm_dwarf_encodeDWord(&cfi->buffer, 0);
        cfi->fdeAddressingRangeOffset = sdvm_dwarf_encodeDWord(&cfi->buffer, 0);
        sdvm_dwarf_encodeULEB128(&cfi->buffer, 0);
    }
    else
    {
        cfi->fdeInitialLocationOffset = sdvm_dwarf_encodePointer(&cfi->buffer, 0);
        cfi->fdeAddressingRangeOffset = sdvm_dwarf_encodePointer(&cfi->buffer, 0);
    }
    cfi->currentPC = cfi->fdeInitialPC;
    cfi->stackFrameSize = cfi->initialStackFrameSize;
    cfi->framePointerRegister = 0;
    cfi->hasFramePointerRegister = false;
    cfi->isInPrologue = true;
}

SDVM_API void sdvm_dwarf_cfi_endFDE(sdvm_dwarf_cfi_builder_t *cfi, size_t pc)
{
    sdvm_dwarf_encodeAlignment(&cfi->buffer, sizeof(uintptr_t));
    if(cfi->isEhFrame)
    {
        uint32_t pcRange = (uint32_t)(pc - cfi->fdeInitialPC);
        memcpy(cfi->buffer.data + cfi->fdeAddressingRangeOffset, &pcRange, sizeof(uint32_t));
    }
    else
    {
        uintptr_t pcRange = pc - cfi->fdeInitialPC;
        memcpy(cfi->buffer.data + cfi->fdeAddressingRangeOffset, &pcRange, sizeof(uintptr_t));
    }

    uint32_t fdeSize = (uint32_t)(cfi->buffer.size - cfi->fdeContentOffset);
    memcpy(cfi->buffer.data + cfi->fdeOffset, &fdeSize, 4);
}

SDVM_API void sdvm_dwarf_cfi_finish(sdvm_dwarf_cfi_builder_t *cfi)
{
    sdvm_dwarf_encodeDWord(&cfi->buffer, 0);
}

SDVM_API void sdvm_dwarf_cfi_setPC(sdvm_dwarf_cfi_builder_t *cfi, size_t pc)
{
    size_t advance = pc - cfi->currentPC;
    if(advance)
    {
        size_t advanceFactor = advance / cfi->cie.codeAlignmentFactor;
        if(advanceFactor <= 63)
        {
            sdvm_dwarf_encodeByte(&cfi->buffer, (DW_OP_CFA_advance_loc << 6) | (uint8_t)advanceFactor);
        }
        else
        {
            if(advanceFactor <= 0xFF)
            {
                sdvm_dwarf_encodeByte(&cfi->buffer, DW_OP_CFA_advance_loc1);
                sdvm_dwarf_encodeByte(&cfi->buffer, (uint8_t)advanceFactor);
            }
            else if(advanceFactor <= 0xFFFF)
            {
                sdvm_dwarf_encodeByte(&cfi->buffer, DW_OP_CFA_advance_loc2);
                sdvm_dwarf_encodeWord(&cfi->buffer, (uint16_t)advanceFactor);
            }
            else
            {
                SDVM_ASSERT(advanceFactor <= 0xFFFFFFFF);
                sdvm_dwarf_encodeByte(&cfi->buffer, DW_OP_CFA_advance_loc4);
                sdvm_dwarf_encodeDWord(&cfi->buffer, (uint32_t)advanceFactor);
            }
        }
    }

    cfi->currentPC = pc;
}

SDVM_API void sdvm_dwarf_cfi_cfaInRegisterWithOffset(sdvm_dwarf_cfi_builder_t *cfi, uintptr_t reg, intptr_t offset)
{
    sdvm_dwarf_encodeByte(&cfi->buffer, DW_OP_CFA_def_cfa);
    sdvm_dwarf_encodeULEB128(&cfi->buffer, reg);
    sdvm_dwarf_encodeULEB128(&cfi->buffer, offset);
}

SDVM_API void sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(sdvm_dwarf_cfi_builder_t *cfi, uintptr_t reg, size_t offset)
{
    sdvm_dwarf_cfi_cfaInRegisterWithOffset(cfi, reg, sizeof(uintptr_t) * offset);
}

SDVM_API void sdvm_dwarf_cfi_registerValueAtFactoredOffset(sdvm_dwarf_cfi_builder_t *cfi, uintptr_t reg, size_t offset)
{
    if(reg <= 63) {
        sdvm_dwarf_encodeByte(&cfi->buffer, (DW_OP_CFA_offset << 6) | (uint8_t)reg);
        sdvm_dwarf_encodeULEB128(&cfi->buffer, offset);
    } else {
        sdvm_dwarf_encodeByte(&cfi->buffer, DW_OP_CFA_offset_extended);
        sdvm_dwarf_encodeULEB128(&cfi->buffer, reg);
        sdvm_dwarf_encodeULEB128(&cfi->buffer, offset);
    }
}

SDVM_API void sdvm_dwarf_cfi_pushRegister(sdvm_dwarf_cfi_builder_t *cfi, uintptr_t reg)
{
    ++cfi->stackFrameSize;
    if(!cfi->hasFramePointerRegister)
        sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, cfi->stackPointerRegister, cfi->stackFrameSize);
    sdvm_dwarf_cfi_registerValueAtFactoredOffset(cfi, reg, cfi->stackFrameSize);
}

SDVM_API void sdvm_dwarf_cfi_saveFramePointerInRegister(sdvm_dwarf_cfi_builder_t *cfi, uintptr_t reg, intptr_t offset)
{
    SDVM_ASSERT(!cfi->hasFramePointerRegister);
    SDVM_ASSERT((offset % sizeof(uintptr_t)) == 0);

    cfi->hasFramePointerRegister = true;
    cfi->framePointerRegister = reg;
    cfi->stackFrameSizeAtFramePointer = cfi->stackFrameSize - offset / sizeof(uintptr_t);
    sdvm_dwarf_cfi_cfaInRegisterWithFactoredOffset(cfi, reg, cfi->stackFrameSizeAtFramePointer);
}

SDVM_API void sdvm_dwarf_cfi_stackSizeAdvance(sdvm_dwarf_cfi_builder_t *cfi, size_t pc, size_t increment)
{
    if(!cfi->isInPrologue) return;
    if(!increment) return;
    
    cfi->stackFrameSize += increment / sizeof(uintptr_t);
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

SDVM_API void sdvm_dwarf_debugInfo_create(sdvm_dwarf_debugInfo_builder_t *builder)
{
    memset(builder, 0, sizeof(sdvm_dwarf_debugInfo_builder_t));
    builder->version = 4;
    builder->lineProgramHeader.minimumInstructionLength = 1;
    builder->lineProgramHeader.maximumOperationsPerInstruction = 1;
    builder->lineProgramHeader.opcodeBase = 13;
    builder->lineProgramHeader.defaultIsStatement = true;

    sdvm_dynarray_initialize(&builder->locationExpression, 1, 256);

    sdvm_dynarray_initialize(&builder->line, 1, 1024);
    sdvm_dynarray_initialize(&builder->str, 1, 1024);
    sdvm_dynarray_initialize(&builder->abbrev, 1, 1024);
    sdvm_dynarray_initialize(&builder->info, 1, 1024);
    sdvm_dynarray_initialize(&builder->lineTextAddresses, sizeof(uint32_t), 1024);
    sdvm_dynarray_initialize(&builder->infoTextAddresses, sizeof(uint32_t), 32);

    // Null string.
    sdvm_dwarf_encodeByte(&builder->str, 0);

    // Info header
    sdvm_dwarf_encodeDwarfPointer(&builder->info, 0);
    sdvm_dwarf_encodeWord(&builder->info, builder->version);
    sdvm_dwarf_encodeDwarfPointer(&builder->info, 0); // Debug abbrev offset
    sdvm_dwarf_encodeByte(&builder->info, sizeof(uintptr_t)); // Address size.
}

SDVM_API void sdvm_dwarf_debugInfo_destroy(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dynarray_destroy(&builder->locationExpression);
    sdvm_dynarray_destroy(&builder->line);
    sdvm_dynarray_destroy(&builder->str);
    sdvm_dynarray_destroy(&builder->abbrev);
    sdvm_dynarray_destroy(&builder->info);
    sdvm_dynarray_destroy(&builder->lineTextAddresses);
    sdvm_dynarray_destroy(&builder->infoTextAddresses);
}

SDVM_API void sdvm_dwarf_debugInfo_finish(sdvm_dwarf_debugInfo_builder_t *builder)
{
    // End the abbreviations.
    sdvm_dwarf_encodeByte(&builder->abbrev, 0);

    // Info initial length.
    {
        uint32_t infoInitialLength = (uint32_t)(builder->info.size - 4);
        memcpy(builder->info.data, &infoInitialLength, 4);
    }
}

SDVM_API void sdvm_dwarf_debugInfo_patchTextAddressesRelativeTo(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t baseAddress)
{
    uint32_t *lineOffsets = (uint32_t*)builder->lineTextAddresses.data;
    for(size_t i = 0; i < builder->lineTextAddresses.size; ++i)
    {
        uintptr_t *address = (uintptr_t *)(builder->line.data + lineOffsets[i]);
        *address += baseAddress;
    }

    uint32_t *infoOffsets = (uint32_t*)builder->infoTextAddresses.data;
    for(size_t i = 0; i < builder->infoTextAddresses.size; ++i)
    {
        uintptr_t *address = (uintptr_t *)(builder->info.data + infoOffsets[i]);
        *address += baseAddress;
    }
}

SDVM_API void sdvm_dwarf_debugInfo_beginLineInformation(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeDWord(&builder->line, 0);
    sdvm_dwarf_encodeWord(&builder->line, builder->version);
    builder->lineHeaderLengthOffset = (uint32_t)sdvm_dwarf_encodeDWord(&builder->line, 0); // Header length
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.minimumInstructionLength);
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.maximumOperationsPerInstruction);
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.defaultIsStatement);
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.lineBase);
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.lineRange);
    sdvm_dwarf_encodeByte(&builder->line, builder->lineProgramHeader.opcodeBase);

    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_copy
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_advance_pc
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_advance_line
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_set_file
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_set_column
    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_negate_stmt
    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_set_basic_block
    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_const_add_pc
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_fixed_advance_pc
    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_set_prologue_end
    sdvm_dwarf_encodeByte(&builder->line, 0); // DW_LNS_set_epilogue_begin
    sdvm_dwarf_encodeByte(&builder->line, 1); // DW_LNS_set_isa

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

SDVM_API void sdvm_dwarf_debugInfo_endDirectoryList(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->line, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_endFileList(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->line, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_endLineInformationHeader(sdvm_dwarf_debugInfo_builder_t *builder)
{
    uint32_t headerSize = (uint32_t)(builder->line.size - builder->lineHeaderLengthOffset - 4);
    memcpy(builder->line.data + builder->lineHeaderLengthOffset, &headerSize, 4);
}

SDVM_API void sdvm_dwarf_debugInfo_line_setAddress(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t value)
{
    sdvm_dwarf_encodeByte(&builder->line, 0);
    sdvm_dwarf_encodeULEB128(&builder->line, 1 + sizeof(value));
    sdvm_dwarf_encodeByte(&builder->line, DW_LNE_set_address);
    uint32_t addressOffset = (uint32_t)sdvm_dwarf_encodePointer(&builder->line, value);
    sdvm_dynarray_add(&builder->lineTextAddresses, &addressOffset);
    builder->lineProgramState.regAddress = (uint32_t)value;
}

SDVM_API void sdvm_dwarf_debugInfo_line_setFile(sdvm_dwarf_debugInfo_builder_t *builder, uint32_t file)
{
    if(builder->lineProgramState.regFile == file)
        return;

    sdvm_dwarf_encodeByte(&builder->line, DW_LNS_set_file);
    sdvm_dwarf_encodeULEB128(&builder->line, file);
    builder->lineProgramState.regFile = file;
}

SDVM_API void sdvm_dwarf_debugInfo_line_setColumn(sdvm_dwarf_debugInfo_builder_t *builder, int column)
{
    if(builder->lineProgramState.regColumn == column)
        return;

    sdvm_dwarf_encodeByte(&builder->line, DW_LNS_set_column);
    sdvm_dwarf_encodeULEB128(&builder->line, column);
    builder->lineProgramState.regColumn = column;
}

SDVM_API void sdvm_dwarf_debugInfo_line_advanceLine(sdvm_dwarf_debugInfo_builder_t *builder, int deltaLine)
{
    if(deltaLine == 0)
        return;

    sdvm_dwarf_encodeByte(&builder->line, DW_LNS_advance_line);
    sdvm_dwarf_encodeSLEB128(&builder->line, deltaLine);
    builder->lineProgramState.regLine += deltaLine;
}

SDVM_API void sdvm_dwarf_debugInfo_line_advancePC(sdvm_dwarf_debugInfo_builder_t *builder, int deltaPC)
{
    if(deltaPC == 0)
        return;

    sdvm_dwarf_encodeByte(&builder->line, DW_LNS_advance_pc);
    sdvm_dwarf_encodeULEB128(&builder->line, deltaPC);
    builder->lineProgramState.regAddress += deltaPC;
}

SDVM_API void sdvm_dwarf_debugInfo_line_copyRow(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->line, DW_LNS_copy);
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
        sdvm_dwarf_encodeByte(&builder->line, opcode);
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
    sdvm_dwarf_encodeByte(&builder->line, 0);
    sdvm_dwarf_encodeULEB128(&builder->line, 1);
    sdvm_dwarf_encodeByte(&builder->line, DW_LNE_end_sequence);
}

SDVM_API void sdvm_dwarf_debugInfo_endLineInformation(sdvm_dwarf_debugInfo_builder_t *builder)
{
    uint32_t lineInfoSize = (uint32_t)(builder->line.size - 4);
    memcpy(builder->line.data, &lineInfoSize, 4);
}

SDVM_API size_t sdvm_dwarf_debugInfo_beginDIE(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t tag, bool hasChildren)
{
    int abbreviationCode = ++builder->abbreviationCount;
    sdvm_dwarf_encodeULEB128(&builder->abbrev, abbreviationCode);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, tag);
    sdvm_dwarf_encodeByte(&builder->abbrev, hasChildren ? DW_CHILDREN_yes : DW_CHILDREN_no);

    return sdvm_dwarf_encodeULEB128(&builder->info, abbreviationCode);
}

SDVM_API void sdvm_dwarf_debugInfo_endDIE(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeByte(&builder->abbrev, 0);
    sdvm_dwarf_encodeByte(&builder->abbrev, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_endDIEChildren(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeULEB128(&builder->info, 0);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_uleb128(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute, uintptr_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_udata);

    sdvm_dwarf_encodeULEB128(&builder->info, value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_secOffset(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute, uintptr_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_sec_offset);

    sdvm_dwarf_encodeDWord(&builder->info, (uint32_t)value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_string(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute, const char *value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_strp);

    size_t stringOffset = sdvm_dwarf_encodeCString(&builder->str, value);
    sdvm_dwarf_encodeDWord(&builder->info, (uint32_t)stringOffset);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_ref1(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute, uint8_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_ref1);
    sdvm_dwarf_encodeByte(&builder->info, value);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_textAddress(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute, uintptr_t value)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_addr);

    uint32_t addressOffset = (uint32_t)sdvm_dwarf_encodePointer(&builder->info, value);
    sdvm_dynarray_add(&builder->infoTextAddresses, &addressOffset);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_beginLocationExpression(sdvm_dwarf_debugInfo_builder_t *builder, uintptr_t attribute)
{
    sdvm_dwarf_encodeULEB128(&builder->abbrev, attribute);
    sdvm_dwarf_encodeULEB128(&builder->abbrev, DW_FORM_exprloc);
}

SDVM_API void sdvm_dwarf_debugInfo_attribute_endLocationExpression(sdvm_dwarf_debugInfo_builder_t *builder)
{
    sdvm_dwarf_encodeULEB128(&builder->info, builder->locationExpression.size);
    sdvm_dynarray_addAll(&builder->info, builder->locationExpression.size, builder->locationExpression.data);
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
