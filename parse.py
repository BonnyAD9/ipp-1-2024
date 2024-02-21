#!/usr/bin/python3

import sys
from typing import TextIO
from lexer import Lexer
from ipp24_parser import Instruction, Parser
from errors import Error
from args import Action, Args, parse_args
from statp import Stats

def main(argv: list[str]) -> Error:
    args = parse_args(argv)
    match args.action:
        case Action.PARSE:
            return parse(args, sys.stdin)
            # return parse(args, open("testfile.IPPcode24", encoding = "utf-8"))
        case Action.HELP:
            print_help()
            return Error.NONE
        case Action.ERR:
            print("error:", args.err_msg, file = sys.stderr)
            return args.err_code
    return Error.NONE

def parse(
    args: Args,
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout
) -> Error:
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

    # print the stats
    stats = Stats(insts, lexer)
    for s in args.stats:
        try:
            f = open(s.filename, "w")
        except Exception as e:
            print("error: failed to open file:", e, file = sys.stderr)
            return Error.FILE_WRITE

        with f:
            stats.print_stats(s.stats, f)

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

def print_help():
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

  --stats=<filename>
    Outputs the stats to the given file. This must appear before any other
    stats parameters.

  --loc
    stat - number of instructions

  --comments
    stat - number of lines with comments on them

  --labels
    stat - number of labels

  --jumps
    stat - number of jumps

  --fwjumps
    stat - number of jumps forward

  --backjumps
    stat - number of jumps backwards

  --badjumps
    stat - number of jumps to nonexisting label

  --prints=<text>
    stat - prints the given text

  --eol
    stat - empty line
"""
    )

# ensure that this is executed as program
if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print("error:", e, file = sys.stderr)
        sys.exit(Error.OTHER)
