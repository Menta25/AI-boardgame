import numpy as np

from dataclasses import dataclass
from typing import ClassVar

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Side


@dataclass(init=False)
class Chariot(Piece):
    abbreviation: ClassVar[str] = "R"

    @classmethod
    def _isValidMove(cls, board: Board, _: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        if deltaFile != 0 and deltaRank != 0:  # NOTE: == isOneDeltaOnly
            return False

        files = range(fromFile + np.sign(deltaFile), toFile, np.sign(deltaFile)) if deltaFile != 0 else [toFile] * (abs(deltaRank) - 1)
        ranks = range(fromRank + np.sign(deltaRank), toRank, np.sign(deltaRank)) if deltaRank != 0 else [toRank] * (abs(deltaFile) - 1)

        for file, rank in zip(files, ranks):  # NOTE: == isPieceInTheWay
            if board[file, rank] is not None:
                return False

        return True
