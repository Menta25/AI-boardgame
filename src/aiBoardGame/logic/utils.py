from __future__ import annotations

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Generic, NamedTuple, Type, TypeVar, List, Optional, Dict


FILE_BOUNDS = (0, 9)
RANK_BOUNDS = (0, 10)


class Side(IntEnum):
    Black = -1
    Red = 1

    @property
    def opponent(self) -> Side:
        return Side(-self)

    def __str__(self) -> str:
        return "B" if self == self.Black else "R"


PieceType = TypeVar("PieceType")
SideType = TypeVar("SideType", bound=Enum)


class BoardEntity(NamedTuple, Generic[SideType, PieceType]):
    side: SideType
    piece: Type[PieceType]

@dataclass(init=False)
class Board(Generic[SideType, PieceType]):
    _data: List[List[Optional[BoardEntity[SideType, PieceType]]]]

    def __init__(self, fileCount: int, rankCount: int) -> None:
        if fileCount <= 0 or rankCount <= 0:
            raise ValueError(f"File and rank count must be greater than 0, got {fileCount} and {rankCount}")
        self._data = [[None for _ in range(rankCount)] for _ in range(fileCount)]

    @property
    def data(self) -> List[List[Optional[BoardEntity[SideType, PieceType]]]]:
        return self._data

    @property
    def fileCount(self) -> int:
        return len(self._data)

    @property
    def rankCount(self) -> int:
        return len(self._data[0])

    def __getitem__(self, key: int) -> List[Optional[BoardEntity[SideType, PieceType]]]:
        return self._data[key]

    def __str__(self) -> str:
        boardStr = ""
        for rank in range(self.rankCount - 1, -1, -1):
            for file in range(self.fileCount):
                boardStr += str(self[file][rank].side) if self[file][rank] != None else "0"
                boardStr += " "
            boardStr += "\n"
        return boardStr
