import logging
import numpy as np
import cv2 as cv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, Optional, ClassVar
from abc import ABC, abstractmethod

from aiBoardGame.logic import FairyStockfish, Difficulty, Position, prettyBoard
from aiBoardGame.robot import RobotArm, RobotArmException
from aiBoardGame.vision import RobotCamera, BoardImage, CameraError

from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class PlayerError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class Player(ABC):
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
class HumanPlayer(Player):
    def prepare(self) -> None:
        input("Press ENTER if you are ready to start the game")

    def makeMove(self, fen: str) -> None:
        command = input("Press ENTER if you want to finish your turn, or type \"concede\" if you want to concede")
        if command == "concede":
            self.isConceding = True


@dataclass
class HumanTerminalPlayer(HumanPlayer, TerminalPlayer):
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
    cornerCoordinates: Optional[np.ndarray]

    _baseCalibPath: ClassVar[Path] = Path("src/aiBoardGame/robotArmCalib.npz")

    def __init__(self, arm: RobotArm, camera: RobotCamera, difficulty: Difficulty = Difficulty.Medium) -> None:
        if not camera.isCalibrated:
            raise PlayerError(f"Camera is not calibrated, cannot use it in {self.__class__.__name__}")

        super().__init__(difficulty)
        self.arm = arm
        self.camera = camera
        self.cornerCoordinates = None

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
            logging.debug(f"Stockfish move: {*fromMove,} -> {*toMove,}")

            image = self.camera.read(undistorted=True)
            boardImage = self.camera.detectBoard(image)
            piece = boardImage.findPiece(fromMove)
            if piece is None:
                raise RuntimeError

            matrix = self._calculateAffineTransform(boardImage)
            fromMove = self._imageToRobotCoordinate(piece[:2], matrix)
            toMove = self._imageToRobotCoordinate(boardImage.positions[toMove.file, toMove.rank], matrix)

            self.arm.moveOnBoard(*fromMove)
            self.arm.setPump(on=True)
            self.arm.moveOnBoard(*toMove)
            self.arm.setPump(on=False)

            self.arm.resetPosition(lowerDown=False, safe=True)
        else:
            self.isConceding = True

    def _calibrate(self) -> None:
        if self._baseCalibPath.exists() and input("Do you want to use last game's robot arm calibration? (yes/no) ") == "yes":
            with np.load(self._baseCalibPath, mmap_mode="r") as calibration:
                cornerCoordinates = calibration["cornerCoordinates"]
        else:
            self.arm.resetPosition(lowerDown=True, safe=True)
            coordinates = []
            for corner in ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"]:
                self.arm.detach(safe=False)
                input(f"Move robot arm to {corner} corner (from the view of RED side), then press ENTER")
                self.arm.attach()
                coordinates.append(self.arm.position)
            cornerCoordinates = np.asarray(coordinates)
            np.savez(self._baseCalibPath, cornerCoordinates=cornerCoordinates)
        object.__setattr__(self, "cornerCoordinates", cornerCoordinates)
        self.arm.resetPosition(lowerDown=False, safe=True)

    def _calculateAffineTransform(self, boardImage: BoardImage) -> np.ndarray:
        boardImageCorners = np.asarray([
            boardImage.positions[0,0],
            boardImage.positions[0,-1],
            boardImage.positions[-1,-1],
            boardImage.positions[-1,0],
        ])
        return cv.estimateAffine2D(boardImageCorners, self.cornerCoordinates)

    def _imageToRobotCoordinate(self, imageCoordinate: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        return imageCoordinate @ matrix[:,:2] + matrix[:, -1:].squeeze()
        