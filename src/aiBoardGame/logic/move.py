from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type, TypeVar, NamedTuple

from aiBoardGame.logic.auxiliary import Board, BoardEntity, Position


Piece = TypeVar("Piece")


@dataclass(frozen=True)
class InvalidMove(Exception):
    piece: Type[Piece]
    move: Move
    message: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.piece.__name__} cannot move from {*self.move.start,} to {*self.move.end,}" if self.message is None else self.message


class Move(NamedTuple):
    start: Position
    end: Position


@dataclass(frozen=True)
class MoveRecord:
    move: Move
    movedPieceEntity: BoardEntity
    capturedPieceEntity: Optional[BoardEntity]

    @classmethod
    def make(cls, board: Board, start: Position, end: Position) -> MoveRecord:
        return MoveRecord(
            move=Move(start, end),
            movedPieceEntity=board[start],
            capturedPieceEntity=board[end]
        )