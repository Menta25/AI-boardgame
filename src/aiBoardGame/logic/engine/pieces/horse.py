from dataclasses import dataclass
from typing import ClassVar, List
from itertools import product, chain, starmap

from aiBoardGame.logic.engine.pieces import Piece
from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side


@dataclass(init=False)
class Horse(Piece):
    baseAbbreviation: ClassVar[str] = "H"
    fenAbbreviation: ClassVar[str] = "N"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        isValidDelta = max(abs(delta.file), abs(delta.rank)) == 2 and min(abs(delta.file), abs(delta.rank)) == 1
        isPieceInTheWay = board[start + (delta/2).round()] is not None

        return isValidDelta and not isPieceInTheWay

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        for delta in starmap(Delta, chain(product((1,-1), (2,-2)), product((2,-2), (1,-1)))):
            toPosition = start + delta
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None and board[start + (delta/2).round()] is None:
                possibleToPositions.append(toPosition)
        return possibleToPositions
