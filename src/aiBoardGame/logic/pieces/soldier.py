from dataclasses import dataclass
from typing import ClassVar, List

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


@dataclass(init=False)
class Soldier(Piece):
    abbreviation: ClassVar[str] = "S"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        deltaFile = toPosition.file - fromPosition.file
        deltaRank = toPosition.rank - fromPosition.rank

        isOverRiver = fromPosition.rank >= (Piece.rankLength + 1) / 2
        if side == Side.Black:
            deltaRank *= -1
            isOverRiver = not isOverRiver

        isOneDeltaOnly = not (deltaFile != 0 and deltaRank != 0)
        isValidDeltaRank = deltaRank == 1
        isValidDeltaFile = isOverRiver and abs(deltaFile) == 1

        return isOneDeltaOnly and isValidDeltaRank or isValidDeltaFile

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  fromPosition: Position) -> List[Position]:
        possibleToPositions = []
        possibleToPositions.append(fromPosition + (0, side))
        isOverRiver = fromPosition.rank >= (Piece.rankLength + 1) / 2
        if isOverRiver:
            possibleToPositions.append(fromPosition + (1, 0))
            possibleToPositions.append(fromPosition + (-1, 0))
        return [possibleToPosition for possibleToPosition in possibleToPositions if cls.isPositionInBounds(side, possibleToPosition) and board[side][possibleToPosition] is None]
