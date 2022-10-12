import numpy as np

from dataclasses import dataclass
from typing import ClassVar, List, Tuple
from itertools import chain, product

from aiBoardGame.logic.pieces import Piece
from aiBoardGame.logic.pieces.cannon import Cannon
from aiBoardGame.logic.pieces.horse import Horse
from aiBoardGame.logic.auxiliary import Board, Position, Side


NEW_FILE_LENGTH = 3
NEW_RANK_LENGTH = 3

FILE_MARGIN = (Piece.fileLength() - NEW_FILE_LENGTH) // 2


@dataclass(init=False)
class General(Piece):
    fileBounds: ClassVar[Tuple[int, int]] = (Piece.fileBounds[0] + FILE_MARGIN, Piece.fileBounds[1] - FILE_MARGIN)
    rankBounds: ClassVar[Tuple[int, int]] = (Piece.rankBounds[0], NEW_RANK_LENGTH)

    abbreviation: ClassVar[str] = "G"

    @classmethod
    def _isValidMove(cls, board: Board, side: Side, fromPosition: Position, toPosition: Position) -> bool:
        deltaFile = toPosition.file - fromPosition.file
        deltaRank = toPosition.rank - fromPosition.rank

        isOneDeltaOnly = not (deltaFile != 0 and deltaRank != 0)
        isValidDelta = abs(deltaFile) == 1 or abs(deltaRank) == 1

        if isOneDeltaOnly and isValidDelta:
            return True
        elif isOneDeltaOnly and abs(deltaRank) > 1 and board[toPosition].piece == General:  # NOTE: Flying general
            for rank in range(fromPosition.rank + np.sign(deltaRank), toPosition.rank, np.sign(deltaRank)):
                if board[toPosition.file, rank] is not None:   
                    return False
            return True
        else:
            return False

    @classmethod
    def isInCheck(cls, board: Board, side: Side, file: int, rank: int) -> bool:
        upwardRanks = list(range(rank + 1, Piece.rankBounds[1]))
        downwardRanks = list(range(rank - 1, Piece.rankBounds[0], -1))
        rightwardFiles = list(range(file + 1, Piece.fileBounds[1]))
        leftwardFiles = list(range(file - 1, Piece.fileBounds[0], -1))

        upwardRanks = zip([file]*len(upwardRanks), upwardRanks)
        downwardRanks = zip([file]*len(downwardRanks), downwardRanks)
        rightwardFiles = zip(rightwardFiles, [rank]*len(rightwardFiles))
        leftwardFiles = zip(leftwardFiles, [rank]*len(leftwardFiles))

        directions = [upwardRanks, rightwardFiles, downwardRanks, leftwardFiles]

        for direction in directions:
            foundPieceCount = 0
            for checkFile, checkRank in direction:
                if foundPieceCount == 2:
                    break
                if board[checkFile, checkRank] is None:
                    continue
                foundPieceCount += 1
                foundPiece = board[checkFile, checkRank]
                if foundPiece.side == side.opponent and (foundPieceCount == 1 and foundPiece != Cannon or foundPieceCount == 2 and foundPiece == Cannon):
                    if foundPiece.piece.isValidMove(board, side.opponent, Position(checkFile, checkRank), Position(file, rank)):
                        return True

        horseDeltas = [(fstSign*1,sndSign*2) for fstSign, sndSign in [(1,1),(1,-1),(-1,1),(-1,-1)]]
        horseDeltas += [horseDeltas[::-1] for horseDeltas in horseDeltas]
        
        for deltaFile, deltaRank in horseDeltas:
            if Horse.isValidMove(board, side.opponent, Position(file+deltaFile, rank+deltaRank), Position(file, rank)):
                return True

        return False
        

    @classmethod
    def _getPossibleMoves(cls, board: Board, side: Side,  fromPosition: Position) -> List[Position]:
        possibleToPositions = []
        for deltaFile, deltaRank in chain(product((1,-1), (0,)), product((0,), (1,-1))):
            toPosition = fromPosition + (deltaFile, deltaRank)
            if cls.isPositionInBounds(side, toPosition) and board[side][toPosition] is None:
                possibleToPositions.append(toPosition)
        toPosition = fromPosition + (0, side)
        while cls.isPositionInBounds(side, toPosition):
            if board[toPosition] is not None:
                if board[side.opponent][toPosition] == General:
                    possibleToPositions.append(toPosition)
                else:
                    break
        return possibleToPositions