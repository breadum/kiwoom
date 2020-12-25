from enum import Enum


class CodeType(Enum):
    stock = 0
    sector = 1

    def __str__(self):
        return self.name


class OutputType(Enum):
    single = 0
    multi = 1

    def __str__(self):
        return self.name

    def __index__(self):
        return self.value


# Global variables
single = OutputType(0)
multi = OutputType(1)
