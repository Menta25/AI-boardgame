from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


FILE_BOUND_LENGTH = 3
RANK_BOUND_LENGTH = 3

FILE_MARGIN = (sum(FILE_BOUNDS) - FILE_BOUND_LENGTH) // 2


@dataclass(init=False)
class Advisor(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (FILE_BOUNDS[0] + FILE_MARGIN, FILE_BOUNDS[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (RANK_BOUNDS[0], RANK_BOUND_LENGTH)

    @classmethod
    def _isValidMove(cls, board: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        return abs(deltaFile) == 1 and abs(deltaRank) == 1  # NOTE: == isValidDelta
