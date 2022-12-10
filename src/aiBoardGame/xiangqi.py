from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from aiBoardGame.logic import XiangqiEngine, InvalidMove, Board, Side, Difficulty, FairyStockfish
from aiBoardGame.vision import RobotCamera, CameraError, XiangqiPieceClassifier, BoardImage
from aiBoardGame.robot import RobotArm

from aiBoardGame.player import HumanPlayer, RobotPlayer, Player
from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class GameplayError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class Xiangqi:
    def __init__(self, camera: RobotCamera, robotArm: RobotArm, difficulty: Difficulty = Difficulty.Medium, classifierWeights: Path = XiangqiPieceClassifier.baseWeightsPath, stockfishPath: Path = FairyStockfish.baseBinaryPath) -> None:
        if not camera.isCalibrated:
            raise GameplayError("Camera is not calibrated, cannot play game")
        elif not robotArm.isConnected:
            raise GameplayError("Robot arm is not connected, cannot play game")

        self.human = HumanPlayer()
        self.robot = RobotPlayer(arm=robotArm, stockfish=FairyStockfish(binaryPath=stockfishPath, difficulty=difficulty))

        self.camera = camera
        self.classifier = XiangqiPieceClassifier(weights=classifierWeights, device=XiangqiPieceClassifier.getAvailableDevice())
        self.newGame()

    @property
    def difficulty(self) -> Difficulty:
        return self.robot.stockfish.difficulty

    @difficulty.setter
    def difficulty(self, value: Difficulty) -> None:
        self.robot.stockfish.difficulty = value

    def newGame(self) -> None:
        self.engine = XiangqiEngine()
        self.lastBoardInfo: Optional[Tuple[BoardImage, str]] = None
        self.robot.calibrate()

    def play(self) -> None:
        self._analyseBoard()
        while not self.engine.isOver:
            try:
                self._playTurn()
            except InvalidMove:
                pass

    def _playTurn(self) -> None:
        currentPlayer: Player = self.human if self.engine.currentSide == Side.Red else self.robot
        currentPlayer.makeMove(self.lastBoardInfo)
        self._updateEngine()

    @retry(times=3, exceptions=(InvalidMove), callback=rerunAfterCorrection)
    def _updateEngine(self) -> None:
        board = self._analyseBoard()
        self.engine.update(board)

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> Board:
        image = self.camera.read(undistorted=True)
        boardImage = self.camera.detectBoard(image)
        self.lastBoardInfo = (boardImage, self.engine.FEN)
        return self.classifier.predictBoard(boardImage)


if __name__ == "__main__":
    import logging
    from aiBoardGame.robot import RobotArmException

    logging.basicConfig(level=logging.INFO, format="")

    try:
        cameraIntrinsics = Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz")
        camera = RobotCamera(feedInput=2, resolution=(1920, 1080), intrinsicsFile=cameraIntrinsics)

        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=500_000)
        robotArm.connect()

        game = Xiangqi(camera=camera, robotArm=robotArm, difficulty=Difficulty.Medium)
        input("Press any key if you want to start to play")
        game.play()

        robotArm.disconnect()
    except (CameraError, RobotArmException, GameplayError) as error:
        logging.error(str(error))
