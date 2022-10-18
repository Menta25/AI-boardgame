from dataclasses import dataclass
import logging
from typing import Dict, List, Tuple, Union
from itertools import chain, product, starmap
from collections import defaultdict

from aiBoardGame.logic.pieces import General, Cannon
from aiBoardGame.logic.auxiliary import Board, BoardEntity, Delta, Position, Side
from aiBoardGame.logic.move import InvalidMove, MoveRecord
from aiBoardGame.logic.pieces.horse import Horse
from aiBoardGame.logic.xiangqiBoardGeneration import createXiangqiBoard


@dataclass(frozen=True)
class XiangqiError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(init=False)
class XiangqiEngine:
    board: Board
    generals: Dict[Side, Position]
    currentSide: Side
    moveHistory: List[MoveRecord]
    _validMoves: Dict[Position, List[Position]]

    def __init__(self) -> None:
        self.board, self.generals = createXiangqiBoard()
        self.currentSide = Side.Red
        self.moveHistory = []
        self._validMoves = self._getAllValidMoves()


    def _getAllPossibleMoves(self) -> Dict[Position, List[Position]]:
        return {position: piece.getPossibleMoves(self.board, position) for position, piece in self.board[self.currentSide].items()}

    def _getAllValidMoves(self) -> Dict[Position, List[Position]]:
        possibleMoves: Dict[Position, List[Position]] = {}
        checks, pins = self._getChecksAndPins()

        if len(checks) >= 1:
            possibleMoves[self.generals[self.currentSide]] = General.getPossibleMoves(self.board, self.generals[self.currentSide])
        else:
            possibleMoves = self._getAllPossibleMoves()
        
            for pinned, pinning in pins.items():
                if pinned in possibleMoves:
                    if len(pinning) >= 2:
                        del possibleMoves[pinned]
                    else:
                        pinningGeneralDeltaNorm = (pinning[0] - self.generals[self.currentSide]).normalize()
                        for end in list(possibleMoves[pinned]):
                            if end != pinning:
                                pinningEndDeltaNorm = (pinning[0] - end).normalize()
                                generalEndDeltaNorm = (self.generals[self.currentSide] - end).normalize()
                                if not (pinningGeneralDeltaNorm == pinningEndDeltaNorm and pinningGeneralDeltaNorm != generalEndDeltaNorm):
                                    possibleMoves[pinned].remove(end)

            if len(checks) == 1:
                validEnds = [checks[0]]
                delta = checks[0] - self.generals[self.currentSide]
                if self.board[checks[0]].piece == Horse:
                    delta = (delta/2).round()
                    validEnds.append([self.generals[self.currentSide] + delta])
                else:
                    delta = delta.normalize()
                    end = self.generals[self.currentSide]
                    while (end := end + delta) != checks[0]:
                        validEnds.append
                for start, ends in possibleMoves:
                    if start != self.generals[self.currentSide]:
                        for end in list(ends):
                            if end not in validEnds:
                                possibleMoves[start].remove(end)

        for possibleGeneralMove in list(possibleMoves[self.generals[self.currentSide]]):
            self._move(self.generals[self.currentSide], possibleGeneralMove)
            checks, _ = self._getChecksAndPins()
            self._undoMove()
            if len(checks) > 0:
                possibleMoves[self.generals[self.currentSide]].remove(possibleGeneralMove)

        for piece in list(possibleMoves):
            if len(possibleMoves[piece]) == 0:
                del possibleMoves[piece]

        return possibleMoves

    def _getChecksAndPins(self) -> Tuple[List[Position], Dict[Position, List[Position]]]:
        checks = []
        pins = defaultdict(list)
        for delta in starmap(Delta, chain(product((1,-1), (0,)), product((0,), (1,-1)))):
            possiblePinPositions = []
            position = self.generals[self.currentSide]
            foundBoardEntityCount = 0
            while self.board.isInBounds(position := position + delta) and foundBoardEntityCount < 3:
                if (foundBoardEntity := self.board[position]) is not None:
                    foundBoardEntityCount += 1
                    if foundBoardEntity.side == self.currentSide:
                        possiblePinPositions.append(position)
                    else:
                        if (foundBoardEntityCount == 1 and foundBoardEntity.piece != Cannon) or (foundBoardEntityCount == 2 and foundBoardEntity.piece == Cannon) and \
                            foundBoardEntity.piece.isValidMove(self.board, self.currentSide.opponent, position, self.generals[self.currentSide]):
                            checks.append(position)
                        elif len(possiblePinPositions) > 0 and not ((foundBoardEntityCount == 3) ^ (foundBoardEntity.piece == Cannon)):
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

        if self.board[start] == None:
            raise InvalidMove(None, start, end, f"No piece found on {*start,}")
        elif end not in self._validMoves[start]:
            raise InvalidMove(self.board[start], start, end)

        self._move(start, end)

        self.currentSide = self.currentSide.opponent
        self._validMoves = self._getAllValidMoves()

        if len(self._validMoves) == 0:
            logging.info(f"{self.currentSide.opponent} has delivered a mate, {self.currentSide.opponent} won!")
        else:
            checks, _ = self._getChecksAndPins()
            if len(checks) > 0:
                logging.info(f"{self.currentSide} is in check!")

        self.print()

    def _move(self, start: Position, end: Position) -> None:
        self.moveHistory.append(MoveRecord.make(self.board, start, end))
        self.board[end] = self.board[start]
        self.board[start] = None

        if self.board[end].piece == General:
            self.generals[self.board[end].side] = end

    def undoMove(self) -> None:
        self._undoMove()
        self.currentSide = self.currentSide.opponent
        self._validMoves = self._getAllValidMoves()
        self.print()

    def _undoMove(self) -> None:
        if len(self.moveHistory) > 0:
            lastMove = self.moveHistory.pop()
            self.board[lastMove.start] = lastMove.movedPieceEntity
            self.board[lastMove.end] = lastMove.capturedPieceEntity

            if lastMove.movedPieceEntity.piece == General:
                self.generals[lastMove.movedPieceEntity.side] = lastMove.start
        else:
            raise XiangqiError("Cannot undo move, game is in start state")

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

    while True:
        command = input("Command: ")
        if command == "undo":
            try:
                game.undoMove()
            except XiangqiError as error:
                logging.info(error)
        else:
            try:
                commandParts = command.split(" ")
                if len(commandParts) == 2:
                    startPositionStrs = commandParts[0].split(",")
                    endPositionStrs = commandParts[1].split(",")
                    if len(startPositionStrs) == 2 and len(endPositionStrs) == 2:
                        start = Position(int(startPositionStrs[0]), int(startPositionStrs[1]))
                        end = Position(int(endPositionStrs[0]), int(endPositionStrs[1]))
                        try:
                            game.move(start, end)
                        except InvalidMove as error:
                            logging.info(error)
                        finally:
                            continue
            except:
                pass
            logging.info("Invalid command")
            