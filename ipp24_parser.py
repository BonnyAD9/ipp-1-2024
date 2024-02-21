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
        self.type = token.type
        self.value = token.value

    def write_xml(self, order: int, out: TextIO):
        # convert argument to xml element

        # the type needs tobe converted to string
        type_s = ""
        match self.type:
            case TokenType.LABEL:
                type_s = "label"
            case TokenType.IDENT:
                type_s = "var"
            case TokenType.NIL:
                type_s = "nil"
            case TokenType.BOOL:
                type_s = "bool"
            case TokenType.INT:
                type_s = "int"
            case TokenType.STRING:
                type_s = "string"
            case TokenType.TYPE:
                type_s = "type"
            case _:
                raise ValueError("Invalid argumen type 'self.type'")

        # write the element
        out.write(
            f'        <arg{order} type="{type_s}">{self.value}</arg{order}>\n'
        )

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
        if shape is None:
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
        out.write(
            f'    <instruction order="{order}" opcode="{self.opcode}">\n'
        )

        # write the arguments
        for (idx, arg) in enumerate(self.args):
            arg.write_xml(idx + 1, out)

        # end the instruction tag
        out.write('    </instruction>\n')

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        # current token
        self.cur = []
        # first error code
        self.err_code = Error.NONE
        # first error message
        self.err_msg = ""

    def parse(self) -> list[Instruction]:
        self._next_tok();

        if self.cur[0].type != TokenType.DIRECTIVE or self.cur[0].value != ".IPPcode24":
            self._error("Invalid code header", Error.INVALID_HEADER)
            return []

        if len(self.cur) != 1:
            self._error("Expected newline after code header")
            return []

        self.cur = self._next_tok()
        res: list[Instruction] = []

        # read all the instructions
        while self.cur[0].type != TokenType.EOF and self.err_code == Error.NONE:
            i = self._parse_instruction()
            if not i:
                return []
            res.append(i)
            self._next_tok()

        return res

    def _parse_instruction(self) -> Union[Instruction, None]:
        inst = self.cur[0]
        # check correct token for opcode
        if inst.type != TokenType.LABEL:
            return self._error("Expected instruction name")

        args: list[Arg] = []

        for a in self.cur[1:]:
            arg = Parser._new_arg(a)
            if arg is None:
                return self._error("Invalid argument type")
            args.append(arg)

        inst = Instruction(inst.value, args)
        val = inst.validate()
        if val is not None:
            return self._error(val[1], val[0])
        return inst

    @staticmethod
    def _new_arg(token: Token) -> Union[Arg, None]:
        match token.type:
            case TokenType.LABEL \
                | TokenType.IDENT \
                | TokenType.NIL \
                | TokenType.BOOL \
                | TokenType.INT \
                | TokenType.STRING \
                | TokenType.TYPE:
                return Arg(token)
            case _:
                return None

    def _next_tok(self) -> list[Token]:
        self.cur = self.lexer.next()
        # Implicitly propagate lexer errors
        if self.cur[0].type == TokenType.ERR:
            self._error(self.cur[0].value)
        return self.cur

    def _error(self, msg: str, code: Error = Error.PARSE) -> None:
        # The first error is the most relevant, ensure that only it is saved.
        if self.err_code == Error.NONE:
            self.err_code = code
            self.err_msg = msg
