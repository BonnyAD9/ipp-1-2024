from enum import IntEnum

class Error(IntEnum):
    """Possible errors returned by the parse program"""

    NONE = 0
    ARGS = 10
    TWICE_SAME_FILE = 12
    INVALID_HEADER = 21
    INVALID_OPCODE = 22
    PARSE = 23
    OTHER = 99
