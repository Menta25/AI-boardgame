from __future__ import annotations

from math import sqrt
from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict, Generator, NamedTuple, Optional, Type, TypeVar, Union, Tuple, overload


Piece = TypeVar("Piece")


class Side(IntEnum):
    Black = -1
    Red = 1

    @property
    def opponent(self) -> Side:
        return Side(-self)


class Delta(NamedTuple):
    file: Union[int, float]
    rank: Union[int, float]

    def normalize(self) -> Delta:
        length = abs(self)
        return Delta(self.file/length, self.rank/length)

    def round(self) -> Delta:
        return Delta(round(self.file), round(self.rank))

    def __add__(self, other: Union[Delta, Tuple[int, int]]) -> Delta:
        if not isinstance(other, (Delta, tuple)):
            raise TypeError("Other object must be Delta or tuple")
        return Delta(self.file + other[0], self.rank + other[1])

    def __sub__(self, other: Union[Delta, Tuple[int, int]]) -> Delta:
        if not isinstance(other, (Delta, tuple)):
            raise TypeError("Other object must be Delta or tuple")
        return Delta(self.file - other[0], self.rank - other[1])

    def __mul__(self, other: Union[int, float]) -> Delta:
        if not isinstance(other, (int, float)):
            raise TypeError("Other object must be int or float")
        return Delta(self.file*other, self.rank*other)

    def __truediv__(self, other: Union[int, float]) -> Delta:
        if not isinstance(other, (int, float)):
            raise TypeError("Other object must be int or float")
        return Delta(self.file/other, self.rank/other)

    def __abs__(self) -> float:
        return sqrt(self.file**2 + self.rank**2)

class Position(NamedTuple):
    file: int
    rank: int

    def __add__(self, other: Union[Delta, Tuple[int, int]]) -> Position:
        if not isinstance(other, (Delta, tuple)):
            raise TypeError("Other object must be Delta or tuple")
        if isinstance(other, Delta):
            other = other.round()
        return Position(self.file + other[0], self.rank + other[1])

    @overload
    def __sub__(self, other: Position) -> Delta:
        ...

    @overload
    def __sub__(self, other: Union[Delta, Tuple[int, int]]) -> Position:
        ...

    def __sub__(self, other: Union[Position, Delta, Tuple[int, int]]) -> Union[Delta, Position]:
        if not isinstance(other, (Position, Delta, tuple)):
            raise TypeError("Other object must be Position, Delta or tuple")
        if isinstance(other, Position):
            return Delta(self.file - other.file, self.rank - other.rank)
        elif isinstance(other, Delta):
            other = other.round()
        return Position(self.file - other[0], self.rank - other[1])

    def __eq__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file == other[0] and self.rank == other[1]

    def __gt__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file > other[0] and self.rank > other[1]

    def __lt__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file < other[0] and self.rank < other[1]

    def __ge__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file >= other[0] and self.rank >= other[1]

    def __le__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file <= other[0] and self.rank <= other[1]


    def isBetween(self, first: Position, second: Position) -> bool:
        return first <= self <= second or first >= self >= second


class BoardEntity(NamedTuple):
    side: Side
    piece: Type[Piece]

    def __str__(self) -> str:
        return f"{self.side.name}{self.piece.name()}"


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
            raise TypeError(f"Cannot assign {value.__class__.__name__} to {self.__class__.__name__} because object is not {value.side.__class__.__name__} aware")
        return super().__setitem__(key, value)


@dataclass
class Board(Dict[Side, SideState]):
    fileBounds: ClassVar[Tuple[int, int]] = (0, 9)
    rankBounds: ClassVar[Tuple[int, int]] = (0, 10)

    fileCount: ClassVar[int] = sum(fileBounds)
    rankCount: ClassVar[int] = sum(rankBounds)

    def __init__(self) -> None:
        self.update({side: SideState() for side in Side})

    @overload
    def __getitem__(self, key: Union[Position, Tuple[int, int]]) -> Optional[BoardEntity]:
        ...

    @overload
    def __getitem__(self, key: Side) -> SideState:
        ...

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
            raise TypeError(f"Cannot set {value.__class__.__name__} to {self.__class__.__name__}'")

    @classmethod
    def isInBounds(cls, position: Position) -> bool:
        return (cls.fileBounds[0], cls.rankBounds[0]) <= position < (cls.fileBounds[1], cls.rankBounds[1])
        
    def pieces(self) -> Generator[Tuple[Position, BoardEntity], None, None]:
        for side, sideState in self.items():
            for position, piece in sideState.items():
                yield position, BoardEntity(side, piece)
                