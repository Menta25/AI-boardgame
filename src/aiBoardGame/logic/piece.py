from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, ClassVar

from aiBoardGame.logic.utils import Board, Side, FILE_BOUNDS, RANK_BOUNDS


@dataclass(init=False)
class Piece(ABC):
    fileBounds: ClassVar[Tuple[int, int]] = FILE_BOUNDS
    rankBounds: ClassVar[Tuple[int, int]] = RANK_BOUNDS

    @classmethod
    def isFileInBounds(cls, side: Side, file: int) -> bool:
        if side == Side.Black:
            file = cls.mirrorFile(file)
        return cls.fileBounds[0] <= file < cls.fileBounds[1]

    @classmethod
    def isRankInBounds(cls, side: Side, rank: int) -> bool:
        if side == Side.Black:
            rank = cls.mirrorRank(rank)
        return cls.rankBounds[0] <= rank < cls.rankBounds[1]

    @classmethod
    def isPositionInBounds(cls, side: Side, file: int, rank: int) -> bool:
        return cls.isFileInBounds(side, file) and cls.isRankInBounds(side, rank)

    @classmethod
    @abstractmethod
    def isValidMove(self, board: Board[Side, Piece], side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented isValidMove method")

    @staticmethod
    def mirrorFile(file: int) -> int:
        return sum(FILE_BOUNDS) - file - 1

    @staticmethod
    def mirrorRank(rank: int) -> int:
        return sum(RANK_BOUNDS) - rank - 1

    @classmethod
    def mirrorPosition(cls, file: int, rank: int) -> Tuple[int, int]:
        return cls.mirrorFile(file), cls.mirrorRank(rank)
