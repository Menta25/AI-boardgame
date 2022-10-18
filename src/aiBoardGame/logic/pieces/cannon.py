import numpy as np

from dataclasses import dataclass
from typing import ClassVar, List
from itertools import chain, product, starmap

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Delta, Position, Side


@dataclass(init=False)
class Cannon(Piece):
    abbreviation: ClassVar[str] = "C"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        if delta.file != 0 and delta.rank != 0:  # NOTE: == isOneDeltaOnly
            return False

        files = range(start.file + np.sign(delta.file), end.file, np.sign(delta.file)) if delta.file != 0 else [end.file] * (abs(delta.rank) - 1)
        ranks = range(start.rank + np.sign(delta.rank), end.rank, np.sign(delta.rank)) if delta.rank != 0 else [end.rank] * (abs(delta.file) - 1)

        isCaptureMove = board[end] is not None
        piecesInTheWay = 0
        for position in zip(files, ranks):
            if board[position] is not None:
                piecesInTheWay += 1

        return isCaptureMove and piecesInTheWay == 1 or not isCaptureMove and piecesInTheWay == 0

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        for delta in starmap(Delta, chain(product((1,-1), (0,)), product((0,), (1,-1)))):
            toPosition = start + delta
            hasFoundPiece = False
            while cls.isPositionInBounds(side, toPosition):
                if not hasFoundPiece and board[toPosition] is None:
                    possibleToPositions.append(toPosition)
                elif board[toPosition] is not None:
                    if hasFoundPiece:
                        if board[toPosition].side == side.opponent:
                            possibleToPositions.append(toPosition)
                        break
                    else:
                        hasFoundPiece = True
                toPosition += delta
        return possibleToPositions