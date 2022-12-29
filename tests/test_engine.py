import pytest
from pathlib import Path

from aiBoardGame.logic.engine.utility import createXiangqiBoard
from aiBoardGame.logic.engine.auxiliary import BoardEntity, Side, Position
from aiBoardGame.logic.engine.xiangqiEngine import XiangqiEngine
from aiBoardGame.logic.engine.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier
from aiBoardGame.logic.engine.replay import replayGame
from aiBoardGame.logic.engine.move import InvalidMove, MoveRecord


class TestEngine:
    def testBoardCreation(self) -> None:
        board, generals = createXiangqiBoard()

        assert board[0,0] == BoardEntity(Side.RED, Chariot)
        assert board[1,0] == BoardEntity(Side.RED, Horse)
        assert board[2,0] == BoardEntity(Side.RED, Elephant)
        assert board[3,0] == BoardEntity(Side.RED, Advisor)
        assert board[4,0] == BoardEntity(Side.RED, General)
        assert board[5,0] == BoardEntity(Side.RED, Advisor)
        assert board[6,0] == BoardEntity(Side.RED, Elephant)
        assert board[7,0] == BoardEntity(Side.RED, Horse)
        assert board[8,0] == BoardEntity(Side.RED, Chariot)
        assert board[1,2] == BoardEntity(Side.RED, Cannon)
        assert board[7,2] == BoardEntity(Side.RED, Cannon)
        assert board[0,3] == BoardEntity(Side.RED, Soldier)
        assert board[2,3] == BoardEntity(Side.RED, Soldier)
        assert board[4,3] == BoardEntity(Side.RED, Soldier)
        assert board[6,3] == BoardEntity(Side.RED, Soldier)
        assert board[8,3] == BoardEntity(Side.RED, Soldier)

        assert board[0,9] == BoardEntity(Side.BLACK, Chariot)
        assert board[1,9] == BoardEntity(Side.BLACK, Horse)
        assert board[2,9] == BoardEntity(Side.BLACK, Elephant)
        assert board[3,9] == BoardEntity(Side.BLACK, Advisor)
        assert board[4,9] == BoardEntity(Side.BLACK, General)
        assert board[5,9] == BoardEntity(Side.BLACK, Advisor)
        assert board[6,9] == BoardEntity(Side.BLACK, Elephant)
        assert board[7,9] == BoardEntity(Side.BLACK, Horse)
        assert board[8,9] == BoardEntity(Side.BLACK, Chariot)
        assert board[1,7] == BoardEntity(Side.BLACK, Cannon)
        assert board[7,7] == BoardEntity(Side.BLACK, Cannon)
        assert board[0,6] == BoardEntity(Side.BLACK, Soldier)
        assert board[2,6] == BoardEntity(Side.BLACK, Soldier)
        assert board[4,6] == BoardEntity(Side.BLACK, Soldier)
        assert board[6,6] == BoardEntity(Side.BLACK, Soldier)
        assert board[8,6] == BoardEntity(Side.BLACK, Soldier)

        assert generals[Side.RED] == Position(4,0)
        assert generals[Side.BLACK] == Position(4,9)

        assert XiangqiEngine().board == board

    def testCurrentSide(self) -> None:
        game = XiangqiEngine()
        assert game.currentSide == Side.RED
        game.move((0,0),(0,1))
        assert game.currentSide == Side.BLACK
        game.move((0,9),(0,8))
        assert game.currentSide == Side.RED

    def testMove(self) -> None:
        game = XiangqiEngine()
        assert game.board[0,0] == BoardEntity(Side.RED, Chariot)
        assert game.board[0,1] == None
        game.move((0,0),(0,1))
        assert game.board[0,0] == None
        assert game.board[0,1] == BoardEntity(Side.RED, Chariot)

    def testGeneralMove(self) -> None:
        game = XiangqiEngine()
        game.move((4,0),(4,1))
        assert game.generals[Side.RED] == Position(4,1)

    def testCapture(self) -> None:
        game = XiangqiEngine()
        assert game.board[1,2] == BoardEntity(Side.RED, Cannon)
        assert game.board[1,9] == BoardEntity(Side.BLACK, Horse)
        game.move((1,2),(1,9))
        assert game.board[1,2] == None
        assert game.board[1,9] == BoardEntity(Side.RED, Cannon)

    def testInvalidMoves(self) -> None:
        game = XiangqiEngine()
        with pytest.raises(InvalidMove):  # NOTE: Invalid piece move
            game.move((2,0),(2,1))
        with pytest.raises(InvalidMove):  # NOTE: Blocked
            game.move((0,0),(1,0))
        with pytest.raises(InvalidMove):  # NOTE: Out of bounds
            game.move((0,0),(-1,0))
        with pytest.raises(InvalidMove):  # NOTE: Invalid side
            game.move((0,9),(0,8))

    def testMoveHistory(self) -> None:
        game = XiangqiEngine()
        assert len(game.moveHistory) == 0
        game.move((0,0),(0,1))
        assert len(game.moveHistory) == 1
        assert game.moveHistory[0] == MoveRecord(
            start=Position(0,0),
            end=Position(0,1),
            movedPieceEntity=BoardEntity(Side.RED, Chariot),
            capturedPieceEntity=None
        )
        game.move((1,7),(1,0))
        assert len(game.moveHistory) == 2
        assert game.moveHistory[1] == MoveRecord(
            start=Position(1,7),
            end=Position(1,0),
            movedPieceEntity=BoardEntity(Side.BLACK, Cannon),
            capturedPieceEntity=BoardEntity(Side.RED, Horse)
        )

    def testUndoMove(self) -> None:
        game = XiangqiEngine()
        board = game.board
        side = game.currentSide
        game.move((0,0),(0,1))
        game.undoMove()
        assert game.board == board
        assert game.currentSide == side
        assert len(game.moveHistory) == 0

    def testFEN(self) -> None:
        assert XiangqiEngine().fen == "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"

    def testGame1(self) -> None:
        gameRecord = Path("tests/data/games/game1.txt")
        game = replayGame(gameRecord)
        assert not game.isOver

    def testGame2(self) -> None:
        gameRecord = Path("tests/data/games/game2.txt")
        game = replayGame(gameRecord)
        assert game.isOver
        assert game.winner == Side.RED
