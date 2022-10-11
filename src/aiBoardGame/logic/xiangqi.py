from dataclasses import dataclass, field
from typing import Type, Optional

from aiBoardGame.logic.utils import Board, Side
from aiBoardGame.logic.xiangqiBoardGeneration import createXiangqiBoard
from aiBoardGame.logic.piece import Piece


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


@dataclass
class Xiangqi:
    board: Board[Side, Piece] = field(default_factory=createXiangqiBoard, init=False)
    currentSide: Side = Side.Red

    def move(self, fromFile, fromRank, toFile, toRank) -> None:
        if self.board[fromFile][fromRank] == None:
            return
        elif self.board[fromFile][fromRank].side != self.currentSide:
            return

        chosenPiece = self.board[fromFile][fromRank].piece
        if not chosenPiece.isValidMove(self.board, self.currentSide, fromFile, fromRank, toFile, toRank):
            raise InvalidMove(chosenPiece, fromFile, fromRank, toFile, toRank)

        if self.board[toFile][toRank] is not None:
            self.board[toFile][toRank] = None

        self.board[toFile][toRank] = self.board[fromFile][fromRank]
        self.board[fromFile][fromRank] = None
        print(self.board)


if __name__ == "__main__":
    game = Xiangqi()
    game.move(4, 0, 8, 7)
