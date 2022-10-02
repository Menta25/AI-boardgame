from dataclasses import dataclass
from typing import ClassVar
from enum import IntEnum

from aiBoardGame.logic.soldier import Soldier

FILE_BOUNDS = (0, 8)
RANK_BOUNDS = (0, 9)


class Side(IntEnum):
    Black = -1
    Red = 1


@dataclass
class Xiangqi:
    fileCount: ClassVar[int] = sum(FILE_BOUNDS) + 1
    rankCount: ClassVar[int] = sum(RANK_BOUNDS) + 1

    soldier: Soldier = Soldier(5, 5)
    