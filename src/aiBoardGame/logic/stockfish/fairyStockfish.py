from enum import Enum, auto, unique
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List, Tuple, ClassVar, Optional
from time import sleep

from aiBoardGame.logic.engine import Position


_BINARY_PATH = Path("src/aiBoardGame/logic/stockfish/fairy-stockfish-largeboard_x86-64")


@unique
class Difficulty(Enum):
    Easy = auto(),
    Medium = auto(),
    Hard = auto()


#  TODO: Define valid arguments for difficulties
_GO_ARGS = {
    Difficulty.Easy: (10, 1000),
    Difficulty.Medium: (20, 2000),
    Difficulty.Hard: (40, 4000)
}


class FairyStockfish:
    baseBinaryPath: ClassVar[Path] = _BINARY_PATH

    def __init__(self, binaryPath: Path = _BINARY_PATH, difficulty: Difficulty = Difficulty.Medium) -> None:
        self._process = Popen(
            args=[binaryPath.as_posix()],
            stdin=PIPE, stdout=PIPE,
            universal_newlines=True
        )
        self._initGameInterface()
        self.difficulty = difficulty
        self._currentFen = None

    @property
    def currentFen(self) -> str:
        return self._currentFen

    def __del__(self) -> None:
        self._process.terminate()

    def _write(self, input: str) -> None:
        self._process.stdin.write(f"{input}\n")
        self._process.stdin.flush()

    def _read(self) -> str:
        return self._process.stdout.readline().strip()

    def _communicate(self, input: List[str], wait: int = 0) -> List[str]:
        self._write(" ".join(input))
        sleep(wait/1000)
        self._write("isready")
        out = []
        while (line := self._read()) != "readyok":
            out.append(line)
        return out 

    def _initGameInterface(self) -> None:
        self._communicate(["ucci"])

    def position(self, fen: str) -> None:
        self._communicate(["position", "fen", fen])
        self._currentFen = fen

    def go(self) -> str:
        depth, movetime = _GO_ARGS[self.difficulty]
        out = self._communicate([
            "go",
            "depth", str(depth),
            "movetime", str(movetime)
        ], wait=movetime+10)
        if len(out) == 0:
            raise RuntimeError("An error occurred during calculating next move")
        return out[-1].split(" ")[1]

    def nextMove(self, fen: str) -> Optional[Tuple[Position, Position]]:
        self.position(fen)
        go = self.go()
        return self._algebraicMoveToPositions(go) if go != "(none)" else None

    @staticmethod
    def _algebraicMoveToPositions(algebraicMove: str) -> Tuple[Position, Position]:
        start = Position(
            file=ord(algebraicMove[0]) - ord("a"),
            rank=int(algebraicMove[1])
        )
        end = Position(
            file=ord(algebraicMove[2]) - ord("a"),
            rank=int(algebraicMove[3])
        )
        return start, end


if __name__ == "__main__":
    stockfishPath = Path("/home/Menta/Workspace/Projects/AI-boardgame/src/aiBoardGame/logic/stockfish/fairy-stockfish-largeboard_x86-64")
    stockfish = FairyStockfish(binaryPath=stockfishPath, difficulty=Difficulty.Medium)
    ret = stockfish.nextMove("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")
    print(ret)
    ret = stockfish.nextMove("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1CN4C1/9/R1BAKABNR b - - 0 1")
    print(ret)
    