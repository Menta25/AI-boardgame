from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


NEW_RANK_LENGTH = Piece.rankLength() // 2


@dataclass(init=False)
class Elephant(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = Piece.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviation: ClassVar[str] = "E"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isValidDelta = abs(deltaFile) == 2 and abs(deltaRank) == 2
        isPieceInTheWay = board[fromFile + round(deltaFile / 2)][fromRank + round(deltaRank / 2)] is not None

        return isValidDelta and not isPieceInTheWay
