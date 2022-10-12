from dataclasses import dataclass
from typing import ClassVar, List
from itertools import product, chain

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


@dataclass(init=False)
class Horse(Piece):
    abbreviation: ClassVar[str] = "H"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        deltaFile = toPosition.file - fromPosition.file
        deltaRank = toPosition.rank - fromPosition.rank

        isValidDelta = max(abs(deltaFile), abs(deltaRank)) == 2 and min(abs(deltaFile), abs(deltaRank)) == 1
        isPieceInTheWay = board[fromPosition + (round(deltaFile/2), round(deltaRank/2))] is not None

        return isValidDelta and not isPieceInTheWay

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  fromPosition: Position) -> List[Position]:
        possibleToPositions = []
        for deltaFile, deltaRank in chain(product((1,-1), (2,-2)), product((2,-2), (1,-1))):
            toPosition = fromPosition + (deltaFile, deltaRank)
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None and board[fromPosition + (round(deltaFile/2), round(deltaRank/2))] is None:
                possibleToPositions.append(toPosition)
        return possibleToPositions
