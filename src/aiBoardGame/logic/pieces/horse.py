from dataclasses import dataclass
from typing import ClassVar

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


@dataclass(init=False)
class Horse(Piece):
    abbreviation: ClassVar[str] = "H"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isValidDelta = max(abs(deltaFile), abs(deltaRank)) == 2 and min(abs(deltaFile), abs(deltaRank)) == 1
        isPieceInTheWay = board[fromFile + round(deltaFile / 2)][fromRank + round(deltaRank / 2)] is not None

        return isValidDelta and not isPieceInTheWay
