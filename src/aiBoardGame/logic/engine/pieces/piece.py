"""Base module for pieces"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple, ClassVar

from aiBoardGame.logic.engine.auxiliary import Board, Position, Side


@dataclass(init=False)
class Piece(ABC):
    """Abstract base class for pieces"""
    fileBounds: ClassVar[Tuple[int, int]] = Board.fileBounds
    """File bounds that given piece operates in"""
    rankBounds: ClassVar[Tuple[int, int]] = Board.rankBounds
    """Rank bounds that given piece operates in"""

    abbreviations: ClassVar[Dict[str, str]] = {
        "base": "X",
        "fen": "X"
    }
    """Abbreviaton for given piece"""


    @classmethod
    def name(cls) -> str:
        """Get given piece class's name

        :return: Piece name
        :rtype: str
        """
        return cls.__name__

    @classmethod
    def fileLength(cls) -> int:
        """Get given piece's file bound length

        :return: File bound length
        :rtype: int
        """
        return sum(cls.fileBounds)

    @classmethod
    def rankLength(cls) -> int:
        """Get given piece's file rank length

        :return: Rank bound length
        :rtype: int
        """
        return sum(cls.rankBounds)

    @classmethod
    def isFileInBounds(cls, side: Side, file: int) -> bool:
        """Checks if file is in operation bounds

        :param side: Side of the board
        :type side: Side
        :param file: File on board
        :type file: int
        :return: Given file is in or not in bounds
        :rtype: bool
        """
        if side == Side.BLACK:
            file = cls.mirrorFile(file)
        return cls.fileBounds[0] <= file < cls.fileBounds[1]

    @classmethod
    def isRankInBounds(cls, side: Side, rank: int) -> bool:
        """Checks if rank is in operation bounds

        :param side: Side of the board
        :type side: Side
        :param rank: Rank on board
        :type rank: int
        :return: Given rank is in or not in bounds
        :rtype: bool
        """
        if side == Side.BLACK:
            rank = cls.mirrorRank(rank)
        return cls.rankBounds[0] <= rank < cls.rankBounds[1]

    @classmethod
    def isPositionInBounds(cls, side: Side, position: Position) -> bool:
        """Checks if position is in operation bounds

        :param side: Side of the board
        :type side: Side
        :param position: Position on board
        :type position: Position
        :return: Given position is in or not in bounds
        :rtype: bool
        """
        return cls.isFileInBounds(side, position.file) and cls.isRankInBounds(side, position.rank)

    @classmethod
    @abstractmethod
    def _getPossibleMoves(cls, board: Board, side: Side, start: Position) -> List[Position]:
        raise NotImplementedError(f"{cls.__name__} has not implemented getPossibleMoves() method")

    @classmethod
    def getPossibleMoves(cls, board: Board, start: Position) -> List[Position]:
        """Generate possible moves from given position

        :param board: Gamestate
        :type board: Board
        :param start: Start position to generate moves from
        :type start: Position
        :return: Possible moves
        :rtype: List[Position]
        """
        side, _ = board[start]
        return [endPosition for endPosition in cls._getPossibleMoves(board, side, start)]

    @classmethod
    @abstractmethod
    def _isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        raise NotImplementedError(f"{cls.__class__.__name__} has not implemented isValidMove() method")

    @classmethod
    def isValidMove(cls, board: Board, side: Side, start: Position, end: Position) -> bool:
        """Check if move is valid from start to end position

        :param board: Gamestate
        :type board: Board
        :param side: Side of the board
        :type side: Side
        :param start: Start position to move from
        :type start: Position
        :param end: End position to move to
        :type end: Position
        :return: Move is valid or not valid
        :rtype: bool
        """
        return cls.isPositionInBounds(side, end) and cls.isPositionInBounds(side, start) and \
               board[side][start] is not None and board[side][start] == cls and \
               end != start and board[side][end] is None and \
               cls._isValidMove(board, side, start, end)

    @staticmethod
    def mirrorFile(file: int) -> int:
        """Mirrors file on board

        :param file: File on board
        :type file: int
        :return: Mirrored file
        :rtype: int
        """
        return Board.fileCount - file - 1

    @staticmethod
    def mirrorRank(rank: int) -> int:
        """Mirrors rank on board

        :param rank: Rank on board
        :type rank: int
        :return: Mirrored rank
        :rtype: int
        """
        return Board.rankCount - rank - 1

    @staticmethod
    def mirrorPosition(position: Position) -> Position:
        """Mirrors position on board

        :param position: Position on board
        :type position: Position
        :return: Mirrored position
        :rtype: Position
        """
        return Position(Piece.mirrorFile(position.file), Piece.mirrorRank(position.rank))
