from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from aiBoardGame.logic.auxiliary import Board, BoardEntity, Position


Piece = TypeVar("Piece")


@dataclass(frozen=True)
class InvalidMove(Exception):
    piece: Type[Piece]
    start: Position
    end: Position
    message: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.piece.__name__} cannot move from {*self.start,} to {*self.end,}" if self.message is None else self.message


@dataclass(frozen=True)
class MoveRecord:
    start: Position
    end: Position
    movedPieceEntity: BoardEntity
    capturedPieceEntity: Optional[BoardEntity]

    @classmethod
    def make(cls, board: Board, start: Position, end: Position) -> MoveRecord:
        return MoveRecord(
            start=start,
            end=end,
            movedPieceEntity=board[start],
            capturedPieceEntity=board[end]
        )