from typing import TextIO
from enum import Enum, auto
import re

class TokenType(Enum):
    EOF = auto()
    ERR = auto()
    DIRECTIVE = auto()
    # label represents opcode, label name or type. Which of these it is is
    # determined by parser based on context.
    LABEL = auto()
    IDENT = auto()
    NIL = auto()
    BOOL = auto()
    INT = auto()
    STRING = auto()
    TYPE = auto()

class Token:
    """Contains the token type and string value of the token."""

    def __init__(self, typ: TokenType, value: str = ""):
        self.type = typ
        self.value = value

# regexes for checking validity of some tokens

# Checks for valid identifiers, labels or instructions
_IDENT_RE = re.compile(r"[A-Za-z_\-$&%*!?][0-9A-Za-z_\-$&%*!?]*")
# Checks for valid integer literals
_INT_RE = re.compile(r"[+\-]?([0-9][0-9_]*|0x[0-9A-Fa-f_]*|0o[0-7_]*)")
# checks for valid string literals
_STRING_RE = re.compile(r"([^\\]|\\[0-9][0-9][0-9])*")

class Lexer:
    def __init__(self, input: TextIO) -> None:
        # The input stream
        self.input = input
        # comments will be ignored with tokenization, the stats about them must
        # be collected here
        self.comment_count = 0

    def next(self) -> list[Token]:
        """Gets the next token"""

        n = self._read_next();
        while not n:
            n = self._read_next();
        return n

    def _read_next(self) -> list[Token]:
        """Reads next line of input and creates it into tokens"""

        # read next line and check for eof
        line = self.input.readline()
        if not line:
            return [Token(TokenType.EOF)]

        queue: list[Token] = []

        for s in line.split():
            # check for comments
            spl = s.split('#', maxsplit=1)
            if spl[0]:
                t = Lexer._parse_token(spl[0]);
                if t.type == TokenType.ERR:
                    return [t]
                queue.append(t)
            if len(spl) > 1:
                self.comment_count += 1;
                return queue

        return queue

    @staticmethod
    def _parse_token(s: str) -> Token:
        # check for special directives (e.g. '.IPPcode24')
        if s[0] == ".":
            return Token(TokenType.DIRECTIVE, s)

        # empty string literals are special case where there is nothing after
        # the `@` symbol
        if s == "string@":
            return Token(TokenType.STRING)

        # split by `@`, if there is no `@` it is label, otherwise the first
        # of the splitted array will determine the token type

        spl = s.split("@")
        if len(spl) == 1:
            return Lexer._parse_label(s)

        # string literals can contain `@`
        if len(spl) > 2:
            if spl[0] == "string":
                return Lexer._parse_string("@".join(spl[1:]))
            return Token(
                TokenType.ERR,
                f"unexpected character '@' in '{s}'"
            )

        type = spl[0]
        value = spl[1]

        # check for the type of the token
        match type:
            case "TF" | "LF" | "GF":
                return Lexer._parse_ident(s)
            case "nil":
                return Lexer._parse_nil(value)
            case "bool":
                return Lexer._parse_bool(value)
            case "int":
                return Lexer._parse_int(value)
            case "string":
                return Lexer._parse_string(value)
            case _:
                return Token(
                    TokenType.ERR,
                    f"Unknown data type '{type}'"
                )

    @staticmethod
    def _parse_label(s: str) -> Token:
        if _IDENT_RE.fullmatch(s):
            return Token(TokenType.LABEL, s.replace("&", "&amp;"))
        return Token(TokenType.ERR, f"Invalid label name '{s}'")

    @staticmethod
    def _parse_ident(s: str) -> Token:
        # `s` also contains the frame, run the checks only on the name
        id = s[3:]
        if _IDENT_RE.fullmatch(id):
            return Token(TokenType.IDENT, s.replace("&", "&amp;"))
        return Token(TokenType.ERR, f"Invalid variable name '{s}'")

    @staticmethod
    def _parse_nil(s: str) -> Token:
        if s == "nil":
            return Token(TokenType.NIL, "nil")
        return Token(TokenType.ERR, "type 'nil' can only have value 'nil'")

    @staticmethod
    def _parse_bool(s: str) -> Token:
        match s:
            case "true":
                return Token(TokenType.BOOL, "true")
            case "false":
                return Token(TokenType.BOOL, "false")
            case _:
                return Token(TokenType.ERR, f"Invalid bool value '{s}'")

    @staticmethod
    def _parse_int(s: str) -> Token:
        if _INT_RE.fullmatch(s):
            return Token(TokenType.INT, s)
        return Token(TokenType.ERR, f"Invalid int value '{s}'")

    @staticmethod
    def _parse_string(s: str) -> Token:
        if _STRING_RE.fullmatch(s):
            return Token(
                TokenType.STRING,
                s.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )
        return Token(TokenType.ERR, f"Invalid string value '{s}'")
