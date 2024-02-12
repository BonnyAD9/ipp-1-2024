from enum import IntEnum

class Error(IntEnum):
    """Possible errors returned by the parse program"""

    NONE = 0
    ARGS = 10
    INVALID_HEADER = 21
    INVALID_OPCODE = 22
    PARSE = 23
    OTHER = 99
