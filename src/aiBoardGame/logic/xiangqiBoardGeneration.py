from aiBoardGame.logic.utils import BoardEntity, Side, Board, FILE_BOUNDS, RANK_BOUNDS

from aiBoardGame.logic.piece import Piece

from aiBoardGame.logic.general import General
from aiBoardGame.logic.advisor import Advisor
from aiBoardGame.logic.elephant import Elephant
from aiBoardGame.logic.horse import Horse
from aiBoardGame.logic.chariot import Chariot
from aiBoardGame.logic.cannon import Cannon
from aiBoardGame.logic.soldier import Soldier


def createXiangqiBoard() -> Board[Side, Piece]:
    xiangqiBoard = Board(sum(FILE_BOUNDS), sum(RANK_BOUNDS))

    uniquePieces = [Chariot, Horse, Elephant, Advisor, General]
    for rank, side in [(Side.Red, RANK_BOUNDS[0]), (Side.Black, RANK_BOUNDS[1]-1)]:
        for file, piece in enumerate(uniquePieces + uniquePieces[-2::-1]):
            xiangqiBoard[file][rank] = BoardEntity(side, piece)

    xiangqiBoard[0][0] = BoardEntity(Side.Red, Chariot)
    xiangqiBoard[1][0] = BoardEntity(Side.Red, Horse)
    xiangqiBoard[2][0] = BoardEntity(Side.Red, Elephant)
    xiangqiBoard[3][0] = BoardEntity(Side.Red, Advisor)
    xiangqiBoard[4][0] = BoardEntity(Side.Red, General)
    xiangqiBoard[5][0] = BoardEntity(Side.Red, Advisor)
    xiangqiBoard[6][0] = BoardEntity(Side.Red, Elephant)
    xiangqiBoard[7][0] = BoardEntity(Side.Red, Horse)
    xiangqiBoard[8][0] = BoardEntity(Side.Red, Chariot)

    xiangqiBoard[2][3] = BoardEntity(Side.Red, Soldier)

    xiangqiBoard[2][6] = BoardEntity(Side.Black, Soldier)
    xiangqiBoard[3][9] = BoardEntity(Side.Black, Advisor)
    xiangqiBoard[6][9] = BoardEntity(Side.Black, Elephant)
    return xiangqiBoard
