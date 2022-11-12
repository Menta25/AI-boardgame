import numpy as np

from dataclasses import dataclass
from typing import ClassVar, List, Tuple
from itertools import chain, product, starmap

from aiBoardGame.logic.engine.pieces import Piece
from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side


NEW_FILE_LENGTH = 3
NEW_RANK_LENGTH = 3

FILE_MARGIN = (Piece.fileLength() - NEW_FILE_LENGTH) // 2


@dataclass(init=False)
class General(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (Piece.fileBounds[0] + FILE_MARGIN, Piece.fileBounds[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    baseAbbreviation: ClassVar[str] = "G"
    fenAbbreviation: ClassVar[str] = "K"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        delta = Delta(end.file - start.file, end.rank - start.rank)

        isOneDeltaOnly = not (delta.file != 0 and delta.rank != 0)
        isValidDelta = abs(delta.file) == 1 or abs(delta.rank) == 1

        if isOneDeltaOnly and isValidDelta:
            return True
        elif isOneDeltaOnly and abs(delta.rank) > 1 and board[end].piece == General:  # NOTE: Flying general
            for rank in range(start.rank + np.sign(delta.rank), end.rank, np.sign(delta.rank)):
                if board[end.file, rank] is not None:   
                    return False
            return True
        else:
            return False

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  start: Position) -> List[Position]:
        possibleToPositions = []
        for delta in starmap(Delta, chain(product((1,-1), (0,)), product((0,), (1,-1)))):
            toPosition = start + delta
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None:
                possibleToPositions.append(toPosition)
        delta = Delta(0, side)
        toPosition = start
        while cls.isPositionInBounds(side, toPosition := toPosition + delta):
            if board[toPosition] is not None:
                if board[side.opponent][toPosition] == General:
                    possibleToPositions.append(toPosition)
                else:
                    break
        return possibleToPositions