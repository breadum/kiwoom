from enum import Enum


class CodeType(Enum):
    STOCK = 0
    SECTOR = 1

    def __str__(self):
        return self.name


class OutputType(Enum):
    SINGLE = 0
    MULTI = 1

    def __str__(self):
        return self.name

    def __index__(self):
        return self.value


class ExitType(Enum):
    # Return codes
    SUCCESS = 0
    FAILURE = -1
    # Hidden config
    IMPOSSIBLE = 712

    def __int__(self):
        return self.value


# Global variables
STOCK = CodeType.STOCK
SECTOR = CodeType.SECTOR

SINGLE = OutputType(0)
MULTI = OutputType(1)

SUCCESS = ExitType.SUCCESS
FAILURE = ExitType.FAILURE
IMPOSSIBLE = ExitType.IMPOSSIBLE
