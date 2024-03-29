"""Module for the elephant piece"""

from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple
from itertools import product, starmap

from aiBoardGame.logic.engine.pieces import Piece
from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side


NEW_RANK_LENGTH = Piece.rankLength() // 2


@dataclass(init=False)
class Elephant(Piece):
    """Elephant piece class"""
    fileBounds: ClassVar[Tuple[int, int]] = Piece.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviations: ClassVar[Dict[str, str]] = {
        "base": "E",
        "fen": "B"
    }


    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        isValidDelta = abs(delta.file) == 2 and abs(delta.rank) == 2
        isPieceInTheWay = board[start + (delta/2).round()] is not None

        return isValidDelta and not isPieceInTheWay


    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side, start: Position) -> List[Position]:
        possibleToPositions = []
        for delta in starmap(Delta, product((-2,2), repeat=2)):
            toPosition = start + delta
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None and board[start + (delta/2).round()] is None:
                possibleToPositions.append(toPosition)
        return possibleToPositions
