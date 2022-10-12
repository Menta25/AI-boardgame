from dataclasses import dataclass
from typing import ClassVar, List, Tuple
from itertools import product

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


NEW_RANK_LENGTH = Piece.rankLength() // 2


@dataclass(init=False)
class Elephant(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = Piece.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviation: ClassVar[str] = "E"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        deltaFile = toPosition.file - fromPosition.file
        deltaRank = toPosition.rank - fromPosition.rank

        isValidDelta = abs(deltaFile) == 2 and abs(deltaRank) == 2
        isPieceInTheWay = board[fromPosition + (round(deltaFile/2), round(deltaRank/2))] is not None

        return isValidDelta and not isPieceInTheWay


    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side, fromPosition: Position) -> List[Position]:
        possibleToPositions = []
        for deltaFile, deltaRank in product((-2,2), repeat=2):
            toPosition = fromPosition + (deltaFile, deltaRank)
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None and board[fromPosition + (round(deltaFile/2), round(deltaRank/2))] is None:
                possibleToPositions.append(toPosition)
        return possibleToPositions
