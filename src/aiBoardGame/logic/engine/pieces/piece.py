from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple, ClassVar

from aiBoardGame.logic.engine.auxiliary import Board, Position, Side


@dataclass(init=False)
class Piece(ABC):
    fileBounds: ClassVar[Tuple[int, int]] = Board.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = Board.rankBounds

    abbreviations: ClassVar[Dict[str, str]] = {
        "base": "X",
        "fen": "X"
    }


    @classmethod
    def name(cls) -> str:
        return cls.__name__

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
    def _getPossibleMoves(cls, board: Board, side: Side, start: Position) -> List[Position]:
        raise NotImplementedError(f"{cls.__name__} has not implemented getPossibleMoves method")

    @classmethod
    def getPossibleMoves(cls, board: Board, start: Position) -> List[Position]:
        side, _ = board[start]
        return [endPosition for endPosition in cls._getPossibleMoves(board, side, start)]

    @classmethod
    @abstractmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        raise NotImplementedError(f"{cls.__class__.__name__} has not implemented isValidMove method")

    @classmethod
    def isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        return cls.isPositionInBounds(side, end) and cls.isPositionInBounds(side, start) and \
               board[side][start] is not None and board[side][start] == cls and \
               end != start and board[side][end] is None and \
               cls._isValidMove(board, side, start, end)

    @staticmethod
    def mirrorFile(file: int) -> int:
        return Board.fileCount - file - 1

    @staticmethod
    def mirrorRank(rank: int) -> int:
        return Board.rankCount - rank - 1

    @staticmethod
    def mirrorPosition(position: Position) -> Position:
        return Position(Piece.mirrorFile(position.file), Piece.mirrorRank(position.rank))
