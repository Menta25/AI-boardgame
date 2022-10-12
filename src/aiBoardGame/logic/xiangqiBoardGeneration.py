from typing import Dict, Tuple
from aiBoardGame.logic.auxiliary import Board, Side
from aiBoardGame.logic.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier


SOLDIER_RANK_OFFSET = 3
CANNON_RANK_OFFSET = 2


def createXiangqiBoard() -> Tuple[Board, Dict[Side, Tuple[int, int]]]:
    xiangqiBoard = Board()

    uniquePieces = [Chariot, Horse, Elephant, Advisor, General]
    for rank, side in [(Board.rankBounds[0], Side.Red), (Board.rankBounds[1]-1, Side.Black)]:
        for file, piece in enumerate(uniquePieces + uniquePieces[-2::-1]):
            xiangqiBoard[side][file, rank] = piece

    for rank, side in [(Board.rankBounds[0]+SOLDIER_RANK_OFFSET, Side.Red), (Board.rankBounds[1]-SOLDIER_RANK_OFFSET-1, Side.Black)]:
        for file in range(Board.fileBounds[0], Board.fileBounds[1], 2):
            xiangqiBoard[side][file, rank] = Soldier

    for rank, side in [(Board.rankBounds[0]+CANNON_RANK_OFFSET, Side.Red), (Board.rankBounds[1]-CANNON_RANK_OFFSET-1, Side.Black)]:
        for file in [Board.fileBounds[0]+1, Board.fileBounds[1]-2]:
            xiangqiBoard[side][file, rank] = Cannon

    generals = {
        Side.Red: (Board.fileLength // 2, Board.rankBounds[0]),
        Side.Black: (Board.fileLength // 2, Board.rankBounds[1] - 1)
    }

    return xiangqiBoard, generals
