from enum import Enum, auto
from typing import TextIO
from ipp24_parser import Instruction
from lexer import Lexer

class StatType(Enum):
    # Number of instructions
    LOC = auto()
    # Number of comments
    COMMENTS = auto()
    # Number of labels
    LABELS = auto()
    # number of instructions that can jump
    JUMPS = auto()
    # number of jumps forward
    FWJUMPS = auto()
    # number of jumps backwards
    BACKJUMPS = auto()
    # number of jumps to nonexisting labels
    BADJUMPS = auto()
    # order instructions from most frequent to least
    FREQUENT = auto()
    # print the string
    PRINT = auto()
    # print newline
    EOL = auto()

class Stat:
    def __init__(self, type: StatType, value: str = "") -> None:
        self.type = type
        self.value = value

class Stats:
    def __init__(self, insts: list[Instruction], lexer: Lexer) -> None:
        self.insts = insts
        self.loc = str(len(insts)) + "\n"
        self.comments = str(lexer.comment_count) + "\n"
        self.examined = False
        self.labels = ""
        self.jumps = ""
        self.fwjumps = ""
        self.backjumps = ""
        self.badjumps = ""
        self.frequent = ""

    def print_stats(self, stats: list[Stat], out: TextIO):
        for s in stats:
            out.write(self._get_value(s))

    def _get_value(self, stat: Stat) -> str:
        match stat.type:
            case StatType.LOC:
                return self.loc
            case StatType.COMMENTS:
                return self.comments
            case StatType.PRINT:
                return stat.value + "\n"
            case StatType.EOL:
                return "\n\n"
            case _:
                if not self.examined:
                    self._examine()
                match stat.type:
                    case StatType.LABELS:
                        return self.labels
                    case StatType.JUMPS:
                        return self.jumps
                    case StatType.FWJUMPS:
                        return self.fwjumps
                    case StatType.BACKJUMPS:
                        return self.backjumps
                    case StatType.BADJUMPS:
                        return self.badjumps
                    case StatType.FREQUENT:
                        return self.frequent

    def _examine(self):
        labels = 0
        jumps = 0
        fwjumps = 0
        backjumps = 0
        badjumps = 0
        frequent = 0

        jump_cnts: dict[str, int] = {}
        freqs: dict[str, int] = dict()

        for inst in self.insts:
            if inst.opcode in freqs:
                freqs[inst.opcode] += 1
            else:
                freqs[inst.opcode] = 1

            match inst.opcode:
                case "LABEL":
                    labels += 1
                    name = inst.args[0].value
                    cnt = jump_cnts.get(name)
                    if cnt != None and cnt > 0:
                        fwjumps += cnt
                    jump_cnts[name] = -1
                case "CALL" | "JUMP" | "JUMPIFEQ" | "JUMPIFNEQ":
                    jumps += 1
                    name = inst.args[0].value
                    cnt = jump_cnts.get(name)
                    if cnt == None:
                        jump_cnts[name] = 1
                    elif cnt == -1:
                        backjumps += 1
                    else:
                        jump_cnts[name] = cnt + 1
                case "RETURN":
                    jumps += 1;
                case _:
                    pass
        # end of iteration of instructions

        for c in jump_cnts.values():
            if c > 0:
                badjumps += c

        frequent = ",".join(map(
            lambda i: i[0],
            sorted(freqs.items(), key=lambda i: i[1], reverse = True)
        ))

        self.labels = str(labels) + "\n"
        self.jumps = str(jumps) + "\n"
        self.fwjumps = str(fwjumps) + "\n"
        self.backjumps = str(backjumps) + "\n"
        self.badjumps = str(badjumps) + "\n"
        self.frequent = frequent + "\n"
        self.examined = True
