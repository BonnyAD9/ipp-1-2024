import sys
from typing import TextIO
from lexer import Lexer
from ipp24_parser import Instruction, Parser


def main(args: list[str]) -> int:
    lexer = Lexer(open("testfile.IPPcode24"))
    parser = Parser(lexer)
    insts = parser.parse()

    if parser.err_code != 0:
        print("error:", parser.err_msg, file=sys.stderr)
        return parser.err_code

    make_xml(insts)

    return 0

def make_xml(insts: list[Instruction], out: TextIO = sys.stdout):
    out.write(
        '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode24">'
    )

    for (idx, inst) in enumerate(insts):
        inst.write_xml(idx + 1, out)

    out.write('</program>')


if __name__ == "__main__":
    sys.exit(main(sys.argv))
