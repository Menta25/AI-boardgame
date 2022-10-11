from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Horse(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def _isValidMove(cls, board: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isValidDelta = max(abs(deltaFile), abs(deltaRank)) == 2 and min(abs(deltaFile), abs(deltaRank)) == 1
        isPieceInTheWay = board[fromFile + round(deltaFile / 2)][fromRank + round(deltaRank / 2)] is not None

        return isValidDelta and not isPieceInTheWay
