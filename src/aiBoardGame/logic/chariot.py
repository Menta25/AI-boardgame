import numpy as np

from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Chariot(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def isValidMove(cls, board: Board[Side, Piece], _: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank
        
        if deltaFile != 0 and deltaRank != 0:
            return False

        files = range(fromFile + np.sign(deltaFile), toFile, np.sign(deltaFile)) if deltaFile != 0 else [toFile] * (abs(deltaRank) - 1)
        ranks = range(fromRank + np.sign(deltaRank), toRank, np.sign(deltaRank)) if deltaRank != 0 else [toRank] * (abs(deltaFile) - 1)

        for file, rank in zip(files, ranks):
            if board[file][rank] is not None:
                return False
        
        return True
