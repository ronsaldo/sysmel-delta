def alignedTo(offset, alignment):
    return (offset + alignment - 1) & (-alignment)