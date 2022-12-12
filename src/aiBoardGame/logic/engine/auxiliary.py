from __future__ import annotations

from math import sqrt
from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict, List, NamedTuple, Optional, Type, TypeVar, Union, Tuple, overload


Piece = TypeVar("Piece")


class Side(IntEnum):
    Black = -1
    Red = 1

    @property
    def opponent(self) -> Side:
        return Side(-self)

    @property
    def FEN(self) -> str:
        return "w" if self == Side.Red else "b"

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
            raise TypeError(f"Other object must be Delta or tuple, was {type(other)}")
        return Delta(self.file + other[0], self.rank + other[1])

    def __sub__(self, other: Union[Delta, Tuple[int, int]]) -> Delta:
        if not isinstance(other, (Delta, tuple)):
            raise TypeError(f"Other object must be Delta or tuple, was {type(other)}")
        return Delta(self.file - other[0], self.rank - other[1])

    def __mul__(self, other: Union[int, float]) -> Delta:
        if not isinstance(other, (int, float)):
            raise TypeError(f"Other object must be int or float, was {type(other)}")
        return Delta(self.file*other, self.rank*other)

    def __truediv__(self, other: Union[int, float]) -> Delta:
        if not isinstance(other, (int, float)):
            raise TypeError(f"Other object must be int or float, was {type(other)}")
        return Delta(self.file/other, self.rank/other)

    def __abs__(self) -> float:
        return sqrt(self.file**2 + self.rank**2)

class Position(NamedTuple):
    file: int
    rank: int

    def __add__(self, other: Union[Delta, Tuple[int, int]]) -> Position:
        if not isinstance(other, (Delta, tuple)):
            raise TypeError(f"Other object must be Delta or tuple, was {type(other)}")
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
            raise TypeError(f"Other object must be Position, Delta or tuple, was {type(other)}")
        if isinstance(other, Position):
            return Delta(self.file - other.file, self.rank - other.rank)
        elif isinstance(other, Delta):
            other = other.round()
        return Position(self.file - other[0], self.rank - other[1])

    def __eq__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError(f"Other object must be Position or tuple, was {type(other)}")
        return self.file == other[0] and self.rank == other[1]

    def __gt__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError(f"Other object must be Position or tuple, was {type(other)}")
        return self.file > other[0] and self.rank > other[1]

    def __lt__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError(f"Other object must be Position or tuple, was {type(other)}")
        return self.file < other[0] and self.rank < other[1]

    def __ge__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError(f"Other object must be Position or tuple, was {type(other)}")
        return self.file >= other[0] and self.rank >= other[1]

    def __le__(self, other: Union[Position, Tuple[int, int]]) -> bool:
        if not isinstance(other, (Position, tuple)):
            raise TypeError(f"Other object must be Position or tuple, was {type(other)}")
        return self.file <= other[0] and self.rank <= other[1]


    def isBetween(self, first: Position, second: Position) -> bool:
        return first <= self <= second or first >= self >= second


class BoardEntity(NamedTuple):
    side: Side
    piece: Type[Piece]

    @property
    def FEN(self) -> str:
        caseFunction = str.upper if self.side == Side.Red else str.lower
        return caseFunction(self.piece.abbreviations["fen"])

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

    def __setitem__(self, key: Union[Position, Tuple[int, int]], value: Optional[Union[Type[Piece], BoardEntity]]) -> None:
        if isinstance(key, tuple):
            key = Position(*key)
        if isinstance(value, BoardEntity):
            raise TypeError(f"Cannot assign {value.__class__.__name__} to {self.__class__.__name__} because object is not {value.side.__class__.__name__} aware")
        elif value is None:
            if key in self:
                del self[key]
        else:
            return super().__setitem__(key, value)


@dataclass
class Board(Dict[Side, SideState]):
    fileBounds: ClassVar[Tuple[int, int]] = (0, 9)
    rankBounds: ClassVar[Tuple[int, int]] = (0, 10)

    fileCount: ClassVar[int] = sum(fileBounds)
    rankCount: ClassVar[int] = sum(rankBounds)

    def __init__(self) -> None:
        self.update({side: SideState() for side in Side})

    @classmethod
    def isInBounds(cls, position: Position) -> bool:
        return (cls.fileBounds[0], cls.rankBounds[0]) <= position < (cls.fileBounds[1], cls.rankBounds[1])

    @property
    def pieces(self) -> List[Tuple[Position, BoardEntity]]:
        allPieces = ((position, BoardEntity(side, piece)) for side, sideState in self.items() for position, piece in sideState.items())
        return sorted(allPieces, key=lambda item: (*item[0],))

    @property
    def FEN(self) -> str:
        fen = ""
        for rank in range(self.rankCount-1, -1, -1):
            emptyCount = 0
            for file in range(self.fileCount):
                boardEntity = self[file, rank]
                if boardEntity is None:
                    emptyCount += 1
                else:
                    if emptyCount != 0:
                        fen += str(emptyCount)
                        emptyCount = 0
                    fen += boardEntity.FEN
            if emptyCount != 0:
                fen += str(emptyCount)
            fen += "/"
        return fen[:-1]

    @overload
    def __getitem__(self, key: Union[Position, Tuple[int, int]]) -> Optional[BoardEntity]:
        ...

    @overload
    def __getitem__(self, key: Side) -> SideState:
        ...

    def __getitem__(self, key: Union[Position, Tuple[int, int], Side]) -> Optional[Union[BoardEntity, SideState]]:
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
        if isinstance(key, (Position, tuple)):
            if isinstance(value, BoardEntity):
                self[value.side][key] = value.piece
                self[value.side.opponent][key] = None
            elif value is None:
                for sideState in self.values():
                    sideState[key] = None
            else:
                raise TypeError(f"Invalid value type, must be BoardEntity or None, was {type(value)}")
        else:
            raise TypeError(f"Invalid key type, must be Positon or Tuple[int, int] was {type(key)}")
