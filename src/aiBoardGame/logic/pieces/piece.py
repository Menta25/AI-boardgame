from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, ClassVar

from aiBoardGame.logic.auxiliary import Board, Position, Side
from aiBoardGame.logic.move import Move


@dataclass(init=False)
class Piece(ABC):
    fileBounds: ClassVar[Tuple[int, int]] = Board.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = Board.rankBounds

    abbreviation: ClassVar[str] = "X"

    @classmethod
    def fileLength(cls) -> int:
        return sum(cls.fileBounds)

    @classmethod
    def rankLength(cls) -> int:
        return sum(cls.rankBounds)

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
    def isPositionInBounds(cls, side: Side, position: Position) -> bool:
        return cls.isFileInBounds(side, position.file) and cls.isRankInBounds(side, position.rank)

    @classmethod
    @abstractmethod
    def _getPossibleMoves(cls, board: Board, side: Side, fromPosition: Position) -> List[Position]:
        raise NotImplementedError(f"{cls.__class__.__name__} has not implemented getPossibleMoves method")

    @classmethod
    def getPossibleMoves(cls, board: Board, fromPosition: Position) -> List[Move]:
        side, _ = board[fromPosition]
        return [Move.make(board, fromPosition, toPosition) for toPosition in cls._getPossibleMoves(board, side, fromPosition)]

    @classmethod
    @abstractmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        raise NotImplementedError(f"{cls.__class__.__name__} has not implemented isValidMove method")

    @classmethod
    def isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        isFromAndToTheSame = fromPosition.file == toPosition.file and fromPosition.rank == toPosition.rank
        if not cls.isPositionInBounds(side, toPosition) or not cls.isPositionInBounds(side, fromPosition) or isFromAndToTheSame or board[side][fromPosition] is None or board[side][fromPosition] != cls:
            return False
        isPointOccupiedByAllyPiece = board[side][toPosition] is not None
        if isPointOccupiedByAllyPiece or not cls._isValidMove(board, side, fromPosition, toPosition):
            return False
        return True

    @staticmethod
    def mirrorFile(file: int) -> int:
        return sum(Board.fileBounds) - file - 1

    @staticmethod
    def mirrorRank(rank: int) -> int:
        return sum(Board.rankBounds) - rank - 1

    @classmethod
    def mirrorPosition(cls, file: int, rank: int) -> Tuple[int, int]:
        return cls.mirrorFile(file), cls.mirrorRank(rank)
