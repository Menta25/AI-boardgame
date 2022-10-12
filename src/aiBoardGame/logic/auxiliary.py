from __future__ import annotations
from decimal import InvalidOperation

from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict, NamedTuple, Optional, Type, TypeVar, Union, Tuple


Piece = TypeVar("Piece")


class Side(IntEnum):
    Black = -1
    Red = 1

    @property
    def opponent(self) -> Side:
        return Side(-self)

    def __str__(self) -> str:
        return super().__str__().split(".")[-1]


class Position(NamedTuple):
    file: int
    rank: int


class BoardEntity(NamedTuple):
    side: Side
    piece: Type[Piece]


class SideState(Dict[Position, Type[Piece]]):
    def __getitem__(self, key: Union[Position, Tuple[int, int]]) -> Optional[Type[Piece]]:
        if isinstance(key, tuple):
            key = Position(*key)
        if isinstance(key, (Position, tuple)):
            return self.get(key)
        else:
            raise TypeError(f"Key has invalid type {key.__class__.__name__}")

    def __setitem__(self, key: Union[Position, Tuple[int, int]], value: Union[Optional[Type[Piece]], BoardEntity]) -> None:
        if isinstance(key, tuple):
            key = Position(*key)
        if isinstance(value, BoardEntity):
            raise InvalidOperation(f"Cannot assign {value.__class__.__name__} to {self.__class__.__name__} because object is not {value.side.__class__.__name__} aware")
        return super().__setitem__(key, value)


@dataclass
class Board(Dict[Side, SideState]):
    fileBounds: ClassVar[Tuple[int, int]] = (0, 9)
    rankBounds: ClassVar[Tuple[int, int]] = (0, 10)

    fileLength: ClassVar[int] = sum(fileBounds)
    rankLength: ClassVar[int] = sum(rankBounds)

    def __init__(self) -> None:
        self.update({side: SideState() for side in Side})

    def __getitem__(self, key: Union[Position, Tuple[int, int], Side]) -> Union[Optional[BoardEntity], SideState]:
        if isinstance(key, Side):
            return super().__getitem__(key)
        elif isinstance(key, (Position, tuple)):
            for side, sideState in self.items():
                if sideState[key] is not None:
                    return BoardEntity(side, sideState[key])
            return None
        else:
            raise TypeError(f"Key has invalid type {key.__class__.__name__}")

    def __setitem__(self, key: Union[Position, Tuple[int, int]], value: Optional[BoardEntity]) -> None:
        if isinstance(key, (Position, tuple)) and (isinstance(value, BoardEntity) or value is None):
            if value is None:
                for sideState in self.values():
                    if key in sideState:
                        del sideState[key]
            else:
                self[value.side][key] = value.piece
                if key in self[value.side.opponent]:
                    del self[value.side.opponent][key]
        else:
            raise InvalidOperation(f"Cannot set {value.__class__.__name__} to {self.__class__.__name__}'")


# from enum import Enum
# from dataclasses import dataclass
# from typing import Generic, NamedTuple, Type, TypeVar, List, Optional

# SideType = TypeVar("SideType", bound=Enum)
# PieceType = TypeVar("PieceType")


# class BoardEntity(NamedTuple, Generic[SideType, PieceType]):
#     side: SideType
#     piece: Type[PieceType]


# @dataclass(init=False)
# class Board(Generic[SideType, PieceType]):
#     _data: List[List[Optional[BoardEntity]]]

#     def __init__(self, fileCount: int, rankCount: int) -> None:
#         if fileCount <= 0 or rankCount <= 0:
#             raise ValueError(f"File and rank count must be greater than 0, got {fileCount} and {rankCount}")
#         self._data = [[None for _ in range(rankCount)] for _ in range(fileCount)]

#     @property
#     def data(self) -> List[List[Optional[BoardEntity]]]:
#         return self._data

#     @property
#     def fileCount(self) -> int:
#         return len(self._data)

#     @property
#     def rankCount(self) -> int:
#         return len(self._data[0])

#     def __getitem__(self, key: int) -> List[Optional[BoardEntity]]:
#         return self._data[key]
