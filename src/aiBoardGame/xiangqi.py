import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, Tuple

from aiBoardGame.logic import XiangqiEngine, InvalidMove, Board, Side, Difficulty, FairyStockfish
from aiBoardGame.vision import RobotCamera, CameraError, XiangqiPieceClassifier, BoardImage
from aiBoardGame.robot import RobotArm, RobotArmException

from aiBoardGame.player import HumanPlayer, RobotArmPlayer, Player
from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class GameplayError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message

class XiangqiBase(ABC):
    def __init__(self, redSide: Player, blackSide: Player) -> None:
        super().__init__()
        self.redSide = redSide
        self.blackSide = blackSide
        self._engine = XiangqiEngine()

    @property
    def sides(self) -> Tuple[Player, Player]:
        return self.redSide, self.blackSide

    @property
    def currentPlayer(self) -> Player:
        return self.redSide if self._engine.currentSide == Side.Red else self.blackSide

    def _prepare(self) -> None:
        for player in self.sides:
            player.prepare()

    def play(self) -> None:
        self._engine.newGame()
        self._prepare()
        while not self._engine.isOver:
            try:
                self.currentPlayer.makeMove(self._engine.FEN)
                self._updateEngine()
            except InvalidMove as error:
                logging.error(str(error))
                self._handleInvalidMove()

    @abstractmethod
    def _updateEngine(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented _updateEngine() method")

    @abstractmethod
    def _handleInvalidMove(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented _handleInvalidMove() method")

class Xiangqi(XiangqiBase):
    def __init__(self, camera: RobotCamera, redSide: Union[HumanPlayer, RobotArmPlayer], blackSide: Union[HumanPlayer, RobotArmPlayer]) -> None:
        if not self._camera.isCalibrated:
            raise GameplayError("Camera is not calibrated, cannot play Xiangqi")
        super().__init__(redSide, blackSide)

        self._camera = camera
        self._classifier = XiangqiPieceClassifier(weights=XiangqiPieceClassifier.baseWeightsPath, device=XiangqiPieceClassifier.getAvailableDevice())

    def _prepare(self) -> None:
        if not self._camera.isActive:
            self._camera.activate()
        
        super()._prepare()
        input("Press ENTER to start the game")
        self._analyseBoard()

    @retry(times=3, exceptions=(InvalidMove))
    def _updateEngine(self) -> None:
        board = self._analyseBoard()
        self._engine.update(board)

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> Board:
        image = self._camera.read(undistorted=True)
        boardImage = self._camera.detectBoard(image)
        return self._classifier.predictBoard(boardImage)

    def _handleInvalidMove(self) -> None:
        if isinstance(self.currentPlayer, RobotArmPlayer):
            while True:
                try:
                    input(f"The move made by the previous robot player was invalid, please rectify the board, then press ENTER")
                    self._updateEngine()
                except InvalidMove as error:
                    logging.error(str(error))


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="")

    try:
        cameraIntrinsics = Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz")
        camera = RobotCamera(feedInput=2, resolution=(1920, 1080), interval=0.1, intrinsicsFile=cameraIntrinsics)
        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=500_000)

        camera.activate()
        robotArm.connect()

        redSide = HumanPlayer()
        blackSide = RobotArmPlayer(arm=robotArm, difficulty=Difficulty.Medium)

        game = Xiangqi(camera=camera, redSide=redSide, blackSide=blackSide)
        game.play()

        robotArm.disconnect()
        camera.deactivate()
    except (CameraError, RobotArmException, GameplayError) as error:
        logging.error(str(error))
