class CompilationTarget:
    def __init__(self, triple: str, pointerSize: int) -> None:
        self.triple = triple
        self.sizeSize = pointerSize
        self.sizeAlignment = pointerSize
        self.pointerSize = pointerSize
        self.pointerAlignment = pointerSize

DefaultCompilationTarget = CompilationTarget(None, 8)
