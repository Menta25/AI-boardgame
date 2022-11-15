from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple
from itertools import product, starmap

from aiBoardGame.logic.engine.pieces import Piece
from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side


NEW_FILE_LENGTH = 3
NEW_RANK_LENGTH = 3

FILE_MARGIN = (Piece.fileLength() - NEW_FILE_LENGTH) // 2


@dataclass(init=False)
class Advisor(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (Piece.fileBounds[0] + FILE_MARGIN, Piece.fileBounds[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviations: ClassVar[Dict[str, str]] = {
        "base": "A",
        "fen": "A"
    }


    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(start.file - end.file, start.rank - end.rank)
        return abs(delta.file) == 1 and abs(delta.rank) == 1  # NOTE: == isValidDelta

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        return [start + delta for delta in starmap(Delta, product((-1,1), repeat=2)) if cls.isPositionInBounds(side, start + delta) and board[side][start + delta] is None]
