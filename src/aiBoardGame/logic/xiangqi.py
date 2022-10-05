from dataclasses import dataclass, field

from aiBoardGame.logic.utils import BoardState, Side, FILE_BOUNDS, RANK_BOUNDS
import aiBoardGame.logic.piece as piece
import aiBoardGame.logic.soldier as soldier

def createXiangqiBoard() -> BoardState[Side, piece.Piece]:
    xiangqiBoard = BoardState(sum(FILE_BOUNDS)+1, sum(RANK_BOUNDS)+1, Side)
    xiangqiBoard[Side.Red][0][0] = soldier.Soldier
    return xiangqiBoard


@dataclass
class Xiangqi:
    boardState: BoardState[Side, piece.Piece] = field(default_factory=createXiangqiBoard, init=False)
    currentSide: Side = Side.Red

    def move(self, fF, fR, tF, tR) -> None:
        self.boardState[self.currentSide][fF][fR].move(self.boardState, self.currentSide, fF, fR, tF, tR)

if __name__ == "__main__":
    game = Xiangqi()
    game.move(0, 0, 0, 1)