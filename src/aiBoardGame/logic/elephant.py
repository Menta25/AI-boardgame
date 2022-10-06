from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


RANK_BOUND_LENGTH = sum(RANK_BOUNDS) // 2


@dataclass(init=False)
class Elephant(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = (RANK_BOUNDS[0], RANK_BOUND_LENGTH)

    @classmethod
    def isValidMove(cls, board: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank
        
        isValidDelta = abs(deltaFile) == 2 and abs(deltaRank) == 2
        isPieceInTheWay = board[fromFile + round(deltaFile / 2)][fromRank + round(deltaRank / 2)] is not None

        return isValidDelta and not isPieceInTheWay
