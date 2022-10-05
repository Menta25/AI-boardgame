from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, ClassVar

from aiBoardGame.logic.utils import BoardState, Side, FILE_BOUNDS, RANK_BOUNDS

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
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def isFileInBounds(cls, side: Side, file: int) -> bool:
        if side == Side.Black:
            file = cls.mirrorFile(file)
        return cls.fileBounds[0] <= file <= cls.fileBounds[1]

    @classmethod
    def isRankInBounds(cls, side: Side, rank: int) -> bool:
        if side == Side.Black:
            rank = cls.mirrorRank(rank)
        return cls.rankBounds[0] <= rank <= cls.rankBounds[1]

    @classmethod
    def isPositionInBounds(cls, side: Side, file: int, rank: int) -> bool:
        return cls.isFileInBounds(side, file) and cls.isRankInBounds(side, rank)

    @classmethod
    @abstractmethod
    def isValidMove(self, boardState: BoardState[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented isValidMove method")

    @classmethod
    def mirrorFile(cls, file: int) -> int:
        return sum(cls.rankBounds) - file

    @classmethod
    def mirrorRank(cls, rank: int) -> int:
        return sum(cls.fileBounds) - rank

    @classmethod
    def mirrorPosition(cls, file: int, rank: int) -> Tuple[int, int]:
        return cls.mirrorFile(file), cls.mirrorRank(rank)

    @classmethod
    def move(cls, boardState: BoardState[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> None:
        invalidMoveBaseParams = (cls.fileBounds, cls.rankBounds, toFile, toRank)
        if not cls.isPositionInBounds(side, toFile, toRank):
            raise InvalidMove(*invalidMoveBaseParams)
        elif fromFile == toFile and fromRank == toRank:
            raise InvalidMove(*invalidMoveBaseParams, f"{cls.__name__} is already at ({toFile}, {toRank}), cannot stay in one place")
        isPointOccupiedByAllyPiece = boardState[side][toFile][toRank] is not None
        if not cls.isValidMove(boardState, side, fromFile, fromRank, toFile, toRank) or isPointOccupiedByAllyPiece:
            raise InvalidMove(*invalidMoveBaseParams, f"{cls.__name__} cannot move from ({fromFile}, {fromRank}) to ({toFile}, {toRank})")

        if boardState[side.opponent][toFile][toRank] is not None:
            boardState[side.opponent][toFile][toRank] = None

        boardState[side][toFile][toRank] = boardState[side][fromFile][fromRank]
        boardState[side][fromFile][fromRank] = None
        print(f"from ({fromFile},{fromRank}) to ({toFile},{toRank})")
