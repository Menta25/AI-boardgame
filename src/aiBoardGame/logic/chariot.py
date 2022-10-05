import numpy as np

from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.utils import BoardState, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Chariot(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def isValidMove(cls, boardState: BoardState[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank
        
        if deltaFile != 0 and deltaRank != 0:
            return False

        for side in Side:
            if deltaFile != 0:
                for rank in range(fromRank + np.sign(deltaFile), toRank, np.sign(deltaFile)):
                    if boardState[side][toFile][rank] is not None:
                        return False
            else:
                for file in range(fromFile + np.sign(deltaRank), toFile, np.sign(deltaRank)):
                    if boardState[side][file][toRank] is not None:
                        return False
        
        return True
