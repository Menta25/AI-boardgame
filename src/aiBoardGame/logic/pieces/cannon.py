import numpy as np

from dataclasses import dataclass
from typing import ClassVar

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


@dataclass(init=False)
class Cannon(Piece):
    abbreviation: ClassVar[str] = "C"

    @classmethod
    def _isValidMove(cls, board: Board, _: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        if deltaFile != 0 and deltaRank != 0:  # NOTE: == isOneDeltaOnly
            return False

        files = range(fromFile + np.sign(deltaFile), toFile, np.sign(deltaFile)) if deltaFile != 0 else [toFile] * (abs(deltaRank) - 1)
        ranks = range(fromRank + np.sign(deltaRank), toRank, np.sign(deltaRank)) if deltaRank != 0 else [toRank] * (abs(deltaFile) - 1)

        isCaptureMove = board[toFile][toRank] is not None
        piecesInTheWay = 0
        for file, rank in zip(files, ranks):
            if board[file][rank] is not None:
                piecesInTheWay += 1

        return isCaptureMove and piecesInTheWay == 1 or not isCaptureMove and piecesInTheWay == 0
