from pathlib import Path
import cv2 as cv

from aiBoardGame.logic.engine.utility import prettyBoard, createXiangqiBoard
from aiBoardGame.logic.engine.auxiliary import Board, Side
from aiBoardGame.logic.engine.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier
from aiBoardGame.vision.xiangqiPieceClassifier import XiangqiPieceClassifier
from aiBoardGame.vision.camera import RobotCameraInterface


class TestClassifier:
    camera = RobotCameraInterface((1920,1080), intrinsicsFile=Path("tests/data/camCalibs.npz"))
    clasifier = XiangqiPieceClassifier(device=XiangqiPieceClassifier.getAvailableDevice())

    def testClassifyExample1(self) -> None:
        image = cv.imread(Path("tests/data/boardImages/example0.jpg").as_posix())
        boardImage = self.camera.detectBoard(image)
        predictedBoard = self.clasifier.predictBoard(boardImage, allTiles=False)
        assert predictedBoard == createXiangqiBoard()[0]

    def testClassifyExample2(self) -> None:
        image = cv.imread(Path("tests/data/boardImages/example1.jpg").as_posix())
        boardImage = self.camera.detectBoard(image)
        predictedBoard = self.clasifier.predictBoard(boardImage, allTiles=False)
        board = Board()
        board[Side.RED][1,0] = Chariot
        board[Side.RED][2,0] = Elephant
        board[Side.RED][5,0] = Advisor
        board[Side.RED][8,0] = Chariot
        board[Side.RED][4,1] = Advisor
        board[Side.RED][0,2] = Cannon
        board[Side.RED][2,2] = Horse
        board[Side.RED][4,2] = General
        board[Side.RED][6,2] = Horse
        board[Side.RED][7,2] = Cannon
        board[Side.RED][8,2] = Elephant
        board[Side.RED][0,3] = Soldier
        board[Side.RED][2,3] = Soldier
        board[Side.RED][4,3] = Soldier
        board[Side.RED][8,3] = Soldier
        board[Side.RED][6,4] = Soldier

        board[Side.BLACK][2,9] = Elephant
        board[Side.BLACK][3,9] = General
        board[Side.BLACK][5,9] = Advisor
        board[Side.BLACK][7,9] = Horse
        board[Side.BLACK][8,9] = Chariot
        board[Side.BLACK][4,8] = Advisor
        board[Side.BLACK][1,7] = Chariot
        board[Side.BLACK][4,7] = Elephant
        board[Side.BLACK][7,7] = Cannon
        board[Side.BLACK][0,6] = Soldier
        board[Side.BLACK][4,6] = Horse
        board[Side.BLACK][6,6] = Soldier
        board[Side.BLACK][2,5] = Soldier
        board[Side.BLACK][8,5] = Soldier
        board[Side.BLACK][1,4] = Cannon
        board[Side.BLACK][4,4] = Soldier

        assert predictedBoard == board

    def testClassifyExample3(self) -> None:
        image = cv.imread(Path("tests/data/boardImages/example2.jpg").as_posix())
        boardImage = self.camera.detectBoard(image)
        predictedBoard = self.clasifier.predictBoard(boardImage, allTiles=False)
        board = Board()
        board[Side.RED][0,0] = Chariot
        board[Side.RED][1,0] = Elephant
        board[Side.RED][2,0] = Horse
        board[Side.RED][5,0] = Advisor
        board[Side.RED][7,0] = Horse
        board[Side.RED][4,1] = Advisor
        board[Side.RED][8,1] = Chariot
        board[Side.RED][0,2] = Cannon
        board[Side.RED][5,2] = General
        board[Side.RED][7,2] = Cannon
        board[Side.RED][8,2] = Elephant
        board[Side.RED][0,3] = Soldier
        board[Side.RED][0,3] = Soldier
        board[Side.RED][2,3] = Soldier
        board[Side.RED][4,4] = Soldier
        board[Side.RED][6,4] = Soldier

        board[Side.BLACK][2,9] = Elephant
        board[Side.BLACK][4,9] = General
        board[Side.BLACK][5,9] = Advisor
        board[Side.BLACK][7,9] = Horse
        board[Side.BLACK][8,9] = Chariot
        board[Side.BLACK][0,7] = Chariot
        board[Side.BLACK][2,7] = Horse
        board[Side.BLACK][3,7] = Advisor
        board[Side.BLACK][4,7] = Elephant
        board[Side.BLACK][7,7] = Cannon
        board[Side.BLACK][0,6] = Soldier
        board[Side.BLACK][6,6] = Soldier
        board[Side.BLACK][8,6] = Soldier
        board[Side.BLACK][2,5] = Soldier
        board[Side.BLACK][4,5] = Soldier
        board[Side.BLACK][1,4] = Cannon

        assert predictedBoard == board

    def testClassifyExample4(self) -> None:
        image = cv.imread(Path("tests/data/boardImages/example3.jpg").as_posix())
        boardImage = self.camera.detectBoard(image)
        predictedBoard = self.clasifier.predictBoard(boardImage, allTiles=False)
        
        assert predictedBoard == createXiangqiBoard()[0]
