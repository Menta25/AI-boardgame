import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from itertools import chain, product, starmap
from collections import defaultdict

from aiBoardGame.logic.engine.pieces import General, Cannon, Horse
from aiBoardGame.logic.engine.move import MoveRecord, InvalidMove
from aiBoardGame.logic.engine.auxiliary import Board, BoardEntity, Delta, Position, Side
from aiBoardGame.logic.engine.utility import createXiangqiBoard, baseNotationToMove, boardToStr


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

    # TODO: Do not allow perpetual chasing and checking
    # TODO: Signal end of the game (its kind of already implemented)
    # TODO: Calculate approximate values for each side
    # TODO: Generate appropriate games state for AlphaZero
    def move(self, start: Union[Position, Tuple[int, int]], end: Union[Position, Tuple[int, int]]) -> None:
        if not isinstance(start, Position):
            start = Position(*start)
        if not isinstance(end, Position):
            end = Position(*end)

        if self.board[start] == None:
            raise InvalidMove(None, start, end, f"No piece found on {*start,}")
        elif start not in self._validMoves or end not in self._validMoves[start]:
            raise InvalidMove(self.board[start].piece, start, end)

        self._move(start, end)

        print(boardToStr(self.board))

        self.currentSide = self.currentSide.opponent
        self._validMoves = self._getAllValidMoves()

        if len(self._validMoves) == 0:
            logging.info(f"{self.currentSide.opponent} has delivered a mate, {self.currentSide.opponent} won!")
        else:
            checks, _ = self._getChecksAndPins()
            if len(checks) > 0:
                logging.info(f"{self.currentSide} is in check!")

    def undoMove(self) -> None:
        self._undoMove()
        self.currentSide = self.currentSide.opponent
        self._validMoves = self._getAllValidMoves()
        print(boardToStr(self.board))

    def _move(self, start: Position, end: Position) -> None:
        self.moveHistory.append(MoveRecord.make(self.board, start, end))
        self.board[end] = self.board[start]
        self.board[start] = None

        if self.board[end].piece == General:
            self.generals[self.board[end].side] = end

    @property
    def FEN(self) -> str:
        return f"{self.board.FEN} {self.currentSide.FEN} - - 0 {len(self.moveHistory)//2+1}"

    def _undoMove(self) -> None:
        if len(self.moveHistory) > 0:
            lastMove = self.moveHistory.pop()
            self.board[lastMove.start] = lastMove.movedPieceEntity
            self.board[lastMove.end] = lastMove.capturedPieceEntity

            if lastMove.movedPieceEntity.piece == General:
                self.generals[lastMove.movedPieceEntity.side] = lastMove.start
        else:
            raise XiangqiError("Cannot undo move, game is in start state")

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
                        if ((foundBoardEntityCount == 1 and foundBoardEntity.piece != Cannon) or (foundBoardEntityCount == 2 and foundBoardEntity.piece == Cannon)) and \
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
                                    possiblePinPositions.remove(possiblePinPosition)

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

    def _getAllPossibleMoves(self) -> Dict[Position, List[Position]]:
        allPossibleMoves = {}
        for position, piece in self.board[self.currentSide].items():
            possibleMoves = piece.getPossibleMoves(self.board, position)
            if len(possibleMoves) > 0:
                allPossibleMoves[position] = possibleMoves
        return allPossibleMoves

    def _getAllValidMoves(self) -> Dict[Position, List[Position]]:
        possibleMoves: Dict[Position, List[Position]] = {}
        checks, pins = self._getChecksAndPins()

        if len(checks) > 1:
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
                checkGeneralDelta = checks[0] - self.generals[self.currentSide]
                if self.board[checks[0]].piece == Horse:
                    checkGeneralDeltaNorm = (checkGeneralDelta/2).round()
                    validEnds.append([self.generals[self.currentSide] + checkGeneralDeltaNorm])
                else:
                    checkGeneralDeltaNorm = checkGeneralDelta.normalize()
                    end = self.generals[self.currentSide]
                    while (end := end + checkGeneralDeltaNorm) != checks[0]:
                        validEnds.append(end)
                for start, ends in possibleMoves.items():
                    if start != self.generals[self.currentSide]:
                        if self.board[checks[0]].piece == Cannon and start.isBetween(checks[0], self.generals[self.currentSide]):
                            for end in list(ends):
                                checkEndDeltaNorm = (checks[0] - end).normalize()
                                generalEndDeltaNorm = (self.generals[self.currentSide] - end).normalize()
                                if checkGeneralDeltaNorm == checkEndDeltaNorm and checkGeneralDeltaNorm != generalEndDeltaNorm:
                                    possibleMoves[start].remove(end)
                        else:
                            for end in list(ends):
                                if end not in validEnds:
                                    possibleMoves[start].remove(end)

        if self.generals[self.currentSide] in possibleMoves:
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
        elif command.startswith("not"):
            notation = command.split(" ")[1]
            start, end = baseNotationToMove(game.board, game.currentSide, notation)
            if start is not None and end is not None:
                logging.info(f"From {*start,} to {*end,}")
            else:
                logging.info("Cannot convert notation to move")
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
                elif len(commandParts) == 1:
                    try:
                        game.moveFromBaseNotation(commandParts[0])
                    except XiangqiError as error:
                        logging.info(error)
                    finally:
                        continue
            except:
                pass
            logging.info("Invalid command")
            