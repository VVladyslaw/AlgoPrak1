class User:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name
    def getName(self) -> None:
        print(self.name)
