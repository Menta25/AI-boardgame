from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import BoardState, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Soldier(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def isValidMove(cls, _: BoardState[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank
        
        isOverRiver = fromRank >= (sum(cls.rankBounds) + 1) / 2
        if side == Side.Black:
            deltaRank *= -1
            isOverRiver = not isOverRiver

        isValidForwardMove = deltaRank == 1
        isValidSidewaysMove = isOverRiver and abs(deltaFile) == 1
        
        return isValidForwardMove ^ isValidSidewaysMove
