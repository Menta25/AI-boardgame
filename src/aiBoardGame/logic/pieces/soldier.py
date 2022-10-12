from dataclasses import dataclass
from typing import ClassVar

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


@dataclass(init=False)
class Soldier(Piece):
    abbreviation: ClassVar[str] = "S"

    @classmethod
    def _isValidMove(cls, _: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isOverRiver = fromRank >= (sum(cls.rankBounds) + 1) / 2
        if side == Side.Black:
            deltaRank *= -1
            isOverRiver = not isOverRiver

        isOneDeltaOnly = not (deltaFile != 0 and deltaRank != 0)
        isValidDeltaRank = deltaRank == 1
        isValidDeltaFile = isOverRiver and abs(deltaFile) == 1

        return isOneDeltaOnly and isValidDeltaRank or isValidDeltaFile
