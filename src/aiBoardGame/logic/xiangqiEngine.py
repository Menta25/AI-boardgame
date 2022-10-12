from dataclasses import dataclass
import logging
from typing import Dict, List, Tuple

from aiBoardGame.logic.pieces import General
from aiBoardGame.logic.auxiliary import Board, Side
from aiBoardGame.logic.move import InvalidMove, MoveRecord
from aiBoardGame.logic.xiangqiBoardGeneration import createXiangqiBoard


@dataclass(init=False)
class XiangqiEngine:
    board: Board
    generals: Dict[Side, Tuple[int, int]]
    currentSide: Side
    moveHistory: List[MoveRecord]

    def __init__(self) -> None:
        self.board, self.generals = createXiangqiBoard()
        self.currentSide = Side.Red
        self.moveHistory = []

    def move(self, fromFile, fromRank, toFile, toRank) -> None:
        if self.board[fromFile, fromRank] == None:
            raise InvalidMove(None, fromFile, fromRank, toFile, toRank, f"No piece found on ({fromFile},{fromRank})")

        chosenPiece = self.board[fromFile, fromRank].piece
        if not chosenPiece.isValidMove(self.board, self.currentSide, fromFile, fromRank, toFile, toRank):
            raise InvalidMove(chosenPiece, fromFile, fromRank, toFile, toRank)

        self._move(fromFile, fromRank, toFile, toRank)

        allyGeneralFile, allyGeneralRank = self.generals[self.currentSide]
        if General.isInCheck(self.board, self.currentSide, allyGeneralFile, allyGeneralRank):
            self._undoMove()
            raise InvalidMove(chosenPiece, fromFile, fromRank, toFile, toRank, f"{self.currentSide}'s General is in check, cannot move {chosenPiece} from ({fromFile},{fromRank}) to ({toFile},{toRank})")

        enemyGeneralFile, enemyGeneralRank = self.generals[self.currentSide.opponent]
        if General.isInCheck(self.board, self.currentSide.opponent, enemyGeneralFile, enemyGeneralRank):
            logging.info(f"{self.currentSide.opponent}'s General is in check")

        #self.currentSide = self.currentSide.opponent
        self.print()

    def _move(self, fromFile, fromRank, toFile, toRank) -> None:
        self.moveHistory.append(MoveRecord(self.board, fromFile, fromRank, toFile, toRank))
        self.board[toFile, toRank] = self.board[fromFile, fromRank]
        self.board[fromFile, fromRank] = None

    def undoMove(self) -> None:
        self._undoMove
        self.print()

    def _undoMove(self) -> None:
        if len(self.moveHistory) > 0:
            lastMove = self.moveHistory.pop()
            self.board[lastMove.fromFile, lastMove.fromRank] = lastMove.movedPiece
            self.board[lastMove.toFile, lastMove.toRank] = lastMove.capturedPiece

    def print(self) -> None:
        boardStr = ""
        for rank in range(self.board.rankLength - 1, -1, -1):
            for file in range(self.board.fileLength):
                if file == 0:
                    if rank == 0:
                        char = " ┗"
                    elif rank == self.board.rankLength - 1:
                        char = " ┏"
                    else:
                        char = " ┣"
                elif file == self.board.fileLength - 1:
                    if rank == 0:
                        char = "━┛"
                    elif rank == self.board.rankLength - 1:
                        char = "━┓"
                    else:
                        char = "━┫"
                else:
                    if rank == 5:
                        char = "━┻"
                    elif rank == 4:
                        char = "━┳"
                    else:
                        char = "━╋"

                boardStr += str(self.board[file, rank].side)[0].lower() + self.board[file, rank].piece.abbreviation if self.board[file, rank] != None else char
                boardStr += "━━"
            boardStr = boardStr[:-2]

            if rank == 5:
                boardStr += "\n ┃                               ┃\n"
            elif rank == self.board.rankLength - 1 or rank == 2:
                boardStr += "\n ┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃\n"
            elif rank == self.board.rankLength - 2 or rank == 1:
                boardStr += "\n ┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃\n"
            else:
                boardStr += "\n ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃\n"
        boardStr = boardStr[:-36]
        print(boardStr)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    game = XiangqiEngine()
    game.move(0, 0, 0, 1)
    game.move(0, 1, 3, 1)
    game.move(3, 1, 3, 8)
    game.move(3, 8, 4, 8)
