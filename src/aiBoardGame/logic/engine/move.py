"""Piece movement history on board"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type, TypeVar, Optional

from aiBoardGame.logic.engine.auxiliary import Position, BoardEntity, Board


Piece = TypeVar("Piece")


@dataclass(frozen=True)
class InvalidMove(Exception):
    """Exception for invalid move on board"""
    piece: Type[Piece]
    start: Position
    end: Position
    message: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.piece.__name__} cannot move from {*self.start,} to {*self.end,}" if self.message is None else self.message


@dataclass(frozen=True)
class MoveRecord:
    """Class for storing movement on board"""
    start: Position
    end: Position
    movedPieceEntity: BoardEntity
    capturedPieceEntity: Optional[BoardEntity]

    @classmethod
    def make(cls, board: Board, start: Position, end: Position) -> MoveRecord:
        """Create move easily

        :param board: Board the move was made one
        :type board: Board
        :param start: Move's start position
        :type start: Position
        :param end: Move's end position
        :type end: Position
        :return: Created move record
        :rtype: MoveRecord
        """
        return MoveRecord(
            start=start,
            end=end,
            movedPieceEntity=board[start],
            capturedPieceEntity=board[end]
        )
        