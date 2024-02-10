from typing import TextIO, Union
from lexer import Lexer, Token, TokenType
from errors import Error

_VAR = [TokenType.IDENT]
_SYMB = [
    TokenType.IDENT,
    TokenType.NIL,
    TokenType.BOOL,
    TokenType.INT,
    TokenType.STRING
]
_LABEL = [TokenType.LABEL]
_TYPE = [TokenType.TYPE]

_INSTRUCTIONS = {
    "MOVE": [_VAR, _SYMB],
    "CREATEFRAME": [],
    "PUSHFRAME": [],
    "POPFRAME": [],
    "DEFVAR": [_VAR],
    "CALL": [_LABEL],
    "RETURN": [],
    "PUSHS": [_SYMB],
    "POPS": [_VAR],
    "ADD": [_VAR, _SYMB, _SYMB],
    "SUB": [_VAR, _SYMB, _SYMB],
    "MUL": [_VAR, _SYMB, _SYMB],
    "IDIV": [_VAR, _SYMB, _SYMB],
    "LT": [_VAR, _SYMB, _SYMB],
    "GT": [_VAR, _SYMB, _SYMB],
    "EQ": [_VAR, _SYMB, _SYMB],
    "AND": [_VAR, _SYMB, _SYMB],
    "OR": [_VAR, _SYMB, _SYMB],
    "NOT": [_VAR, _SYMB, _SYMB],
    "INT2CHAR": [_VAR, _SYMB],
    "STRI2INT": [_VAR, _SYMB, _SYMB],
    "READ": [_VAR, _TYPE],
    "WRITE": [_SYMB],
    "CONCAT": [_VAR, _SYMB, _SYMB],
    "STRLEN": [_VAR, _SYMB],
    "GETCHAR": [_VAR, _SYMB, _SYMB],
    "SETCHAR": [_VAR, _SYMB, _SYMB],
    "TYPE": [_VAR, _SYMB],
    "LABEL": [_LABEL],
    "JUMP": [_LABEL],
    "JUMPIFEQ": [_LABEL, _SYMB, _SYMB],
    "JUMPIFNEQ": [_LABEL, _SYMB, _SYMB],
    "EXIT": [_SYMB],
    "DPRINT": [_SYMB],
    "BREAK": [],
}

class Arg:
    def __init__(self, token: Token) -> None:
        match token.type:
            case TokenType.LABEL \
                | TokenType.IDENT \
                | TokenType.NIL \
                | TokenType.BOOL \
                | TokenType.INT \
                | TokenType.STRING \
                | TokenType.TYPE:
                self.type = token.type
                self.value = token.value
            case _:
                raise ValueError(
                    "Invalid token type '" + str(token.type) + "'"
                )

    def write_xml(self, order: int, out: TextIO):
        type_str = ""
        match self.type:
            case TokenType.LABEL:
                type_str = "label"
            case TokenType.IDENT:
                type_str = "var"
            case TokenType.NIL:
                type_str = "nil"
            case TokenType.BOOL:
                type_str = "bool"
            case TokenType.STRING:
                type_str = "string"
            case TokenType.TYPE:
                type_str = "type"
            case _:
                raise ValueError(
                    "Invalid argumen type '" + str(self.type) + "'"
                )

        out.write(f'<arg{order} type="{type_str}">{self.value}</arg{order}>')

class Instruction:
    def __init__(self, name: str, args: list[Arg]) -> None:
        self.opcode = name.upper()
        self.args = args

    def validate(self) -> Union[tuple[Error, str], None]:
        shape = _INSTRUCTIONS[self.opcode]
        if len(shape) != len(self.args):
            return (
                Error.PARSE,
                "Invalid number of arguments for instruciton '"
                    + self.opcode
                    + "'"
            )

        for (have, expect) in zip(self.args, shape):
            if expect[0] == TokenType.TYPE and have.type == TokenType.LABEL:
                have.type = TokenType.LABEL
                continue
            if have.type not in expect:
                return (
                    Error.PARSE,
                    "Invalid arguments to '" + self.opcode + "'",
                )

        return None

    def write_xml(self, order: int, out: TextIO):
        out.write(f'<instruction order="{order}" opcode="{self.opcode}">')

        for (idx, arg) in enumerate(self.args):
            arg.write_xml(idx + 1, out)

        out.write('</instruction>')

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        self.cur = Token(TokenType.NEWLINE)
        self.err_code = Error.NONE
        self.err_msg = ""

    def parse(self) -> list[Instruction]:
        # skip all whitespaces at the start of the file
        while self.cur.type == TokenType.NEWLINE:
            self._next_tok()

        # check the language header
        if self.cur.type != TokenType.DIRECTIVE \
            or self.cur.value != ".IPPcode24":
            self._error("Invalid code header", Error.IVALID_HEADER)
            return []

        # there is bug in pylance, this will outsmart it so that it doesn't
        # show wrong warning
        self.cur = self._next_tok()
        # ensure there is whitespace after the language header
        if self.cur.type != TokenType.NEWLINE:
            self._error("Expected newline after code header.");
            return []

        # skip all whitespaces before code starts
        self._next_tok()
        while self.cur.type == TokenType.NEWLINE:
            self._next_tok()

        res: list[Instruction] = []

        while self.cur.type != TokenType.EOF and self.err_code == Error.NONE:
            if self.cur.type == TokenType.DIRECTIVE:
                self._error("Unexpected token DIRECTIVE")
                return []

            i = self._parse_instruction();
            if not i:
                return []

            res.append(i)
            while self.cur.type == TokenType.NEWLINE:
                self._next_tok()

        return res

    def _parse_instruction(self) -> Union[Instruction, None]:
        inst = self.cur
        if inst.type != TokenType.LABEL:
            return self._error("Expected instruciton name")

        args: list[Arg] = []
        self._next_tok()
        while self.cur.type != TokenType.EOF \
            and self.cur.type != TokenType.ERR \
            and self.cur.type != TokenType.NEWLINE \
            and self.cur.type != TokenType.DIRECTIVE:
            args.append(Arg(self.cur))
            self._next_tok()

        res = Instruction(inst.value, args)
        err = res.validate()
        if err:
            self.err_code = err[0]
            self.err_msg = err[1]
            return None

        return res

    def _next_tok(self) -> Token:
        self.cur = self.lexer.next()
        if self.cur.type == TokenType.ERR:
            self._error(self.cur.value)
        return self.cur

    def _error(self, msg: str, code: Error = Error.PARSE) -> None:
        if self.err_code == Error.NONE:
            self.err_code = code
            self.err_msg = msg
        return None

