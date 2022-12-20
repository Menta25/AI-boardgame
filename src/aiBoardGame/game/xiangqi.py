# pylint: disable=no-name-in-module

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
    turnChanged = pyqtSignal(int)
    engineUpdated = pyqtSignal(str)
    over = pyqtSignal(Side, Player)

    def __init__(self, redSide: Player, blackSide: Player) -> None:
        ABC.__init__(self)
        QObject.__init__(self)
        self.sides: Dict[Side, Player] = {Side.RED: redSide, Side.BLACK: blackSide}
        self._engine = XiangqiEngine()
        self._turn = 0


    @property
    def turn(self) -> int:
        return self._turn

    @turn.setter
    def turn(self, value: int) -> None:
        self._turn = value
        self.turnChanged.emit(value)

    @property
    def redSide(self) -> Player:
        return self.sides[Side.RED]

    @property
    def blackSide(self) -> Player:
        return self.sides[Side.BLACK]

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
            return Side.BLACK, black
        elif self.blackSide.isConceding:
            return Side.RED, red
        else:
            return None


    def _prepare(self) -> None:
        try:
            self._engine.newGame()
            self.engineUpdated.emit(self._engine.fen)
            self.turn = 0
            for player in self.sides.values():
                player.prepare()
        except PlayerError as error:
            raise GameplayError(str(error)) from error

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
                logging.info(f"Turn {self.turn}")
                logging.info("")
            try:
                self.currentPlayer.makeMove(self._engine.fen)
                if not self.currentPlayer.isConceding:
                    self._updateEngine()
                    if self._engine.isCurrentPlayerChecked:
                        text = f"{self.currentSide.name} {self.currentPlayer.__class__.__name__} is in check!"
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
                self.engineUpdated.emit(self._engine.fen)
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
    newBoardImage = pyqtSignal(BoardImage)
    invalidStartPosition = pyqtSignal(Board)
    invalidMove = pyqtSignal(str, str)

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
        while (board := self._analyseBoard()) != self._engine.board:
            logging.error(f"\n{prettyBoard(board, colors=True)}")
            self.invalidStartPosition.emit(board)
            utils.pauseRun()


    @retry(times=3, exceptions=(InvalidMove))
    def _updateEngine(self) -> None:
        board = self._analyseBoard()
        logging.debug(f"\n{prettyBoard(board, colors=True)}")
        self._engine.update(board)

    @retry(times=3, exceptions=(CameraError), callback=rerunAfterCorrection)
    def _analyseBoard(self) -> Board:
        image = self._camera.read(undistorted=True)
        boardImage = self._camera.detectBoard(image)
        self.newBoardImage.emit(boardImage)
        return self._classifier.predictBoard(boardImage)

    def _handleInvalidMove(self, error: InvalidMove) -> None:
        logging.info("Engine state:")
        logging.info(f"\n{prettyBoard(self._engine.board, colors=True)}")
        if isinstance(self.currentPlayer, RobotArmPlayer):
            while True:
                try:
                    logging.error(str(error))
                    self.invalidMove.emit(str(error), self._engine.fen)
                    utils.pauseRun()
                    self._updateEngine()
                except InvalidMove as newError:
                    logging.error(str(newError))
                    utils.statusUpdate.emit(str(newError))
        else:
            logging.error(str(error))
            utils.statusUpdate.emit(str(error))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")

    try:
        cameraIntrinsics = Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz")
        cam = RobotCamera(feedInput=0, resolution=(1920, 1080), interval=0.1, intrinsicsFile=cameraIntrinsics)
        robotArm = RobotArm(hardwareID="USB VID:PID=2341:0042", speed=500_000)

        cam.activate()
        robotArm.connect()

        red = HumanPlayer()
        black = RobotArmPlayer(arm=robotArm, camera=cam, difficulty=Difficulty.MEDIUM)

        game = Xiangqi(camera=cam, redSide=red, blackSide=black)
        game.play()

        robotArm.disconnect()
        cam.deactivate()
    except (CameraError, RobotArmException, GameplayError, PlayerError) as exception:
        logging.error(str(exception))

    # try:
    #     red = HumanTerminalPlayer()
    #     black = RobotTerminalPlayer(difficulty=Difficulty.Easy)

    #     game = TerminalXiangqi(redSide=red, blackSide=black)
    #     game.play()
    # except GameplayError as exception:
    #     logging.error(str(exception))
