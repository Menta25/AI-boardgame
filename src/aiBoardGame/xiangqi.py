import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, Tuple, Optional

from aiBoardGame.logic import XiangqiEngine, InvalidMove, Board, Side, Difficulty, prettyBoard, Position
from aiBoardGame.vision import RobotCamera, CameraError, XiangqiPieceClassifier
from aiBoardGame.robot import RobotArm, RobotArmException

from aiBoardGame.player import Player, HumanPlayer, RobotArmPlayer, HumanTerminalPlayer, RobotTerminalPlayer
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
        logging.info("Starting game")
        moves = 0
        while not self._engine.isOver:
            if moves % 2 == 0:
                logging.info("")
                logging.info(f"Turn {moves//2}.")
                logging.info("")
            try:
                self.currentPlayer.makeMove(self._engine.FEN)
                if self.currentPlayer.isConceding:
                    logging.info(f"{self._engine.currentSide.name} {self.currentPlayer.__class__.__name__} has conceded")
                    break
                self._updateEngine()
            except InvalidMove as error:
                self._handleInvalidMove(error)
            else:
                moves += 1
        logging.info("The game has ended")

    @abstractmethod
    def _updateEngine(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented _updateEngine() method")

    @abstractmethod
    def _handleInvalidMove(self, error: InvalidMove) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented _handleInvalidMove() method")


class TerminalXiangqi(XiangqiBase):
    def __init__(self, redSide: Union[HumanTerminalPlayer, RobotTerminalPlayer], blackSide: Union[HumanTerminalPlayer, RobotTerminalPlayer]) -> None:
        super().__init__(redSide, blackSide)

    def _prepare(self) -> None:
        super()._prepare()
        logging.info("")
        logging.info(prettyBoard(self._engine.board, colors=True))
        logging.info("")

    def _updateEngine(self) -> None:
        move: Optional[Tuple[Position, Position]] = self.currentPlayer.move
        if move is None:
            raise InvalidMove(None, None, None, f"Cannot get {self.currentPlayer.__class__.__name__}'s last move")
        self._engine.move(*move)
        logging.info("")
        logging.info(prettyBoard(self._engine.board, colors=True, lastMove=move))
        logging.info("")

    def _handleInvalidMove(self, error: InvalidMove) -> None:
        logging.error(str(error))

class Xiangqi(XiangqiBase):
    def __init__(self, camera: RobotCamera, redSide: Union[HumanPlayer, RobotArmPlayer], blackSide: Union[HumanPlayer, RobotArmPlayer]) -> None:
        if not camera.isCalibrated:
            raise GameplayError("Camera is not calibrated, cannot play Xiangqi")
        super().__init__(redSide, blackSide)

        self._camera = camera
        self._classifier = XiangqiPieceClassifier(weights=XiangqiPieceClassifier.baseWeightsPath, device=XiangqiPieceClassifier.getAvailableDevice())

    def _prepare(self) -> None:
        if not self._camera.isActive:
            self._camera.activate()
        
        super()._prepare()
        self._analyseBoard()

    @retry(times=3, exceptions=(InvalidMove))
    def _updateEngine(self) -> None:
        board = self._analyseBoard()
        logging.info(prettyBoard(board, colors=True))
        self._engine.update(board)

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> Board:
        image = self._camera.read(undistorted=True)
        boardImage = self._camera.detectBoard(image)
        return self._classifier.predictBoard(boardImage)

    def _handleInvalidMove(self, error: InvalidMove) -> None:
        logging.error(str(error))
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
        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=100_000)

        camera.activate()
        robotArm.connect()

        redSide = HumanPlayer()
        blackSide = RobotArmPlayer(arm=robotArm, camera=camera, difficulty=Difficulty.Medium)

        game = Xiangqi(camera=camera, redSide=redSide, blackSide=blackSide)
        game.play()

        robotArm.disconnect()
        camera.deactivate()
    except (CameraError, RobotArmException, GameplayError) as error:
        logging.error(str(error))

    # try:
    #     redSide = RobotTerminalPlayer(difficulty=Difficulty.Hard)
    #     blackSide = RobotTerminalPlayer(difficulty=Difficulty.Medium)

    #     game = TerminalXiangqi(redSide=redSide, blackSide=blackSide)
    #     game.play()
    # except GameplayError as error:
    #     logging.error(str(error))
