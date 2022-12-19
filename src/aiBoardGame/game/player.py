import numpy as np
import cv2 as cv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, Optional, ClassVar
from abc import ABC, abstractmethod
from PyQt6.QtCore import pyqtSignal, QObject

from aiBoardGame.logic import FairyStockfish, Difficulty, Position
from aiBoardGame.robot import RobotArm, RobotArmException
from aiBoardGame.vision import RobotCamera, BoardImage, CameraError

from aiBoardGame.game.utility import retry, rerunAfterCorrection, utils, FinalMeta


@dataclass(frozen=True)
class PlayerError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class Player(ABC, QObject, metaclass=FinalMeta):
    isConceding: bool = field(default=False, init=False)

    @abstractmethod
    def prepare(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented prepare() method")

    @abstractmethod
    def makeMove(self, fen: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented getPossibleMoves() method")


@dataclass
class TerminalPlayer(Player):
    move: Optional[Tuple[Position, Position]] = field(default=None, init=False)


@dataclass
class HumanTerminalPlayer(TerminalPlayer):
    def prepare(self) -> None:
        input("Press ENTER if you are ready to start the game")

    def makeMove(self, fen: str) -> None:
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
    prepareStarted: pyqtSignal = field(default=pyqtSignal(), init=False)
    makeMoveStarted: pyqtSignal = field(default=pyqtSignal(), init=False)

    def prepare(self) -> None:
        self.prepareStarted.emit()
        utils.event.set()

    def makeMove(self, fen: str) -> None:
        self.makeMoveStarted.emit()
        utils.event.set()


@dataclass(init=False)
class RobotPlayer(Player):
    stockfish: FairyStockfish

    def __init__(self, difficulty: Difficulty = Difficulty.Medium) -> None:
        self.stockfish = FairyStockfish(difficulty=difficulty)

    @property
    def difficulty(self) -> Difficulty:
        return self.stockfish.difficulty

    @difficulty.setter
    def difficulty(self, value: Difficulty) -> None:
        self.stockfish.difficulty = value


@dataclass(init=False)
class RobotTerminalPlayer(RobotPlayer, TerminalPlayer):
    def __init__(self, difficulty: Difficulty = Difficulty.Medium) -> None:
        RobotPlayer.__init__(self, difficulty)
        TerminalPlayer.__init__(self)

    def prepare(self) -> None:
        pass

    def makeMove(self, fen: str) -> None:
        self.move = self.stockfish.nextMove(fen=fen)
        if self.move is None:
            self.isConceding = True


@dataclass(init=False)
class RobotArmPlayer(RobotPlayer):
    arm: RobotArm
    camera: RobotCamera
    cornerCartesians: Optional[np.ndarray]

    calibrateCorner: pyqtSignal = field(default=pyqtSignal(str), init=False)

    _baseCalibPath: ClassVar[Path] = Path("src/aiBoardGame/robotArmCalib.npz")

    def __init__(self, arm: RobotArm, camera: RobotCamera, difficulty: Difficulty = Difficulty.Medium) -> None:
        if not camera.isCalibrated:
            raise PlayerError(f"Camera is not calibrated, cannot use it in {self.__class__.__name__}")

        super().__init__(self, difficulty)
        self.arm = arm
        self.camera = camera
        self.cornerCartesians = None

    def prepare(self) -> None:
        if not self.arm.isConnected:
            try:
                self.arm.connect()
            except RobotArmException:
                raise PlayerError(f"Cannot connect robot arm, failed to prepare {self.__class__.__name__}")
        elif not self.camera.isActive:
            self.camera.activate()
        self._calibrate()

    @retry(times=1, exceptions=(RobotArmException, CameraError, RuntimeError), callback=rerunAfterCorrection)
    def makeMove(self, fen: str) -> None:
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
        self.arm.move(to=(x, y, None), safe=True, isCartesian=True)
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

    def calibrate(self) -> None:
        self.arm.resetPosition(lowerDown=True, safe=True)
        coordinates = []
        for corner in ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"]:
            self.arm.detach(safe=False)
            self.calibrateCorner.emit(corner)
            utils.event.set()
            self.arm.attach()
            coordinates.append(self.arm.position)
        self.robotArmCornerCoordinates = np.asarray(coordinates)
        object.__setattr__(self, "cornerCoordinates", coordinates)
        self.arm.resetPosition(lowerDown=False, safe=True)

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
        