from __future__ import annotations

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Generic, Type, TypeVar, List, Optional, Dict


FILE_BOUNDS = (0, 8)
RANK_BOUNDS = (0, 9)


class Side(IntEnum):
    Black = -1
    Red = 1

    @property
    def opponent(self) -> Side:
        return Side(-self)


PieceType = TypeVar("PieceType")
SideType = TypeVar("SideType", bound=Enum)


@dataclass(init=False)
class Board(Generic[PieceType]):
    _data: List[List[Optional[PieceType]]]

    def __init__(self, fileCount: int, rankCount: int) -> None:
        if fileCount <= 0 or rankCount <= 0:
            raise ValueError(f"File and rank count must be greater than 0, got {fileCount} and {rankCount}")
        self._data = [[None for _ in range(rankCount)] for _ in range(fileCount)]

    @property
    def data(self) -> List[List[Optional[PieceType]]]:
        return self._data

    @property
    def fileCount(self) -> int:
        return len(self._data)

    @property
    def rankCount(self) -> int:
        return len(self._data[0])

    def __getitem__(self, key: int) -> List[Optional[PieceType]]:
        return self._data[key]

@dataclass(init=False)
class BoardState(Generic[SideType, PieceType]):
    _sideBoards: Dict[SideType, Board[PieceType]]

    def __init__(self, fileCount: int, rankCount: int, sides: Type[SideType]) -> None:
        self._sideBoards = {side: Board(fileCount, rankCount) for side in sides}

    def __getitem__(self, key: SideType) -> Board[PieceType]:
        return self._sideBoards[key]

    @property
    def fileCount(self) -> int:
        return next(iter(self._sideBoards.values())).fileCount

    @property
    def rankCount(self) -> int:
        return next(iter(self._sideBoards.values())).rankCount
