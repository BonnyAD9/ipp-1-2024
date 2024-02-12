from typing import TextIO
from enum import Enum, auto
import re

class TokenType(Enum):
    EOF = auto()
    ERR = auto()
    NEWLINE = auto()
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

    def __init__(self, type: TokenType, value: str = ""):
        self.type = type
        self.value = value

# regexes for checking validity of some tokens

# Checks for valid identifiers, labels or instructions
_IDENT_RE = re.compile(r"[0-9A-Za-z_\-$&%*!?]*")
# Checks for valid integer literals
_INT_RE = re.compile(r"[+\-]([0-9]|0x[0-9A-Fa-f]|0o[0-7])")
# checks for valid string literals
_STRING_RE = re.compile(r"([^\\]|\\[0-9][0-9][0-9])*")

class Lexer:
    def __init__(self, input: TextIO) -> None:
        # The input stream
        self.input = input
        # Tokens to be returned, the list is reversed (first token to be
        # returned is the last in the list)
        self.queue: list[Token] = []

    def next(self) -> Token:
        """Gets the next token"""

        # if the queue contains tokens, return from there otherwise read new
        # tokens
        return self._read_next() if not self.queue else self.queue.pop()

    def _read_next(self) -> Token:
        """Reads next line of input and creates it into tokens"""

        # read next line and check for eof
        line = self.input.readline()
        if not line:
            return Token(TokenType.EOF)

        # last token of each line is always newline
        self.queue.append(Token(TokenType.NEWLINE))
        # The tokens in the source are always separated by whitespace and there
        # are no other whitespaces so we can split by whitespace.
        # The tokens are reversed so that they can be efficiently readed from
        # the queue.
        for s in reversed(line.split()):
            # check for comments
            if s[0] == "#":
                # reading from back, ignore what was already readed
                self.queue.clear()
                # don't forget to add the newline as the last token
                self.queue.append(Token(TokenType.NEWLINE))
            else:
                self.queue.append(Lexer._parse_token(s))

        # the queue always contains at least newline
        return self.queue.pop()

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
            else:
                return Token(
                    TokenType.ERR,
                    "unexpected character '@' in '" + s + "'"
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
                    "Unknown data type '" + type + "'"
                )

    @staticmethod
    def _parse_label(s: str) -> Token:
        if _IDENT_RE.fullmatch(s):
            return Token(TokenType.LABEL, s.replace("&", "&amp;"))
        else:
            return Token(TokenType.ERR, "Invalid label name '" + s + "'")

    @staticmethod
    def _parse_ident(s: str) -> Token:
        # `s` also contains the frame, run the checks only on the name
        id = s[3:]
        if _IDENT_RE.fullmatch(id):
            return Token(TokenType.IDENT, s.replace("&", "&amp;"))
        else:
            return Token(TokenType.ERR, "Invalid variable name '" + s + "'")

    @staticmethod
    def _parse_nil(s: str) -> Token:
        if s == "nil":
            return Token(TokenType.NIL, "nil")
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
