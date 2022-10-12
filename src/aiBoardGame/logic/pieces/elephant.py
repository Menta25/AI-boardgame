from dataclasses import dataclass
from typing import ClassVar, List, Tuple
from itertools import product

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.auxiliary import Board, Position, Side


NEW_RANK_LENGTH = Piece.rankLength() // 2


@dataclass(init=False)
class Elephant(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = Piece.fileBounds
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviation: ClassVar[str] = "E"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromFile: int, fromRank: int, toFile: int, toRank: int) -> bool:
        deltaFile = toFile - fromFile
        deltaRank = toRank - fromRank

        isValidDelta = abs(deltaFile) == 2 and abs(deltaRank) == 2
        isPieceInTheWay = board[fromFile + round(deltaFile / 2)][fromRank + round(deltaRank / 2)] is not None

        return isValidDelta and not isPieceInTheWay

    # TODO: Check for intervening pieces
    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side, fromPosition: Position) -> List[Position]:
        return [Position(fromPosition.file + deltaFile, fromPosition.rank + deltaRank) for deltaFile, deltaRank in product((-2,2), repeat=2)]
