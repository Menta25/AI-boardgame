import logging
import numpy as np
import cv2 as cv
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, ClassVar
from abc import ABC, abstractmethod

from aiBoardGame.logic import FairyStockfish
from aiBoardGame.robot import RobotArm, RobotArmException
from aiBoardGame.vision import BoardImage

from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class Player(ABC):
    @abstractmethod
    def makeMove(self, lastBoardInfo: Tuple[BoardImage, str]) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented getPossibleMoves method")


@dataclass(frozen=True)
class HumanPlayer(Player):
    def makeMove(self, lastBoardInfo: Tuple[BoardImage, str]) -> None:
        input("Press any key if you want to finish your turn...")


@dataclass(frozen=True)
class RobotPlayer(Player):
    arm: RobotArm
    stockfish: FairyStockfish
    cornerCoordinates: Optional[np.ndarray] = None

    baseCalibPath: ClassVar[Path] = Path("src/aiBoardGame/robotArmCalib.npz")

    @retry(times=1, exceptions=(RobotArmException, RuntimeError), callback=rerunAfterCorrection)
    def makeMove(self, lastBoardInfo: Tuple[BoardImage, str]) -> None:
        fromMove, toMove = self.stockfish.nextMove(fen=lastBoardInfo[1])
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

    def calibrate(self) -> None:
        if self.baseCalibPath.exists() and input("Do you want to use last game's robot arm calibration? (yes/no) ") == "yes":
            with np.load(self.baseCalibPath, mmap_mode="r") as calibration:
                cornerCoordinates = calibration["cornerCoordinates"]
        else:
            self.arm.resetPosition(lowerDown=True, safe=True)
            coordinates = []
            for corner in ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"]:
                self.arm.detach(safe=False)
                input(f"Move robot arm to {corner} corner (from the view of RED side)")
                self.arm.attach()
                coordinates.append(self.arm.position)
            cornerCoordinates = np.asarray(coordinates)
            np.savez(self.baseCalibPath, cornerCoordinates=cornerCoordinates)
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
        