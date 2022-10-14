from __future__ import annotations
from decimal import InvalidOperation

from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict, NamedTuple, Optional, Type, TypeVar, Union, Tuple, overload


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

    def __eq__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return self.file == other[0] and self.rank == other[1]

    def __add__(self, other: Union[Position, Tuple[int, int]]) -> Position:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return Position(self.file + other[0], self.rank + other[1])

    def __sub__(self, other: Union[Position, Tuple[int, int]]) -> Position:
        if not isinstance(other, (Position, tuple)):
            raise TypeError("Other object must be Position or tuple")
        return Position(self.file - other[0], self.rank - other[1])

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
        return self > other or self == other


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
            raise InvalidOperation(f"Cannot set {value.__class__.__name__} to {self.__class__.__name__}'")

    @classmethod
    def isInBounds(cls, position: Position) -> bool:
        return (cls.fileBounds[0], cls.rankBounds[0]) <= position < (cls.fileBounds[1], cls.rankBounds[1])
