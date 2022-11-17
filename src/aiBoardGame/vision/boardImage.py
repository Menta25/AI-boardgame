from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from typing import ClassVar, Tuple, Union
from dataclasses import dataclass, field

from aiBoardGame.logic.engine import Board, Position


_boardLogger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoardImage:
    """A game board represented by a ndarray"""
    data: np.ndarray

    positions: np.ndarray = field(init=False)

    fileStep: np.float64 = field(init=False)
    rankStep: np.float64 = field(init=False)
    tileSize: np.ndarray = field(init=False)

    offsetMultiplier: ClassVar[float] = 1.2

    def __post_init__(self) -> None:
        imageHSV = cv.cvtColor(self.data, cv.COLOR_BGR2HSV)
        offsetHSV = np.array([10,80,80], np.uint8)
        boardHSV = np.array([15,89,153], np.uint8)
        boardMask = cv.inRange(imageHSV, boardHSV-offsetHSV, boardHSV+offsetHSV)

        erosionKernel = np.ones((5, 5), np.uint8)
        erosion = cv.erode(boardMask, erosionKernel, iterations=3)

        boardContours, _ = cv.findContours(erosion, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        x, y, width, height = cv.boundingRect(np.vstack(boardContours))

        fileStep = int(width / Board.fileCount)
        rankStep = int(height / Board.rankCount)
        tileSize = (np.array([fileStep, rankStep]) * self.offsetMultiplier).astype(np.uint16)

        files = np.linspace(x, x+width, num=Board.fileCount+1, dtype=np.uint16)[:-1] + int(fileStep/2)
        ranks = np.linspace(y, y+height, num=Board.rankCount+1, dtype=np.uint16)[:-1] + int(rankStep/2)

        files = np.repeat(files[:, np.newaxis], Board.rankCount, 1)
        ranks = np.repeat(ranks[np.newaxis, :], Board.fileCount, 0)

        positions = np.dstack((files, ranks))

        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "fileStep", fileStep)
        object.__setattr__(self, "rankStep", rankStep)
        object.__setattr__(self, "tileSize", tileSize)

        _boardLogger.info(f"Created Board from {self.data.shape} array")

    @property
    def tiles(self) -> np.ndarray:
        return np.array([[self._tile(tileCenter) for tileCenter in file[::-1]] for file in self.positions])

    def tile(self, position: Position) -> np.ndarray:
        """Return the given tile's ndarray representation"""
        imagePosition: np.ndarray = self.positions[position.file, Board.rankCount-1 - position.rank]
        return self._tile(imagePosition)

    def _tile(self, tileCenter: np.ndarray) -> np.ndarray:
        topLeftCorner = (tileCenter - self.tileSize/2).astype(np.uint16)
        bottomRightCorner = (tileCenter + self.tileSize/2).astype(np.uint16)
        return self.data[topLeftCorner[1]:bottomRightCorner[1], topLeftCorner[0]:bottomRightCorner[0]]

    def __getitem__(self, key: Union[Position, Tuple[int, int]]) -> np.ndarray:
        if isinstance(key, tuple):
            key = Position(*key)
        if isinstance(key, Position):
            return self.tile(key)
        else:
            raise TypeError(f"Key has invalid type {key.__class__.__name__}")

    @property
    def roi(self) -> np.ndarray:
        topLeftCorner = (self.positions[0,0] - self.tileSize/2).astype(np.uint16)
        bottomRightCorner = (self.positions[-1,-1] + self.tileSize/2).astype(np.uint16)
        return self.data[topLeftCorner[1]:bottomRightCorner[1], topLeftCorner[0]:bottomRightCorner[0]]

    # NOTE: Obsolete
    def _pieces(self) -> np.ndarray:
        blurredBoard = cv.medianBlur(self.data, 5)
        grayBlurredBoard = cv.cvtColor(blurredBoard, cv.COLOR_BGR2GRAY)

        pieces = cv.HoughCircles(grayBlurredBoard, cv.HOUGH_GRADIENT, dp=1.5, minDist=int(self.fileStep-self.fileStep/10), param1=30, param2=46, minRadius=int(self.fileStep/2 - self.fileStep/10), maxRadius=int(self.fileStep/2 + self.fileStep/10))
        if pieces is None:
            print("No piece found")
            return

        return pieces[0,:].astype(np.uint16)

    def showPieces(self) -> None:
        dataCopy = self.data.copy()
        for piece in self._pieces():
            center = piece[0:2]
            radius = piece[2]
            cv.circle(dataCopy, center, 2, (0,0,255), 3)
            cv.circle(dataCopy, center, radius, (0,255,0), 3)

        cv.imshow("pieces", dataCopy)
        cv.waitKey(0)

if __name__ == "__main__":
    import time
    from pathlib import Path
    from aiBoardGame.vision.xiangqiPieceClassifier import XiangqiPieceClassifier
    
    from aiBoardGame.logic.engine.utility import boardToStr

    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board/board5.jpg")
    boardImage = BoardImage(data=cv.imread(boardImagePath.as_posix()).copy())

    classifier = XiangqiPieceClassifier(Path("finalWeights.pt"))

    # from PIL import Image
    # from torchvision import transforms
    # tile = Image.fromarray(boardImage.tiles[8,9][...,::-1])
    # print(classifier.predict(transforms.ToTensor()(tile)))

    start = time.time()
    tiles = boardImage.tiles
    board = classifier.predictTiles(tiles)
    print(f"predict time: {time.time() - start:.4f}s")

    print(boardToStr(board))

    cv.imshow("roi", boardImage.roi)
    cv.waitKey(0)

    # tiles = boardImage.tiles
    # for rank in range(Board.rankCount):
    #     for file in range(Board.fileCount):
    #         cv.imshow(f"({file},{rank})", tiles[file][rank])
    #         cv.waitKey(0)
    #         cv.destroyAllWindows()

    # cv.imshow(f"{classifier.predictTile(boardImage[7,5])}", boardImage[7,5])
    # cv.waitKey(0)

    boardImage.showPieces()

    cv.destroyAllWindows()