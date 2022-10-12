from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from aiBoardGame.logic.auxiliary import Board, BoardEntity, Position


Piece = TypeVar("Piece")


@dataclass(frozen=True)
class InvalidMove(Exception):
    piece: Type[Piece]
    fromPosition: Position
    toPosition: Position
    message: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.piece.__name__} cannot move from {*self.fromPosition,} to {*self.toPosition,}" if self.message is None else self.message


@dataclass(frozen=True)
class Move:
    fromPosition: Position
    toPosition: Position
    movedPieceEntity: BoardEntity
    capturedPieceEntity: Optional[BoardEntity]

    @classmethod
    def make(cls, board: Board, fromPosition: Position, toPosition: Position) -> Move:
        return Move(
            fromPosition=fromPosition,
            toPosition=toPosition,
            movedPieceEntity=board[fromPosition],
            capturedPieceEntity=board[toPosition]
        )