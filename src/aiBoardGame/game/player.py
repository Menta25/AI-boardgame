"""Player module for making moves"""

# pylint: disable=no-name-in-module, no-member, unnecessary-pass

from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, Optional, ClassVar
from abc import ABC, abstractmethod
import numpy as np
import cv2 as cv
from PyQt6.QtCore import pyqtSignal, QObject

from aiBoardGame.logic import FairyStockfish, Difficulty, Position
from aiBoardGame.robot import RobotArm, RobotArmException
from aiBoardGame.vision import RobotCamera, BoardImage, CameraError

from aiBoardGame.game.utility import retry, rerunAfterCorrection, utils, FinalMeta


@dataclass(frozen=True)
class PlayerError(Exception):
    """Exception for player errors"""
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class Player(QObject, ABC, metaclass=FinalMeta):
    """Abstract base class of all player classes"""
    isConceding: bool = field(default=False, init=False)
    """Has player conceded in game"""

    def __post_init__(self) -> None:
        super().__init__()

    @abstractmethod
    def prepare(self) -> None:
        """Prepare to play game

        :raises NotImplementedError: Method has not been implemented in subclass
        """
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented prepare() method")

    @abstractmethod
    def makeMove(self, fen: str) -> None:
        """Make move on board

        :param fen: Game state to make move decision on
        :type fen: str
        :raises NotImplementedError: Method has not been implemented in subclass
        """
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented getPossibleMoves() method")


@dataclass
class TerminalPlayer(Player):
    """Player class for playing in a terminal"""
    move: Optional[Tuple[Position, Position]] = field(default=None, init=False)
    """Last valid move typed in terminal"""


@dataclass(init=False)
class HumanTerminalPlayer(TerminalPlayer):
    """Human player class for playing in a terminal"""
    def prepare(self) -> None:
        """Prepare to play game
        """
        input("Press ENTER if you are ready to start the game")

    def makeMove(self, fen: str) -> None:
        """Make move on board

        :param fen: Game state to make move decision on
        :type fen: str
        """
        while True:
            try:
                moveStr = input("Move (fromFile,fromRank toFile,toRank): ")
                moveStrParts = moveStr.split(" ")
                if len(moveStrParts) == 1 and moveStrParts[0] == "concede":
                    self.isConceding = True
                    break
                elif len(moveStrParts) == 2:
                    startPositionStrs = moveStrParts[0].split(",")
                    endPositionStrs = moveStrParts[1].split(",")
                    if len(startPositionStrs) == 2 and len(endPositionStrs) == 2:
                        start = Position(int(startPositionStrs[0]), int(startPositionStrs[1]))
                        end = Position(int(endPositionStrs[0]), int(endPositionStrs[1]))
                        self.move = (start, end)
                        break
            except ValueError:
                pass


@dataclass
class HumanPlayer(Player):
    """Human player class for playing in real life"""
    prepareStarted: pyqtSignal = field(default=pyqtSignal(), init=False)
    """Signal emitted when player is preparing"""
    makeMoveStarted: pyqtSignal = field(default=pyqtSignal(), init=False)
    """Signal emitted when player has to make a move"""

    def prepare(self) -> None:
        """Prepare to play game
        """
        self.prepareStarted.emit()
        utils.pauseRun()

    def makeMove(self, fen: str) -> None:
        """Make move on board

        :param fen: Game state to make move decision on
        :type fen: str
        """
        self.makeMoveStarted.emit()
        utils.pauseRun()


@dataclass(init=False)
class RobotPlayer(Player):
    """Robot player class base"""
    stockfish: FairyStockfish
    """Stockfish to generate moves"""

    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM) -> None:
        """Constructs a RobotPlayer object

        :param difficulty: Quality of generated moves, defaults to Difficulty.MEDIUM
        :type difficulty: Difficulty, optional
        """
        super().__init__()
        self.stockfish = FairyStockfish(difficulty=difficulty)

    @property
    def difficulty(self) -> Difficulty:
        """Quality of generated moves"""
        return self.stockfish.difficulty

    @difficulty.setter
    def difficulty(self, value: Difficulty) -> None:
        self.stockfish.difficulty = value


@dataclass(init=False)
class RobotTerminalPlayer(RobotPlayer, TerminalPlayer):
    """Robot player class for playing in a terminal"""
    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM) -> None:
        RobotPlayer.__init__(self, difficulty)
        TerminalPlayer.__init__(self)

    def prepare(self) -> None:
        """Prepare to play game
        """
        pass

    def makeMove(self, fen: str) -> None:
        """Make move on board

        :param fen: Game state to make move decision on
        :type fen: str
        """
        self.move = self.stockfish.nextMove(fen=fen)
        if self.move is None:
            self.isConceding = True


