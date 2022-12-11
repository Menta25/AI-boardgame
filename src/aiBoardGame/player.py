import logging
import numpy as np
import cv2 as cv
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, ClassVar
from abc import ABC, abstractmethod

from aiBoardGame.logic import FairyStockfish, Difficulty, Position
from aiBoardGame.robot import RobotArm, RobotArmException
from aiBoardGame.vision import RobotCamera, BoardImage

from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass
class Player(ABC):
    @abstractmethod
    def prepare(self) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented prepare() method")

    @abstractmethod
    def makeMove(self, fen: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented getPossibleMoves() method")


@dataclass
class TerminalPlayer(Player):
    move: Optional[Tuple[Position, Position]] = None


@dataclass
class HumanPlayer(Player):
    def prepare(self) -> None:
        pass

    def makeMove(self, fen: str) -> None:
        input("Press ENTER if you want to finish your turn...")


@dataclass
class HumanTerminalPlayer(HumanPlayer, TerminalPlayer):
    def makeMove(self, fen: str) -> None:
        logging.info(fen)  # TODO: Print board
        while True:
            try:
                moveStr = input("Move (fromFile,fromRank toFile,toRank): ")
                moveStrParts = moveStr.split(" ")
                if len(moveStrParts) == 2:
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


@dataclass(init=False)
class RobotArmPlayer(RobotPlayer):
    arm: RobotArm
    camera: RobotCamera
    cornerCoordinates: Optional[np.ndarray]

    _baseCalibPath: ClassVar[Path] = Path("src/aiBoardGame/robotArmCalib.npz")

    def __init__(self, arm: RobotArm, difficulty: Difficulty = Difficulty.Medium) -> None:
        super().__init__(difficulty)
        self.arm = arm
        self.cornerCoordinates = None

    def prepare(self) -> None:
        if not self.arm.isConnected:
            self.arm.connect()
        self._calibrate()

    @retry(times=1, exceptions=(RobotArmException, RuntimeError), callback=rerunAfterCorrection)
    def makeMove(self, fen: str) -> None:
        fromMove, toMove = self.stockfish.nextMove(fen=fen)
        logging.debug(f"Stockfish move: {*fromMove,} -> {*toMove,}")

        piece = lastBoardInfo[0].findPiece(fromMove)
        if piece is None:
            raise RuntimeError

        matrix = self._calculateAffineTransform(lastBoardInfo[0])
        fromMove = self._imageToRobotCoordinate(piece[:2], matrix)
        toMove = self._imageToRobotCoordinate(lastBoardInfo[0].positions[toMove.file, toMove.rank], matrix)

        self.arm.moveOnBoard(*fromMove)
        self.arm.setPump(on=True)
        self.arm.moveOnBoard(*toMove)
        self.arm.setPump(on=False)

        self.arm.resetPosition(lowerDown=False, safe=True)

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
        