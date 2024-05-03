class CompilationTarget:
    def __init__(self, triple: str, pointerSize: int) -> None:
        self.triple = triple
        self.pointerSize = pointerSize

DefaultCompilationTarget = CompilationTarget(None, 8)
