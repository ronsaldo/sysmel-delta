class MemoryDescriptor:
    def __init__(self, size: int, alignment: int, gcDescriptor = None) -> None:
        self.size = size
        self.alignment = alignment
        self.gcDescriptor = gcDescriptor
        self.key = (self.size, self.alignment)

    def __eq__(self, other: object) -> bool:
        return self.key == other.key

    def __hash__(self) -> int:
        return self.key.__hash__()

    def __str__(self) -> str:
        return '(size %d alignment %d)' % (self.size, self.alignment)
