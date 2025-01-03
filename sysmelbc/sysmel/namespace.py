class Namespace:
    def __init__(self, name: str) -> None:
        self.name = name
        self.exportedValues = []
        self.mirExportedValues = []
