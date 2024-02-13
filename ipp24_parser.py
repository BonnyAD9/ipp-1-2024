from typing import TextIO, Union
from lexer import Lexer, Token, TokenType
from errors import Error

# definitions to check the validity of instructions. This doesn't check the
# types of literals but it checks that the general token type is correct

# variable
_VAR = [TokenType.IDENT]
# any symbol with value
_SYMB = [
    TokenType.IDENT,
    TokenType.NIL,
    TokenType.BOOL,
    TokenType.INT,
    TokenType.STRING
]
# label
_LABEL = [TokenType.LABEL]
# type, this will match LABEL but it will be converted to TYPE
_TYPE = [TokenType.TYPE]

# define how the instructions should be used
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
    "NOT": [_VAR, _SYMB],
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
    """Represents argument to a instruction, it is subset of Token."""

    def __init__(self, token: Token) -> None:
        # check that the token as valid type. Throw if the type is incorrect
        # because that should never happen and it is a bug.
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
                raise ValueError(f"Invalid token type '{token.type}'")

    def write_xml(self, order: int, out: TextIO):
        # convert argument to xml element

        # the type needs tobe converted to string
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
            case TokenType.INT:
                type_str = "int"
            case TokenType.STRING:
                type_str = "string"
            case TokenType.TYPE:
                type_str = "type"
            case _:
                raise ValueError(f"Invalid argumen type 'self.type'")

        # write the element
        out.write(f'<arg{order} type="{type_str}">{self.value}</arg{order}>')

class Instruction:
    """Represents IPPcode24 instruction, that is its opcode and arguments"""

    def __init__(self, name: str, args: list[Arg]) -> None:
        self.opcode = name.upper()
        self.args = args

    def validate(self) -> Union[tuple[Error, str], None]:
        """
        Validates the instruction, checks if the opcode is known and if the
        arguments are correct.

            Returns:
                `None` if the arguments are correct, tuple of error code and
                error message if the arguments are incorrect.
        """

        shape = _INSTRUCTIONS.get(self.opcode)

        # check if the opcode is valid
        if shape == None:
            return (
                Error.INVALID_OPCODE,
                f"Unknown instruction '{self.opcode}'"
            )

        # check if the number of arguments is correct
        if len(shape) != len(self.args):
            return (
                Error.PARSE,
                f"Invalid number of arguments for instruction '{self.opcode}'"
            )

        # check if type of each of the arguments matches
        for (have, expect) in zip(self.args, shape):
            # convert LABEL to TYPE when appropriate. It is expected that if
            # argument can be type, the type is the first of the possible
            # values
            if expect[0] == TokenType.TYPE \
                and have.type == TokenType.LABEL \
                and have.value in ["nil", "bool", "int", "string"]:
                have.type = TokenType.TYPE
                continue
            if have.type not in expect:
                return (
                    Error.PARSE,
                    f"Invalid arguments to '{self.opcode}'",
                )

        return None

    def write_xml(self, order: int, out: TextIO):
        # start the instruction tag
        out.write(f'<instruction order="{order}" opcode="{self.opcode}">')

        # write the arguments
        for (idx, arg) in enumerate(self.args):
            arg.write_xml(idx + 1, out)

        # end the instruction tag
        out.write('</instruction>')

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        # current token
        self.cur = Token(TokenType.NEWLINE)
        # first error code
        self.err_code = Error.NONE
        # first error message
        self.err_msg = ""

    def parse(self) -> list[Instruction]:
        # skip all whitespaces at the start of the file
        while self.cur.type == TokenType.NEWLINE:
            self._next_tok()

        # check the language header
        if self.cur.type != TokenType.DIRECTIVE \
            or self.cur.value != ".IPPcode24":
            self._error("Invalid code header", Error.INVALID_HEADER)
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

        # read all the instructions

        res: list[Instruction] = []

        while self.cur.type != TokenType.EOF and self.err_code == Error.NONE:
            # DIRECTIVE can now never appear.
            if self.cur.type == TokenType.DIRECTIVE:
                self._error(
                    f"Unexpected token DIRECTIVE({self.cur.value})",
                    Error.INVALID_OPCODE
                )
                return []

            # parse the instruction
            i = self._parse_instruction();
            if not i:
                return []

            res.append(i)
            # skip all newlines
            while self.cur.type == TokenType.NEWLINE:
                self._next_tok()

        return res

    def _parse_instruction(self) -> Union[Instruction, None]:
        inst = self.cur
        # check correct token for opcode
        if inst.type != TokenType.LABEL:
            return self._error("Expected instruciton name")

        args: list[Arg] = []
        self._next_tok()
        # read arguments while there is valid argument token type
        while self.cur.type != TokenType.EOF \
            and self.cur.type != TokenType.ERR \
            and self.cur.type != TokenType.NEWLINE \
            and self.cur.type != TokenType.DIRECTIVE:
            args.append(Arg(self.cur))
            self._next_tok()

        # create the instruction and validate it
        res = Instruction(inst.value, args)
        err = res.validate()
        if err:
            self._error(err[1], err[0])
            return None

        return res

    def _next_tok(self) -> Token:
        self.cur = self.lexer.next()
        # Implicitly propagate lexer errors
        if self.cur.type == TokenType.ERR:
            self._error(self.cur.value)
        return self.cur

    def _error(self, msg: str, code: Error = Error.PARSE) -> None:
        # The first error is the most relevant, ensure that only it is saved.
        if self.err_code == Error.NONE:
            self.err_code = code
            self.err_msg = msg
        return None
