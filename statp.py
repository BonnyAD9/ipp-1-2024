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
        # comments were already ignored, we must ask the lexer about them
        self.comments = str(lexer.comment_count) + "\n"
        # true if the stats are calculated
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
                return "\n"
            case _:
                # calculate the stats lazily only once
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

        # info about usages of labels:
        #   None       - this is the first sight of the label
        #   positive n - the label has been jumped to n times, but haven't been
        #                defined yet (jump forward / bad jump)
        #   -1         - label has been already defined (jump backwards)
        jump_cnts: dict[str, int] = {}
        # histogram of opcodes
        freqs: dict[str, int] = {}

        for inst in self.insts:
            # add the opcode to histogram
            if inst.opcode in freqs:
                freqs[inst.opcode] += 1
            else:
                freqs[inst.opcode] = 1

            match inst.opcode:
                # definition of label found, all encouters of that label so far
                # are jumps forward
                case "LABEL":
                    labels += 1
                    name = inst.args[0].value
                    cnt = jump_cnts.get(name)
                    if cnt != None and cnt > 0:
                        fwjumps += cnt
                    jump_cnts[name] = -1
                # jump where we can determine the direction of it
                case "CALL" | "JUMP" | "JUMPIFEQ" | "JUMPIFNEQ":
                    jumps += 1
                    name = inst.args[0].value
                    cnt = jump_cnts.get(name)
                    # first encounter - jump forward / bad jump
                    if cnt == None:
                        jump_cnts[name] = 1
                    # label has already been encountered - jump backward
                    elif cnt == -1:
                        backjumps += 1
                    # jump forward / bad jumps
                    else:
                        jump_cnts[name] = cnt + 1
                # return is also jump, but the direction is not defined
                case "RETURN":
                    jumps += 1;
                case _:
                    pass
        # end of iteration of instructions

        # all jumps to nonexisting labels are bad jumps
        for c in jump_cnts.values():
            if c > 0:
                badjumps += c

        # order the instruction opcodes based on their frequency
        frequent = ",".join(map(
            lambda i: i[0],
            sorted(freqs.items(), key = lambda i: i[1], reverse = True)
        ))

        # store the data
        self.labels = str(labels) + "\n"
        self.jumps = str(jumps) + "\n"
        self.fwjumps = str(fwjumps) + "\n"
        self.backjumps = str(backjumps) + "\n"
        self.badjumps = str(badjumps) + "\n"
        self.frequent = frequent + "\n"
        # data is now loaded, don't load it again
        self.examined = True
