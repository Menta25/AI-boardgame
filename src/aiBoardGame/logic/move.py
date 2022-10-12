from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import BoardEntity


@dataclass(frozen=True)
class InvalidMove(Exception):
    piece: Type[Piece]
    fromFile: int
    fromRank: int
    toFile: int
    toRank: int
    message: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.piece.__name__} cannot move from ({self.fromFile},{self.fromRank}) to ({self.toFile},{self.toRank})" if self.message is None else self.message


@dataclass(frozen=True)
class MoveRecord:
    fromFile: int
    fromRank: int
    toFile: int
    toRank: int
    movedPiece: BoardEntity = field(compare=False)
    capturedPiece: Optional[BoardEntity] = field(default=None, compare=False)
