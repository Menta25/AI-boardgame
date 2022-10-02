from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, ClassVar

from aiBoardGame.logic.xiangqi import Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(frozen=True)
class InvalidPosition(Exception):
    fileBounds: Tuple[int, int]
    rankBounds: Tuple[int, int]
    file: int
    rank: int

    def __str__(self) -> str:
        return f"File and rank values must be between [{self.fileBounds[0]}, {self.fileBounds[1]}] and [{self.rankBounds[0]}, {self.rankBounds[1]}], {self.file} and {self.rank} were given"

@dataclass(frozen=True)
class InvalidMove(InvalidPosition):
    message: Optional[str] = None

    def __str__(self) -> str:
        return super().__str__() if self.message is None else self.message


@dataclass(init=False)
class Piece(ABC):
    _file: int
    _rank: int
    _side: Side

    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    def __init__(self, file: int, rank: int) -> None:
        if not self.isPositionInBounds(file, rank):
            raise InvalidPosition(self.fileBounds, self.rankBounds, file, rank)

        super().__init__()
        self._file = file
        self._rank = rank
        self._side = Side.Black if file >= (sum(RANK_BOUNDS) + 1) / 2 else Side.Red

    @classmethod
    def isFileInBounds(cls, file: int) -> bool:
        return cls.fileBounds[0] <= file <= cls.fileBounds[1]

    @classmethod
    def isRankInBounds(cls, rank: int) -> bool:
        return cls.rankBounds[0] <= rank <= cls.rankBounds[1]

    @classmethod
    def isPositionInBounds(cls, file: int, rank: int) -> bool:
        return cls.isFileInBounds(file) and cls.isRankInBounds(rank)

    @property
    def file(self) -> int:
        return self._file

    @property
    def rank(self) -> int:
        return self._rank

    @property
    def side(self) -> Side:
        return self._side

    @abstractmethod
    def isValidMove(self, file: int, rank: int) -> bool:
        return self.isPositionInBounds(file, rank)

    def move(self, file: int, rank: int) -> None:
        if not self.isValidMove(file, rank):
            raise InvalidMove(self.fileBounds, self.rankBounds, file, rank)
        self._file = file
        self._rank = rank
