from enum import Enum, auto
from typing import Iterator, Union
from errors import Error
from statp import Stat, StatType

class Action(Enum):
    """Action based on CLI arguments."""

    HELP = auto()
    PARSE = auto()
    ERR = auto()

class StatFile:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.stats: list[Stat] = []

class Args:
    """CLI parser"""

    def __init__(self, args: Iterator[str]) -> None:
        self.action = Action.PARSE
        self.err_code = Error.NONE
        self.err_msg = ""
        self.stats: list[StatFile] = []
        self.cur: Union[str, None] = None
        self.args = args

    def parse(self) -> None:
        """Parses the arguments"""

        # skip the first argument
        self._next()

        self._next()
        while self.cur is not None:
            match self.cur:
                case "-h" | "-?" | "--help":
                    if self.action != Action.PARSE:
                        return self._error("Cannot set action multiple times")
                    self.action = Action.HELP
                case "--loc":
                    self._add_stat(Stat(StatType.LOC))
                case "--comments":
                    self._add_stat(Stat(StatType.COMMENTS))
                case "--labels":
                    self._add_stat(Stat(StatType.LABELS))
                case "--jumps":
                    self._add_stat(Stat(StatType.JUMPS))
                case "--fwjumps":
                    self._add_stat(Stat(StatType.FWJUMPS))
                case "--backjumps":
                    self._add_stat(Stat(StatType.BACKJUMPS))
                case "--badjumps":
                    self._add_stat(Stat(StatType.BADJUMPS))
                case "--frequent":
                    self._add_stat(Stat(StatType.FREQUENT))
                case "--eol":
                    self._add_stat(Stat(StatType.EOL))
                case _:
                    if self.cur.startswith("--stats="):
                        spl = self.cur.split("=", 1)
                        self._add_stats(spl[1])
                    elif self.cur.startswith("--print="):
                        spl = self.cur.split("=", 1)
                        self._add_stat(Stat(StatType.PRINT, spl[1]))
                    else:
                        return self._error(f"Unknown argument '{self.cur}'")
            self._next()

    def _add_stat(self, stat: Stat) -> None:
        # check if there is any --stats file to associate this stat with
        if len(self.stats) == 0:
            self._error("Cannot use '" + str(self.cur) + "' before --stats")
            return
        self.stats[-1].stats.append(stat)

    def _add_stats(self, filename: str) -> None:
        # check if the file is unique
        for s in self.stats:
            if s.filename == filename:
                self._error(
                    f"Cannot output twice to the same file '{filename}'",
                    Error.FILE_WRITE
                )
                return
        self.stats.append(StatFile(filename))

    def _next(self) -> Union[str, None]:
        self.cur = next(self.args, None)
        return self.cur

    def _error(self, msg: str, code: Error = Error.ARGS) -> None:
        # save only the first error
        if self.err_code == Error.NONE:
            self.err_msg = msg
            self.err_code = code
            self.action = Action.ERR

def parse_args(args: list[str]) -> Args:
    """Parses the CLI arguments"""
    it = iter(args)
    res = Args(it)
    res.parse()
    return res
