import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, Tuple, Optional, Dict
from PyQt6.QtCore import pyqtSignal, QObject

from aiBoardGame.logic import XiangqiEngine, InvalidMove, Board, Side, Difficulty, prettyBoard, Position
from aiBoardGame.vision import RobotCamera, CameraError, XiangqiPieceClassifier, BoardImage
from aiBoardGame.robot import RobotArm, RobotArmException

from aiBoardGame.game.player import Player, HumanPlayer, RobotArmPlayer, HumanTerminalPlayer, RobotTerminalPlayer, PlayerError
from aiBoardGame.game.utility import retry, rerunAfterCorrection, utils, FinalMeta


@dataclass(frozen=True)
class GameplayError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message

class XiangqiBase(ABC, QObject, metaclass=FinalMeta):
    def __init__(self, redSide: Player, blackSide: Player) -> None:
        ABC.__init__(self)
        QObject.__init__(self)
        self.sides: Dict[Side, Player] = {Side.Red: redSide, Side.Black: blackSide}
        self._engine = XiangqiEngine()
        self._turn = 0

        self.turnChanged = pyqtSignal(int)
        self.engineUpdated = pyqtSignal(str)
        self.over = pyqtSignal(Side, Player)

    @property
    def turn(self) -> int:
        return self._turn

    @turn.setter
    def turn(self, value: int) -> None:
        self._turn = value
        self.turnChanged.emit(value)

    @property
    def redSide(self) -> Player:
        return self.sides[Side.Red]

    @property
    def blackSide(self) -> Player:
        return self.sides[Side.Black]

    @property
    def currentSide(self) -> Side:
        return self._engine.currentSide

    @property
    def currentPlayer(self) -> Player:
        return self.sides[self.currentSide]

    @property
    def isOver(self) -> bool:
        return self._engine.isOver or any([player.isConceding for player in self.sides.values()])

    @property
    def winner(self) -> Optional[Tuple[Side, Player]]:
        if self._engine.isOver:
            winnerSide = self._engine.winner
            return winnerSide, self.sides[winnerSide]
        elif self.redSide.isConceding:
            return Side.Black, blackSide
        elif self.blackSide.isConceding:
            return Side.Red, redSide
        else:
            return None


    def _prepare(self) -> None:
        try:
            self._engine.newGame()
            self.engineUpdated.emit(self._engine.FEN)
            self.turn = 0
            for player in self.sides.values():
                player.prepare()
        except PlayerError as error:
            raise GameplayError(str(error))

    def play(self) -> None:
        self._prepare()
        text = "Starting game"
        logging.info(text)
        utils.statusUpdate.emit(text)
        moves = 0
        while not self.isOver:
            if moves % 2 == 0:
                self.turn += 1
                logging.info("")
                logging.info(f"Turn {self.turn}.")
                logging.info("")
            try:
                self.currentPlayer.makeMove(self._engine.FEN)
                if not self.currentPlayer.isConceding:
                    self._updateEngine()
                    if self._engine.isCurrentPlayerChecked:
                        text = f"{self.currentSide} {self.currentPlayer} is in check!"
                        logging.info(text)
                        utils.statusUpdate.emit(text)
                else:
                    text = f"{self.currentPlayer.__class__.__name__} has conceded"
                    logging.info(text)
                    utils.statusUpdate.emit(text)
            except InvalidMove as error:
                self._handleInvalidMove(error)
            else:
                moves += 1
                self.engineUpdated(self._engine.FEN)
        side, player = self.winner
        logging.info(f"The game has ended, {side.name} {player.__class__.__name__} has won")
        self.over.emit(side, player)

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

        self.newBoardImage = pyqtSignal(BoardImage)
        self.invalidStartPosition = pyqtSignal(Board)
        self.invalidMove = pyqtSignal(str, str)

    def _prepare(self) -> None:
        if not self._camera.isActive:
            self._camera.activate()
        
        super()._prepare()
        while (board := self._analyseBoard()) != self._engine.board:
            logging.error(prettyBoard(board, colors=True))
            self.invalidStartPosition.emit(board)
            utils.event.set()


    @retry(times=3, exceptions=(InvalidMove))
    def _updateEngine(self) -> None:
        board = self._analyseBoard()
        logging.debug(prettyBoard(board, colors=True))
        self._engine.update(board)

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> Board:
        image = self._camera.read(undistorted=True)
        boardImage = self._camera.detectBoard(image)
        self.newBoardImage.emit(boardImage)
        return self._classifier.predictBoard(boardImage)

    def _handleInvalidMove(self, error: InvalidMove) -> None:
        logging.info("Engine state:")
        logging.info(prettyBoard(self._engine.board, colors=True))
        if isinstance(self.currentPlayer, RobotArmPlayer):
            while True:
                try:
                    logging.error(str(error))
                    self.invalidMove.emit(str(error), self._engine.FEN)
                    utils.event.set()
                    self._updateEngine()
                except InvalidMove as newError:
                    logging.error(str(newError))
        else:
            logging.error(str(error))
            utils.statusUpdate.emit(str(error))


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="")

    try:
        cameraIntrinsics = Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz")
        camera = RobotCamera(feedInput=0, resolution=(1920, 1080), interval=0.1, intrinsicsFile=cameraIntrinsics)
        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=500_000)

        camera.activate()
        robotArm.connect()

        redSide = HumanPlayer()
        blackSide = RobotArmPlayer(arm=robotArm, camera=camera, difficulty=Difficulty.Medium)

        game = Xiangqi(camera=camera, redSide=redSide, blackSide=blackSide)
        game.play()

        robotArm.disconnect()
        camera.deactivate()
    except (CameraError, RobotArmException, GameplayError, PlayerError) as error:
        logging.error(str(error))

    # try:
    #     redSide = HumanTerminalPlayer()
    #     blackSide = RobotTerminalPlayer(difficulty=Difficulty.Easy)

    #     game = TerminalXiangqi(redSide=redSide, blackSide=blackSide)
    #     game.play()
    # except GameplayError as error:
    #     logging.error(str(error))
