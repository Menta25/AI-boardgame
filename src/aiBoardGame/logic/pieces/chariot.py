import numpy as np

from dataclasses import dataclass
from typing import ClassVar, List
from itertools import chain, product, starmap

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Delta, Position, Side


@dataclass(init=False)
class Chariot(Piece):
    abbreviation: ClassVar[str] = "R"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        if delta.file != 0 and delta.rank != 0:  # NOTE: == isOneDeltaOnly
            return False

        files = range(start.file + np.sign(delta.file), end.file, np.sign(delta.file)) if delta.file != 0 else [end.file] * (abs(delta.rank) - 1)
        ranks = range(start.rank + np.sign(delta.rank), end.rank, np.sign(delta.rank)) if delta.rank != 0 else [end.rank] * (abs(delta.file) - 1)

        for file, rank in zip(files, ranks):  # NOTE: == isPieceInTheWay
            if board[file, rank] is not None:
                return False

        return True

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        for delta in starmap(Delta, chain(product((1,-1), (0,)), product((0,), (1,-1)))):
            toPosition = start
            while cls.isPositionInBounds(side, toPosition := toPosition + delta):
                if board[toPosition] is None:
                    possibleToPositions.append(toPosition)
                elif board[toPosition] is not None:
                    if board[toPosition].side == side.opponent:
                        possibleToPositions.append(toPosition)
                    break
        return possibleToPositions