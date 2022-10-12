import numpy as np

from dataclasses import dataclass
from typing import ClassVar, List
from itertools import chain, product

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


@dataclass(init=False)
class Cannon(Piece):
    abbreviation: ClassVar[str] = "C"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        deltaFile = toPosition.file - fromPosition.file
        deltaRank = toPosition.rank - fromPosition.rank

        if deltaFile != 0 and deltaRank != 0:  # NOTE: == isOneDeltaOnly
            return False

        files = range(fromPosition.file + np.sign(deltaFile), toPosition.file, np.sign(deltaFile)) if deltaFile != 0 else [toPosition.file] * (abs(deltaRank) - 1)
        ranks = range(fromPosition.rank + np.sign(deltaRank), toPosition.rank, np.sign(deltaRank)) if deltaRank != 0 else [toPosition.rank] * (abs(deltaFile) - 1)

        isCaptureMove = board[toPosition] is not None
        piecesInTheWay = 0
        for position in zip(files, ranks):
            if board[position] is not None:
                piecesInTheWay += 1

        return isCaptureMove and piecesInTheWay == 1 or not isCaptureMove and piecesInTheWay == 0

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  fromPosition: Position) -> List[Position]:
        possibleToPositions = []
        for deltaFile, deltaRank in chain(product((1,-1), (0,)), product((0,), (1,-1))):
            toPosition = fromPosition + (deltaFile, deltaRank)
            hasFoundPiece = False
            while cls.isPositionInBounds(toPosition):
                if not hasFoundPiece and board[toPosition] is None:
                    possibleToPositions.append(toPosition)
                elif board[toPosition] is not None:
                    if hasFoundPiece:
                        if board[toPosition].side == side.opponent:
                            possibleToPositions.append(toPosition)
                        break
                    else:
                        hasFoundPiece = True
                toPosition += (deltaFile, deltaRank)
        return possibleToPositions