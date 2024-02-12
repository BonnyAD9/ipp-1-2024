#!/usr/bin/python3

from enum import Enum, auto
import sys
from typing import TextIO
from lexer import Lexer
from ipp24_parser import Instruction, Parser
from errors import Error

class Action(Enum):
    """Action based on CLI arguments."""

    HELP = auto()
    PARSE = auto()
    ERR = auto()

class Args:
    """Parsed CLI arguments"""

    def __init__(self, action: Action, value: str = ""):
        self.action = action
        self.value = value

def main(argv: list[str]) -> Error:
    args = parse_args(argv)
    match args.action:
        case Action.PARSE:
            return parse()
        case Action.HELP:
            help()
            return Error.NONE
        case Action.ERR:
            print("error:", args.value, file = sys.stderr)
            return Error.ARGS
    return Error.NONE

def parse_args(args: list[str]) -> Args:
    # simple parsing, there can be only 0 or 1 arguments
    match len(args):
        case 1:
            return Args(Action.PARSE)
        case 2:
            pass
        case _:
            return Args(Action.ERR, "Invalid number of arguments")

    # check if the single argument is valid
    match args[1]:
        case "--help" | "-h" | "-?":
            return Args(Action.HELP)
        case _:
            return Args(Action.ERR, "Invalid argument '" + args[1] + "'")

def parse(input: TextIO = sys.stdin, output: TextIO = sys.stdout) -> Error:
    """Parses IPPcode from `input` to xml into `output`"""

    # parse the input
    lexer = Lexer(input)
    parser = Parser(lexer)
    insts = parser.parse()

    # check for errors while parsing
    if parser.err_code != Error.NONE:
        print("error:", parser.err_msg, file = sys.stderr)
        return parser.err_code

    # generate xml into output
    make_xml(insts, output)

    return Error.NONE

def make_xml(insts: list[Instruction], out: TextIO):
    """Serializes the instructions into a xml output"""

    # The xml serialization is very simple and in this case using library to do
    # it wouldn't be much simpler

    # the xml header and program tag
    out.write(
        '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode24">'
    )

    # write instrucitons
    for (idx, inst) in enumerate(insts):
        inst.write_xml(idx + 1, out)

    # close the program tag
    out.write('</program>')

def help():
    """Prints help to stdout."""

    print(
"""Welcome in help for parser by BonnyAD9.

This script parses IPPcode24 into XML.

Usage:
  parse
    parses from stdin to stdout
  parse [options]

Options:
  -h  -?  --help
    prints this help
"""
    )
    pass

# ensure that this is executed as program
if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print("error:", e, file = sys.stderr)
        exit(Error.OTHER)
