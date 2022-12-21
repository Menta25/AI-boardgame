"""Xiangqi rules"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union, Optional
from itertools import chain, product, starmap
from collections import defaultdict

from aiBoardGame.logic.engine.pieces import General, Cannon, Horse
from aiBoardGame.logic.engine.move import MoveRecord, InvalidMove
from aiBoardGame.logic.engine.auxiliary import Board, BoardEntity, Delta, Position, Side
from aiBoardGame.logic.engine.utility import createXiangqiBoard, baseNotationToMove


@dataclass(init=False)
class XiangqiEngine:
    """Class for controlling Xiangqi game state and verifying moves"""
    board: Board
    """Board that sides operate on"""
    generals: Dict[Side, Position]
    """Stored positions of the generals"""
    currentSide: Side
    """Next that has to move"""
    moveHistory: List[MoveRecord]
    """Stored moves made by both sides"""

    _checks: List[Position]
    _pins: Dict[Position, List[Position]]
    _validMoves: Dict[Position, List[Position]]

    def __init__(self) -> None:
        """Constructs a XiangqiEngine object
        """
        self.board, self.generals = createXiangqiBoard()
        self.currentSide = Side.RED
        self.moveHistory = []
        self._calculateValidMoves()

    @property
    def isCurrentPlayerChecked(self) -> bool:
        """Check if current side is in check"""
        return len(self._checks) > 0

    @property
    def isOver(self) -> bool:
        """Check if a side has checkmated the other"""
        return len(self._validMoves) == 0

    @property
    def winner(self) -> Optional[Side]:
        """Return winner side if the game is over"""
        return self.currentSide.opponent if self.isOver else None

    def newGame(self) -> None:
        """Start a new game instance
        """
        self.__init__()  # pylint: disable=unnecessary-dunder-call

    # TODO: Do not allow perpetual chasing and checking
    # TODO: Calculate approximate values for each side
    def move(self, start: Union[Position, Tuple[int, int]], end: Union[Position, Tuple[int, int]]) -> None:
        """Move a piece on board. All possible and valid moves are generated between turns, given move has to be amongst them

        :param start: Start position to move from
        :type start: Union[Position, Tuple[int, int]]
        :param end: End position to move to
        :type end: Union[Position, Tuple[int, int]]
        :raises InvalidMove: Game is already over
        :raises InvalidMove: No piece found on start position
        :raises InvalidMove: Given piece cannot make the move (out of bounds, piece is in check, etc.)
        """
        if not isinstance(start, Position):
            start = Position(*start)
        if not isinstance(end, Position):
            end = Position(*end)

        if self.isOver:
            raise InvalidMove(None, start, end, "Cannot move beacuse the game is already over, start a new game or undo last move")
        elif self.board[start] is None:
            raise InvalidMove(None, start, end, f"No piece found on {*start,}")
        elif start not in self._validMoves or end not in self._validMoves[start]:
            raise InvalidMove(self.board[start].piece, start, end)

        self._move(start, end)
        self.currentSide = self.currentSide.opponent
        self._calculateValidMoves()

    def undoMove(self) -> None:
        """Undo last move made. Also removes it from the move history
        """
        self._undoMove()
        self.currentSide = self.currentSide.opponent
        self._calculateValidMoves()

    def update(self, board: Board) -> None:
        """Update board with a new board state if it is a valid transition

        :param board: New board state
        :type board: Board
        :raises InvalidMove: No piece were moved
        :raises InvalidMove: Multiple piece were moved
        :raises InvalidMove: Moved piece does not match with it's previous state
        """
        selfPiecesAsSet = set(self.board.pieces)
        otherPiecesAsSet = set(board.pieces)

        selfDifference = list(selfPiecesAsSet - otherPiecesAsSet)
        otherDifference = list(otherPiecesAsSet - selfPiecesAsSet)

        if len(selfDifference) == 0 and len(otherDifference) == 0:
            raise InvalidMove(None, None, None, "Cannot update because no piece were moved")
        elif not (1 <= len(selfDifference) <= 2 and len(otherDifference) == 1):
            logging.error(selfDifference)
            logging.error(otherDifference)
            raise InvalidMove(None, None, None, "Cannot update because multiple piece were moved")

        end, movedBoardEntity = otherDifference[0]
        start = None
        for position, boardEntity in selfDifference:
            if boardEntity == movedBoardEntity:
                start = position

        if start is None:
            raise InvalidMove(None, None, None, "Moved piece does not match with it's previous state")

        self.move(start, end)

    def _move(self, start: Position, end: Position) -> None:
        self.moveHistory.append(MoveRecord.make(self.board, start, end))
        self.board[end] = self.board[start]
        self.board[start] = None

        if self.board[end].piece == General:
            self.generals[self.board[end].side] = end

    @property
    def fen(self) -> str:
        """Game's FEN"""
        return f"{self.board.fen} {self.currentSide.fen} - - 0 {len(self.moveHistory)//2+1}"

    def _undoMove(self) -> None:
        if len(self.moveHistory) > 0:
            lastMove = self.moveHistory.pop()
            self.board[lastMove.start] = lastMove.movedPieceEntity
            self.board[lastMove.end] = lastMove.capturedPieceEntity

            if lastMove.movedPieceEntity.piece == General:
                self.generals[lastMove.movedPieceEntity.side] = lastMove.start
        else:
            raise InvalidMove(None, None, None, "Cannot undo move, game is in start state")

    def _calculateValidMoves(self) -> None:
        self._checks, self._pins = self._getChecksAndPins()
        self._validMoves = self._getAllValidMoves(self._checks, self._pins)

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
                        elif len(possiblePinPositions) > 0 and not (foundBoardEntityCount == 3) ^ (foundBoardEntity.piece == Cannon):
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

    def _getAllValidMoves(self, checks: List[Position], pins: Dict[Position, List[Position]]) -> Dict[Position, List[Position]]:
        possibleMoves: Dict[Position, List[Position]] = {}

        if len(self._checks) > 1:
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
                            if end != pinning[0]:
                                pinningEndDeltaNorm = (pinning[0] - end).normalize()
                                generalEndDeltaNorm = (self.generals[self.currentSide] - end).normalize()
                                if not (pinningGeneralDeltaNorm == pinningEndDeltaNorm and pinningGeneralDeltaNorm != generalEndDeltaNorm):
                                    possibleMoves[pinned].remove(end)

            if len(checks) == 1:
                validEnds = [checks[0]]
                checkGeneralDelta = checks[0] - self.generals[self.currentSide]
                if self.board[checks[0]].piece == Horse:
                    checkGeneralDeltaNorm = (checkGeneralDelta/2).round()
                    validEnds.append(self.generals[self.currentSide] + checkGeneralDeltaNorm)
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
                checksAfterMove, _ = self._getChecksAndPins()
                self._undoMove()
                if len(checksAfterMove) > 0:
                    possibleMoves[self.generals[self.currentSide]].remove(possibleGeneralMove)

        for piece in list(possibleMoves):
            if len(possibleMoves[piece]) == 0:
                del possibleMoves[piece]

        return possibleMoves

