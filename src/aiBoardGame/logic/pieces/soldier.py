from dataclasses import dataclass
from typing import ClassVar, List

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Delta, Position, Side


_RIVER_RANK = (Piece.rankLength() + 1) / 2


@dataclass(init=False)
class Soldier(Piece):
    baseAbbreviation: ClassVar[str] = "S"
    fenAbbreviation: ClassVar[str] = "P"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        isOverRiver = start.rank >= (Piece.rankLength() + 1) / 2
        if side == Side.Black:
            delta = Delta(delta.file, -1*delta.rank)
            isOverRiver = not isOverRiver

        isOneDeltaOnly = not (delta.file != 0 and delta.rank != 0)
        isValidDeltaRank = delta.rank == 1
        isValidDeltaFile = isOverRiver and abs(delta.file) == 1

        return isOneDeltaOnly and isValidDeltaRank or isValidDeltaFile



    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        possibleToPositions.append(start + Delta(0, side))
        isOverRiver = start.rank >= _RIVER_RANK if side == Side.Red else start.rank < _RIVER_RANK
        if isOverRiver:
            possibleToPositions.append(start + Delta(1, 0))
            possibleToPositions.append(start + Delta(-1, 0))
        return [possibleToPosition for possibleToPosition in possibleToPositions if cls.isPositionInBounds(side, possibleToPosition) and board[side][possibleToPosition] is None]
