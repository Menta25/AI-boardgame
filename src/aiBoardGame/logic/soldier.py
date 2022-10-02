from dataclasses import dataclass
from typing import ClassVar, Tuple

from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.xiangqi import FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Soldier(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    def isValidMove(self, file: int, rank: int) -> bool:
        return super().isValidMove(file, rank)