@dataclass(init=False)
class RobotArmPlayer(RobotPlayer):
    """Robot arm player for playing in real life"""
    arm: RobotArm
    """Robot arm to move pieces on board"""
    camera: RobotCamera
    """Camera to detect pieces"""
    cornerCartesians: Optional[np.ndarray]
    """Board coordinates"""

    calibrateCorner: pyqtSignal = pyqtSignal(str)
    """Signal emitted when robot arm needs to be moved to corner"""
    loadLastCalibration: pyqtSignal = pyqtSignal()
    """Signal emitted when deciding to load last calibration"""

    _loaded: bool

    _baseCalibPath: ClassVar[Path] = Path("src/aiBoardGame/robotArmCalib.npz")

    def __init__(self, arm: RobotArm, camera: RobotCamera, difficulty: Difficulty = Difficulty.MEDIUM) -> None:
        """Constructs a RobotArmPlayer object

        :param arm: Robot arm to move pieces on board
        :type arm: RobotArm
        :param camera: Camera to detect pieces
        :type camera: RobotCamera
        :param difficulty: Quality of generated moves, defaults to Difficulty.MEDIUM
        :type difficulty: Difficulty, optional
        :raises PlayerError: Camera is not calibrated
        """
        if not camera.isCalibrated:
            raise PlayerError(f"Camera is not calibrated, cannot use it in {self.__class__.__name__}")

        super().__init__(difficulty)
        self.arm = arm
        self.camera = camera
        self.cornerCartesians = None

        self._loaded = False

    def prepare(self) -> None:
        """Prepare to play game

        :raises PlayerError: Cannot connect robot arm
        """
        if not self.arm.isConnected:
            try:
                self.arm.connect()
            except RobotArmException as exception:
                raise PlayerError(f"Cannot connect robot arm, failed to prepare {self.__class__.__name__}") from exception
        elif not self.camera.isActive:
            self.camera.activate()
        self._calibrate()

    @retry(times=1, exceptions=(RobotArmException, CameraError, RuntimeError), callback=rerunAfterCorrection)
    def makeMove(self, fen: str) -> None:
        """Make move on board

        :param fen: Game state to make move decision on
        :type fen: str
        :raises RuntimeError: Generated move piece not found on board
        """
        move = self.stockfish.nextMove(fen=fen)
        if move is not None:
            fromMove, toMove = move

            image = self.camera.read(undistorted=True)
            boardImage = self.camera.detectBoard(image)
            matrix = self._calculateAffineTransform(boardImage)

            capturedPiece = boardImage.findPiece(toMove)
            if capturedPiece is not None:
                capturedPieceCartesian = self._imageToRobotCartesian(capturedPiece[:2].astype(int), matrix)
                self._pickUpPiece(capturedPieceCartesian)
                self._capturePiece()

            movingPiece = boardImage.findPiece(fromMove)
            if movingPiece is None:
                raise RuntimeError

            fromMovingPieceCartesian = self._imageToRobotCartesian(movingPiece[:2].astype(int), matrix)
            toMovingPieceCartesian = self._imageToRobotCartesian(boardImage.positions[toMove.file, toMove.rank], matrix)

            self._pickUpPiece(fromMovingPieceCartesian)
            self._putDownPiece(toMovingPieceCartesian)

            self.arm.reset(safe=True)
        else:
            self.isConceding = True

    def _moveToPosition(self, position: np.ndarray) -> None:
        x, y = position
        self.arm.move(position=(x, y, None), safe=True, isCartesian=True)
        self.arm.lowerDown()

    def _pickUpPiece(self, position: np.ndarray) -> None:
        self._moveToPosition(position)
        self.arm.setPump(on=True)

    def _putDownPiece(self, position: np.ndarray) -> None:
        self._moveToPosition(position)
        self.arm.setPump(on=False)

    def _capturePiece(self) -> None:
        self.arm.reset(safe=True)
        capturedPieceDropHeight = 4*RobotArm.freeMoveHeightLimit
        self.arm.moveVertical(height=capturedPieceDropHeight)
        self.arm.moveHorizontal(stretch=self.arm.resetPosition[0]+100.0, rotation=self.arm.resetPosition[1])
        self.arm.setPump(on=False)
        self.arm.reset(safe=False)

    def _calibrate(self) -> None:
        if self._baseCalibPath.exists():
            self.loadLastCalibration.emit()
            utils.pauseRun()

        if not self._loaded:
            self.arm.detach(safe=True)
            cartesians = []
            for corner in ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"]:
                self.arm.detach(safe=False)
                self.calibrateCorner.emit(corner)
                utils.pauseRun()
                self.arm.attach()
                cartesians.append(self.arm.position)
            self.cornerCartesians = np.asarray(cartesians)[:,:2]
            np.savez(self._baseCalibPath, cornerCartesians=self.cornerCartesians)
        else:
            self._loaded = False
        self.arm.reset(safe=True)

    def loadCalibration(self) -> None:
        """Load robot arm calibration
        """
        with np.load(self._baseCalibPath, mmap_mode="r") as calibration:
            self.cornerCartesians = calibration["cornerCartesians"]
            self._loaded = True

    def _calculateAffineTransform(self, boardImage: BoardImage) -> np.ndarray:
        boardImageCorners = np.asarray([
            boardImage.positions[0,-1],
            boardImage.positions[-1,-1],
            boardImage.positions[-1,0],
            boardImage.positions[0,0]
        ], dtype=np.float64)
        return cv.estimateAffine2D(boardImageCorners, self.cornerCartesians)[0]

    def _imageToRobotCartesian(self, imageCartesian: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        return imageCartesian @ matrix[:,:2] + matrix[:, -1:].squeeze()
        