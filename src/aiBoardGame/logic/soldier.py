from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Soldier(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def _isValidMove(cls, _: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
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
