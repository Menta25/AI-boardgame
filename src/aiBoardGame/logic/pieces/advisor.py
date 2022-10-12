from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


NEW_FILE_LENGTH = 3
NEW_RANK_LENGTH = 3

FILE_MARGIN = (Piece.fileLength() - NEW_FILE_LENGTH) // 2


@dataclass(init=False)
class Advisor(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (Piece.fileBounds[0] + FILE_MARGIN, Piece.fileBounds[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviation: ClassVar[str] = "A"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        return abs(deltaFile) == 1 and abs(deltaRank) == 1  # NOTE: == isValidDelta
