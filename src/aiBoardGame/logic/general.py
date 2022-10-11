from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


FILE_BOUND_LENGTH = 3
RANK_BOUND_LENGTH = 3

FILE_MARGIN = (sum(FILE_BOUNDS) - FILE_BOUND_LENGTH) // 2


@dataclass(init=False)
class General(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (FILE_BOUNDS[0] + FILE_MARGIN, FILE_BOUNDS[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (RANK_BOUNDS[0], RANK_BOUND_LENGTH)

    @classmethod
    def _isValidMove(cls, board: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isOneDeltaOnly = not (deltaFile != 0 and deltaRank != 0)
        isValidDelta = abs(deltaFile) == 1 or abs(deltaRank) == 1

        return isOneDeltaOnly and isValidDelta
