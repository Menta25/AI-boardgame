from dataclasses import dataclass
import logging
from typing import Dict, List, Tuple, Union

from aiBoardGame.logic.pieces import General
from aiBoardGame.logic.auxiliary import Board, Position, Side
from aiBoardGame.logic.move import InvalidMove, Move
from aiBoardGame.logic.xiangqiBoardGeneration import createXiangqiBoard


@dataclass(init=False)
class XiangqiEngine:
    board: Board
    generals: Dict[Side, Tuple[int, int]]
    currentSide: Side
    moveHistory: List[Move]

    def __init__(self) -> None:
        self.board, self.generals = createXiangqiBoard()
        self.currentSide = Side.Red
        self.moveHistory = []

    def move(self, fromPositon: Union[Position, Tuple[int, int]], toPosition: Union[Position, Tuple[int, int]]) -> None:
        if not isinstance(fromPositon, Position):
            fromPositon = Position(*fromPositon)
        if not isinstance(toPosition, Position):
            toPosition = Position(*toPosition)

        if self.board[fromPositon] == None:
            raise InvalidMove(None, fromPositon, toPosition, f"No piece found on {*fromPositon,}")

        chosenPiece = self.board[fromPositon].piece
        if not chosenPiece.isValidMove(self.board, self.currentSide, fromPositon, toPosition):
            raise InvalidMove(chosenPiece, fromPositon, toPosition)

        self._move(fromPositon, toPosition)

        allyGeneralFile, allyGeneralRank = self.generals[self.currentSide]
        if General.isInCheck(self.board, self.currentSide, allyGeneralFile, allyGeneralRank):
            self._undoMove()
            raise InvalidMove(chosenPiece, fromPositon, toPosition, f"{self.currentSide}'s General is in check, cannot move {chosenPiece} from {*fromPositon,} to {*toPosition,}")

        enemyGeneralFile, enemyGeneralRank = self.generals[self.currentSide.opponent]
        if General.isInCheck(self.board, self.currentSide.opponent, enemyGeneralFile, enemyGeneralRank):
            logging.info(f"{self.currentSide.opponent}'s General is in check")

        #self.currentSide = self.currentSide.opponent
        self.print()

    def _move(self, fromPosition: Position, toPosition: Position) -> None:
        self.moveHistory.append(Move.make(self.board, fromPosition, toPosition))
        self.board[toPosition] = self.board[fromPosition]
        self.board[fromPosition] = None

    def undoMove(self) -> None:
        self._undoMove()
        self.print()

    def _undoMove(self) -> None:
        if len(self.moveHistory) > 0:
            lastMove = self.moveHistory.pop()
            self.board[lastMove.fromPosition] = lastMove.movedPieceEntity
            self.board[lastMove.toPosition] = lastMove.capturedPieceEntity

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
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    game = XiangqiEngine()
    game.move((0, 0), (0, 1))
    game.move((0, 1), (3, 1))
    game.move((3, 1), (3, 8))
    game.move((3, 8), (4, 8))
    game.undoMove()