"""Module for various auxiliary class"""

from __future__ import annotations

from math import sqrt
from enum import IntEnum
from dataclasses import dataclass
from typing import ClassVar, Dict, List, NamedTuple, Optional, Type, TypeVar, Union, Tuple, overload


Piece = TypeVar("Piece")


class Side(IntEnum):
    """Enum class for board sides"""
    BLACK = -1
    RED = 1

    @property
    def opponent(self) -> Side:
        """Get opponent side"""
        return Side(-self)

    @property
    def fen(self) -> str:
        """Get side's FEN"""
        return "w" if self == Side.RED else "b"

class Delta(NamedTuple):
    """Class for indicating movement direction and distance"""
    file: Union[int, float]
    rank: Union[int, float]

    def normalize(self) -> Delta:
        """Normalize movement vector

        :return: Normalized delta
        :rtype: Delta
        """
        length = abs(self)
        return Delta(self.file/length, self.rank/length)

    def round(self) -> Delta:
        """Round movement vector

        :return: Rounded delta
        :rtype: Delta
        """
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
    """Class for storing positions on board"""
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
        """Check if position is between two other positions

        :param first: First position
        :type first: Position
        :param second: Second position
        :type second: Position
        :return: Is position between the other two
        :rtype: bool
        """
        return first <= self <= second or first >= self >= second


class BoardEntity(NamedTuple):
    """Class for storing pieces on board"""
    side: Side
    piece: Type[Piece]

    @property
    def fen(self) -> str:
        """Get piece's FEN

        :return: Piece's FEN
        :rtype: str
        """
        caseFunction = str.upper if self.side == Side.RED else str.lower
        return caseFunction(self.piece.abbreviations["fen"])

    def __str__(self) -> str:
        return f"{self.side.name}{self.piece.name()}"


class SideState(Dict[Position, Type[Piece]]):
    """Helper class for storing a side's pieces on board"""
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


@dataclass(init=False)
class Board(Dict[Side, SideState]):
    """Class for tracking gameboard state"""
    fileBounds: ClassVar[Tuple[int, int]] = (0, 9)
    """File bounds that pieces operate in"""
    rankBounds: ClassVar[Tuple[int, int]] = (0, 10)
    """Rank bounds that pieces operate in"""

    fileCount: ClassVar[int] = sum(fileBounds)
    """File bound length"""
    rankCount: ClassVar[int] = sum(rankBounds)
    """Rank bound length"""

    def __init__(self) -> None:
        self.update({side: SideState() for side in Side})

    @classmethod
    def isInBounds(cls, position: Position) -> bool:
        """Checks if position is in operation bounds

        :param position: Position
        :type position: Position
        :return: Given position is in or not in bounds
        :rtype: bool
        """
        return (cls.fileBounds[0], cls.rankBounds[0]) <= position < (cls.fileBounds[1], cls.rankBounds[1])

    @property
    def pieces(self) -> List[Tuple[Position, BoardEntity]]:
        """Pieces on board"""
        allPieces = ((position, BoardEntity(side, piece)) for side, sideState in self.items() for position, piece in sideState.items())
        return sorted(allPieces, key=lambda item: (*item[0],))

    @property
    def fen(self) -> str:
        """Board's FEN"""
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
                    fen += boardEntity.fen
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
