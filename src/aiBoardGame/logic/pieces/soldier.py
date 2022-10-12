from dataclasses import dataclass
from typing import ClassVar, List

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


@dataclass(init=False)
class Soldier(Piece):
    abbreviation: ClassVar[str] = "S"

    @classmethod
    def _isValidMove(cls, _: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isOverRiver = fromRank >= (Piece.rankLength + 1) / 2
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
        possibleToPositions.append(Position(fromPosition.file, fromPosition.rank + side))
        isOverRiver = fromPosition.rank >= (Piece.rankLength + 1) / 2
        if isOverRiver:
            possibleToPositions.append(Position(fromPosition.file + 1, fromPosition.rank))
            possibleToPositions.append(Position(fromPosition.file - 1, fromPosition.rank))
        return possibleToPositions