if __name__ == "__main__":
    from aiBoardGame.logic.engine.utility import prettyBoard

    logging.basicConfig(format="", level=logging.INFO)

    game = XiangqiEngine()

    while True:
        command = input("Command: ")
        if command == "undo":
            try:
                game.undoMove()
            except InvalidMove as error:
                logging.info(error)
        elif command.startswith("not"):
            notation = command.split(" ")[1]
            startPosition, endPosition = baseNotationToMove(game.board, game.currentSide, notation)
            if startPosition is not None and endPosition is not None:
                logging.info(f"From {*startPosition,} to {*endPosition,}")
            else:
                logging.info("Cannot convert notation to move")
        else:
            try:
                commandParts = command.split(" ")
                if len(commandParts) == 2:
                    startPositionStrs = commandParts[0].split(",")
                    endPositionStrs = commandParts[1].split(",")
                    if len(startPositionStrs) == 2 and len(endPositionStrs) == 2:
                        startPosition = Position(int(startPositionStrs[0]), int(startPositionStrs[1]))
                        endPosition = Position(int(endPositionStrs[0]), int(endPositionStrs[1]))
                        try:
                            game.move(startPosition, endPosition)
                            logging.info(prettyBoard(game.board, colors=True, lastMove=(startPosition, endPosition)))
                        except InvalidMove as error:
                            logging.info(error)
                        finally:
                            continue
            except Exception:
                pass
            logging.info("Invalid command")
            