from dataclasses import dataclass
from typing import ClassVar, List

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Delta, Position, Side


@dataclass(init=False)
class Soldier(Piece):
    abbreviation: ClassVar[str] = "S"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        isOverRiver = start.rank >= (Piece.rankLength + 1) / 2
        if side == Side.Black:
            deltaRank *= -1
            isOverRiver = not isOverRiver

        isOneDeltaOnly = not (delta.file != 0 and delta.rank != 0)
        isValidDeltaRank = deltaRank == 1
        isValidDeltaFile = isOverRiver and abs(delta.file) == 1

        return isOneDeltaOnly and isValidDeltaRank or isValidDeltaFile

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        possibleToPositions.append(start + Delta(0, side))
        isOverRiver = start.rank >= (Piece.rankLength + 1) / 2
        if isOverRiver:
            possibleToPositions.append(start + Delta(1, 0))
            possibleToPositions.append(start + Delta(-1, 0))
        return [possibleToPosition for possibleToPosition in possibleToPositions if cls.isPositionInBounds(side, possibleToPosition) and board[side][possibleToPosition] is None]
