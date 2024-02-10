from typing import TextIO
from enum import Enum, auto
import re

class TokenType(Enum):
    EOF = auto()
    ERR = auto()
    NEWLINE = auto()
    DIRECTIVE = auto()
    INSTRUCTION = auto()
    IDENT = auto()
    NIL = auto()
    BOOL = auto()
    INT = auto()
    STRING = auto()

class Token:
    def __init__(self, type: TokenType, value: str = ""):
        self.type = type
        self.value = value

_IDENT_RE = re.compile(r"[0-9A-Za-z_\\-$&%*!?]*")
_INT_RE = re.compile(r"[+\\-]([0-9]|0x[0-9A-Fa-f]|0o[0-7])")
_STRING_RE = re.compile(r"([^\\\\]|\\\\[0-9][0-9][0-9])*")

class Lexer:
    def __init__(self, input: TextIO) -> None:
        self.input = input
        self.cur = " "
        self.queue: list[Token] = []

    def next(self) -> Token:
        return self._read_next() if not self.queue else self.queue.pop()

    def _read_next(self) -> Token:
        line = self.input.readline()
        if not line:
            return Token(TokenType.EOF)

        self.queue.append(Token(TokenType.NEWLINE))
        for s in reversed(line.split()):
            self.queue.append(Lexer._parse_token(s))

        return self.queue.pop()

    @staticmethod
    def _parse_token(s: str) -> Token:
        if s[0] == ".":
            return Token(TokenType.DIRECTIVE, s)

        spl = s.split("@")
        if len(spl) == 1:
            Lexer._parse_instruction(s)

        if len(spl) > 2:
            if spl[0] == "string":
                return Lexer._parse_string("".join(s[1:]))
            else:
                return Token(
                    TokenType.ERR,
                    "unexpected character '@' in '" + s + "'"
                )

        type = spl[0]
        value = spl[1]

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
                    "Unknown data type '" + type + "'"
                )

    @staticmethod
    def _parse_instruction(s: str) -> Token:
        return Token(TokenType.INSTRUCTION, s.upper())

    @staticmethod
    def _parse_ident(s: str) -> Token:
        id = s[3:]
        if _IDENT_RE.fullmatch(id):
            return Token(TokenType.IDENT, s.replace("&", "&amp;"))
        else:
            return Token(TokenType.ERR, "Invalid variable name '" + s + "'")

    @staticmethod
    def _parse_nil(s: str) -> Token:
        if s == "nil":
            return Token(TokenType.NIL)
        else:
            return Token(TokenType.ERR, "type 'nil' can only have value 'nil'")

    @staticmethod
    def _parse_bool(s: str) -> Token:
        match s:
            case "true":
                return Token(TokenType.BOOL, "true")
            case "false":
                return Token(TokenType.BOOL, "false")
            case _:
                return Token(TokenType.ERR, "Invalid bool value '" + s + "'")

    @staticmethod
    def _parse_int(s: str) -> Token:
        if _INT_RE.fullmatch(s):
            return Token(TokenType.INT, s)
        else:
            return Token(TokenType.ERR, "Invalid int value '" + s + "'")

    @staticmethod
    def _parse_string(s: str) -> Token:
        if _STRING_RE.fullmatch(s):
            return Token(
                TokenType.STRING,
                s.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )
        else:
            return Token(TokenType.ERR, "Invalid string value '" + s + "'")
