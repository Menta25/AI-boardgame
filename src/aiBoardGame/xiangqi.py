from dataclasses import dataclass

from aiBoardGame.logic import XiangqiEngine, InvalidMove, Side, Difficulty, FairyStockfish
from aiBoardGame.vision import RobotCamera, CameraError, XiangqiPieceClassifier

from aiBoardGame.player import HumanPlayer, RobotPlayer, Player
from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class GameplayError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class Xiangqi:
    def __init__(self, camera: RobotCamera, classifier: XiangqiPieceClassifier, robotArm: RobotArm, stockfishPath: Path = FairyStockfish.baseBinaryPath, difficulty: Difficulty = Difficulty.Medium) -> None:
        if not camera.isCalibrated:
            raise GameplayError("Camera is not calibrated, cannot play game")
        elif not self.classifier.isTrained:
            raise GameplayError("Classifier is not trained, cannot play game")
        elif not robotArm.isConnected:
            raise GameplayError("Robot arm is not connected, cannot play game")

        self.human = HumanPlayer()
        self.robot = RobotPlayer(arm=robotArm, stockfish=FairyStockfish(binaryPath=stockfishPath, difficulty=difficulty))

        self.camera = camera
        self.classifier = classifier
        self.engine = XiangqiEngine()

    @property
    def difficulty(self) -> Difficulty:
        return self.robot.stockfish.difficulty

    @difficulty.setter
    def difficulty(self, value: Difficulty) -> None:
        self.robot.stockfish.difficulty = value

    def play(self) -> None:
        self.robot.arm.resetPosition()

        while not self.engine.isOver:
            try:
                self._playTurn()
            except InvalidMove:
                pass

        self.robot.arm.resetPosition()

    def _playTurn(self) -> None:
        currentPlayer: Player = self.human if self.engine.currentSide == Side.Red else self.robot
        currentPlayer.makeMove(self.engine)
        self._updateEngine()

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> None:
        image = self.camera.read(undistorted=True)
        boardImage = self.camera.detectBoard(image)
        return self.classifier.predictBoard(boardImage, filterEmptyTiles=True)

    @retry(times=3, exceptions=(InvalidMove), callback=rerunAfterCorrection)
    def _updateEngine(self) -> None:
        boardState = self._analyseBoard()
        self.engine.update(boardState)

if __name__ == "__main__":
    import logging
    from pathlib import Path
    from aiBoardGame.robot import RobotArm, RobotArmException

    try:
        cameraIntrinsics = Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz")
        camera = RobotCamera(feedInput=2, resolution=(1920, 1080), intrinsicsFile=cameraIntrinsics)

        classifierWeights = Path("/home/Menta/Workspace/Projects/AI-boardgame/newModelParams.pt")
        device = XiangqiPieceClassifier.getAvailableDevice()
        classifier = XiangqiPieceClassifier(weights=classifierWeights, device=device)

        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=500_000)
        robotArm.connect()

        game = Xiangqi(camera=camera, classifier=classifier, robotArm=robotArm, difficulty=Difficulty.Medium)

        game.play()

        robotArm.disconnect()
    except (CameraError, RobotArmException, GameplayError) as error:
        logging.error(str(error))
