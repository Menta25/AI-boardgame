from dataclasses import dataclass
import logging
from typing import Dict, List, Tuple, Union
from itertools import chain, product, starmap
from collections import defaultdict

from aiBoardGame.logic.pieces import General, Cannon
from aiBoardGame.logic.auxiliary import Board, BoardEntity, Delta, Position, Side
from aiBoardGame.logic.move import Move, InvalidMove, MoveRecord
from aiBoardGame.logic.pieces.horse import Horse
from aiBoardGame.logic.xiangqiBoardGeneration import createXiangqiBoard


@dataclass(init=False)
class XiangqiEngine:
    board: Board
    generals: Dict[Side, Position]
    currentSide: Side
    moveHistory: List[MoveRecord]

    def __init__(self) -> None:
        self.board, self.generals = createXiangqiBoard()
        self.currentSide = Side.Red
        self.moveHistory = []


    def _getAllPossibleMoves(self) -> Dict[Position, List[Position]]:
        return {position: piece.getPossibleMoves(self.board, position) for position, piece in self.board[self.currentSide].items()}

    def _getAllValidMoves(self) -> List[Move]:
        validMoves = []
        checks, pins = self._getChecksAndPins()

        if len(checks) >= 1:
            return [Move(self.generals[self.currentSide], end) for end in General.getPossibleMoves(self.board, self.generals[self.currentSide])]

        validMoves = self._getAllPossibleMoves()
        
        for pinned, pinning in pins.items():
            if pinned in validMoves:
                if len(pinning) >= 2:
                    del validMoves[pinned]
                else:
                    pinningGeneralDeltaNorm = (pinning[0] - self.generals[self.currentSide]).normalize()
                    for end in list(validMoves[pinned]):
                        if end != pinning:
                            pinningEndDeltaNorm = (pinning[0] - end).normalize()
                            generalEndDeltaNorm = (self.generals[self.currentSide] - end).normalize()
                            if not (pinningGeneralDeltaNorm == pinningEndDeltaNorm and pinningGeneralDeltaNorm != generalEndDeltaNorm):
                                validMoves[pinned].remove(end)

        if len(checks) == 1:
            # TODO: Finish
            pass

        return validMoves

    def _getChecksAndPins(self) -> Tuple[List[Position], Dict[Position, List[Position]]]:
        checks = []
        pins = defaultdict(list)
        for delta in starmap(Delta, chain(product((1,-1), (0,)), product((0,), (1,-1)))):
            possiblePinPositions = []
            position = self.generals[self.currentSide] + delta
            foundBoardEntityCount = 0
            while self.board.isInBounds(position) and foundBoardEntityCount < 3:
                if (foundBoardEntity := self.board[position]) is not None:
                    foundBoardEntityCount += 1
                    if foundBoardEntity.side == self.currentSide:
                        possiblePinPositions.append(position)
                    else:
                        if (foundBoardEntityCount == 1 and foundBoardEntity.piece != Cannon) or (foundBoardEntityCount == 2 and foundBoardEntity.piece == Cannon) and \
                            foundBoardEntity.piece.isValidMove(self.board, self.currentSide.opponent, position, self.generals[self.currentSide]):
                            checks.append(position)
                        elif len(possiblePinPositions) > 0 and not (foundBoardEntityCount == 3 ^ foundBoardEntity.piece == Cannon):
                            for possiblePinPosition in list(possiblePinPositions):
                                possiblePinBoardEntity = self.board[possiblePinPosition]
                                self.board[possiblePinPosition] = None
                                isValidMove = foundBoardEntity.piece.isValidMove(self.board, self.currentSide.opponent, position, self.generals[self.currentSide])
                                self.board[possiblePinPosition] = possiblePinBoardEntity
                                if isValidMove:
                                    pins[possiblePinPosition].append(position)
                                    del possiblePinPositions[possiblePinPosition]

        for delta in starmap(Delta, chain(product((1,-1), (2,-2)), product((2,-2), (1,-1)))):
            position = self.generals[self.currentSide] + delta
            if self.board.isInBounds(position) and self.board[position] == BoardEntity(self.currentSide.opponent, Horse):
                possiblePinPosition = position + (delta/2).round()
                possiblePinBoardEntity = self.board[possiblePinPosition]
                if possiblePinBoardEntity is None or possiblePinBoardEntity.side == self.currentSide:
                    self.board[possiblePinPosition] = None
                    if Horse.isValidMove(self.board, self.currentSide.opponent, position, self.generals[self.currentSide]):
                        if possiblePinBoardEntity is None:
                            checks.append(position)
                        else:
                            pins[possiblePinPosition].append(position)
                    self.board[possiblePinPosition] = possiblePinBoardEntity

        return checks, dict(pins)

    def move(self, start: Union[Position, Tuple[int, int]], end: Union[Position, Tuple[int, int]]) -> None:
        if not isinstance(start, Position):
            start = Position(*start)
        if not isinstance(end, Position):
            end = Position(*end)
        move = Move(start, end)

        if self.board[start] == None:
            raise InvalidMove(None, move, f"No piece found on {*start,}")

        # chosenPiece = self.board[fromPositon].piece
        # if not chosenPiece.isValidMove(self.board, self.currentSide, fromPositon, toPosition):
        #     raise InvalidMove(chosenPiece, fromPositon, toPosition)

        self._move(start, end)

        # allyGeneralFile, allyGeneralRank = self.generals[self.currentSide]
        # if General.isInCheck(self.board, self.currentSide, allyGeneralFile, allyGeneralRank):
        #     self._undoMove()
        #     raise InvalidMove(chosenPiece, fromPositon, toPosition, f"{self.currentSide}'s General is in check, cannot move {chosenPiece} from {*fromPositon,} to {*toPosition,}")

        # enemyGeneralFile, enemyGeneralRank = self.generals[self.currentSide.opponent]
        # if General.isInCheck(self.board, self.currentSide.opponent, enemyGeneralFile, enemyGeneralRank):
        #     logging.info(f"{self.currentSide.opponent}'s General is in check")

        #self.currentSide = self.currentSide.opponent
        self.print()

    def _move(self, start: Position, end: Position) -> None:
        self.moveHistory.append(MoveRecord.make(self.board, start, end))
        self.board[end] = self.board[start]
        self.board[start] = None

        if self.board[end].piece == General:
            self.generals[self.board[end].side] = end

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
