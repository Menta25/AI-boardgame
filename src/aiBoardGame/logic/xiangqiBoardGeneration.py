from aiBoardGame.logic.utils import BoardEntity, Side, Board, FILE_BOUNDS, RANK_BOUNDS
from aiBoardGame.logic.piece import Piece
from aiBoardGame.logic.soldier import Soldier
from aiBoardGame.logic.chariot import Chariot
from aiBoardGame.logic.advisor import Advisor
from aiBoardGame.logic.elephant import Elephant
from aiBoardGame.logic.general import General


def createXiangqiBoard() -> Board[Side, Piece]:
    xiangqiBoard = Board(sum(FILE_BOUNDS), sum(RANK_BOUNDS))
    xiangqiBoard[2][3] = BoardEntity(Side.Red, Soldier)
    xiangqiBoard[0][0] = BoardEntity(Side.Red, Chariot)
    xiangqiBoard[3][0] = BoardEntity(Side.Red, Advisor)
    xiangqiBoard[2][0] = BoardEntity(Side.Red, Elephant)
    xiangqiBoard[4][0] = BoardEntity(Side.Red, General)

    xiangqiBoard[2][6] = BoardEntity(Side.Black, Soldier)
    xiangqiBoard[3][9] = BoardEntity(Side.Black, Advisor)
    xiangqiBoard[6][9] = BoardEntity(Side.Black, Elephant)
    return xiangqiBoard