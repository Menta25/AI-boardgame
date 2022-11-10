from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from typing import ClassVar, Tuple, Union
from dataclasses import dataclass, field

from aiBoardGame.logic.auxiliary import Board, Position

_boardLogger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoardImage:
    """A game board represented by a ndarray"""
    data: np.ndarray

    corners: np.ndarray = field(init=False)
    positions: np.ndarray = field(init=False)

    fileStep: np.float64 = field(init=False)
    rankStep: np.float64 = field(init=False)
    tileSize: np.ndarray = field(init=False)

    offsetMultiplier: ClassVar[float] = 1.15

    def __post_init__(self) -> None:
        imageHSV = cv.cvtColor(self.data, cv.COLOR_BGR2HSV)
        offsetHSV = np.array([5,80,80], np.uint8)
        boardHSV = np.array([15,89,153], np.uint8)
        boardMask = cv.inRange(imageHSV, boardHSV-offsetHSV, boardHSV+offsetHSV)

        erosionKernel = np.ones((5, 5), np.uint8)
        erosion = cv.erode(boardMask, erosionKernel, iterations=3)

        boardContours, _ = cv.findContours(erosion, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        x, y, width, height = cv.boundingRect(np.vstack(boardContours))

        fileStep = width / Board.fileCount
        rankStep = height / Board.rankCount

        files = np.linspace(fileStep, width, num=Board.fileCount) + (x - fileStep/2)
        ranks = np.linspace(rankStep, height, num=Board.rankCount) + (y - rankStep/2)

        files = files.astype(np.uint16)
        ranks = ranks.astype(np.uint16)

        files = np.repeat(files[np.newaxis, :], Board.rankCount, 0)
        ranks = np.repeat(ranks[:, np.newaxis], Board.fileCount, 1)

        positions = np.dstack((files, ranks))

        corners = np.array([
            np.array([x, y]),
            np.array([x+width, y+height])
        ])

        tileSize = np.array([fileStep, rankStep], dtype=np.float64) * self.offsetMultiplier

        object.__setattr__(self, "corners", corners)
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "fileStep", fileStep)
        object.__setattr__(self, "rankStep", rankStep)
        object.__setattr__(self, "tileSize", tileSize)

        _boardLogger.info(f"Created Board from {self.data.shape} array")

    # @property
    # def tiles(self) -> np.ndarray:
    #     topLeftCorner = np.around(self.positions[0,0] - self.tileSize/2).astype(int)
    #     bottomRightCorner = np.around(self.positions[-1,-1] + self.tileSize/2).astype(int)

    #     tileShape = np.around(np.append(self.tileSize[::-1], [3])).astype(int)
    #     tilesRoi = self.data[topLeftCorner[1]:bottomRightCorner[1], topLeftCorner[0]-1:bottomRightCorner[0]]

    #     rawTiles = np.lib.stride_tricks.sliding_window_view(tilesRoi, tileShape)[::round(self.rankStep),::round(self.fileStep)]

    #     return np.flip(rawTiles.squeeze(2).swapaxes(0,1), 1)

    @property
    def tiles(self) -> np.ndarray:
        for file in self.positions:
            for tileCenter in file:
                topLeftCorner = np.around(tileCenter - self.tileSize/2).astype(int)
                bottomRightCorner = np.around(tileCenter + self.tileSize/2).astype(int)



        tileShape = np.around(np.append(self.tileSize[::-1], [3])).astype(int)
        tilesRoi = self.data[topLeftCorner[1]:bottomRightCorner[1], topLeftCorner[0]-1:bottomRightCorner[0]]

        rawTiles = np.lib.stride_tricks.sliding_window_view(tilesRoi, tileShape)[::int(self.rankStep),::int(self.fileStep)]

        return np.flip(rawTiles.squeeze(2).swapaxes(0,1), 1)

    def tile(self, position: Position) -> np.ndarray:
        """Return the given tile's ndarray representation"""
        imagePosition: np.ndarray = self.positions[position.file, Board.rankCount-1 - position.rank]

        topLeftCorner = np.around(imagePosition - self.tileSize/2).astype(int)
        bottomRightCorner = np.around(imagePosition + self.tileSize/2).astype(int)

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
        return self.data[self.corners[0][1]:self.corners[-1][1], self.corners[0][0]:self.corners[-1][0]]

    # NOTE: Obsolete
    def pieces(self) -> np.ndarray:
        blurredBoard = cv.medianBlur(self.data, 5)
        grayBlurredBoard = cv.cvtColor(blurredBoard, cv.COLOR_BGR2GRAY)

        pieces = cv.HoughCircles(grayBlurredBoard, cv.HOUGH_GRADIENT, dp=1.5, minDist=self.tileWidth, param1=30, param2=46, minRadius=int(self.tileWidth/2 - self.tileWidth/10), maxRadius=int(self.tileWidth/2 + self.tileWidth/10))
        if pieces is None:
            print("No piece found")
            return

        pieces = np.uint16(np.around(pieces))
        return pieces[0,:]


if __name__ == "__main__":
    import time
    from pathlib import Path
    from aiBoardGame.vision.xiangqiPieceClassifier import XiangqiPieceClassifier
    
    from aiBoardGame.logic.utility import boardToStr

    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/board0.jpg")
    boardImage = BoardImage(data=cv.imread(boardImagePath.as_posix()).copy())

    classifier = XiangqiPieceClassifier(Path("newModelParams.pt"))

    # from PIL import Image
    # from torchvision import transforms
    # tile = Image.fromarray(boardImage.tiles[8,9][...,::-1])
    # print(classifier.predict(transforms.ToTensor()(tile)))

    start = time.time()
    tiles = boardImage.tiles
    board = classifier.predictTiles(tiles)
    print(f"predict time: {time.time() - start:.4f}s")

    print(boardToStr(board))

    # tiles = boardImage.tiles
    # for rank in range(Board.rankCount):
    #     for file in range(Board.fileCount):
    #         cv.imshow(f"({file},{rank})", tiles[file][rank])
    #         cv.waitKey(0)

    cv.destroyAllWindows()