from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from typing import ClassVar, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from aiBoardGame.logic.engine import Board, Position


_boardLogger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoardImage:
    """A game board represented by a ndarray"""
    data: np.ndarray

    _x: Optional[int] = None
    _y: Optional[int] = None
    _width: Optional[int] = None
    _height: Optional[int] = None

    positions: np.ndarray = field(init=False)

    fileStep: np.float64 = field(init=False)
    rankStep: np.float64 = field(init=False)
    tileSize: np.ndarray = field(init=False)

    tileSizeMultiplier: ClassVar[float] = 1.6
    pieceSizeMultiplier: ClassVar[float] = 1.2

    hsvRange: ClassVar[np.ndarray] = np.array([15,128,150])[np.newaxis,:] + np.array([[10,128,150], [10,127,100]]) * np.array([[-1],[1]])


    def __post_init__(self) -> None:
        if any([attribute is None for attribute in [self._x, self._y, self._width, self._height]]):
            x, y, width, height = self._fallbackBoardDetection(self.data)
        else:
            x, y, width, height = self._x, self._y, self._width, self._height

        # for corner in np.array([[x,y],[x+width,y],[x+width,y+height],[x,y+height]]):
        #     cv.circle(self.data, corner.astype(int), 2, (0,255,255),2)

        fileStep = int(width / Board.fileCount)
        rankStep = int(height / Board.rankCount)
        tileSize = (np.array([fileStep, rankStep]) * self.tileSizeMultiplier).astype(np.uint16)

        files = np.linspace(x, x+width, num=Board.fileCount+1, dtype=np.uint16)[:-1] + int(fileStep/2)
        ranks = np.linspace(y, y+height, num=Board.rankCount+1, dtype=np.uint16)[:-1] + int(rankStep/2)

        files = np.repeat(files[:, np.newaxis], Board.rankCount, 1)
        ranks = np.repeat(ranks[np.newaxis, :], Board.fileCount, 0)

        positions = np.dstack((files, ranks))

        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "fileStep", fileStep)
        object.__setattr__(self, "rankStep", rankStep)
        object.__setattr__(self, "tileSize", tileSize)

        # for file in self.positions: 
        #     for tileCenter in file:
        #         cv.circle(self.data, tileCenter, 1, (255,0,0), 2)

    @classmethod
    def _fallbackBoardDetection(cls, data: np.ndarray) -> Tuple[int, int, int, int]:
        imageHSV = cv.cvtColor(data, cv.COLOR_BGR2HSV)
        boardMask = cv.inRange(imageHSV, cls.hsvRange[0], cls.hsvRange[1])

        kernel = np.ones((5, 5), np.uint8)
        erosion = cv.erode(boardMask, kernel, iterations=3)
        dilate = cv.dilate(erosion, kernel, iterations=3)

        boardContours, _ = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        return cv.boundingRect(np.vstack(boardContours))

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
    
    def _detectCircles(self, image: np.ndarray, minDist: int, minRadius: int, maxRadius: int) -> np.ndarray:
        grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        clahe = cv.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        claheImage = clahe.apply(grayImage)
        blurredImage = cv.medianBlur(claheImage, 13)
        pieces = cv.HoughCircles(blurredImage, cv.HOUGH_GRADIENT, dp=2, minDist=minDist, param1=15, param2=45, minRadius=minRadius, maxRadius=maxRadius)
        return pieces[0] if pieces is not None else np.array([])

    @property
    def pieces(self) -> List[Tuple[Position, np.ndarray]]:
        pieces = []
        for file, tilesInfile in enumerate(self.positions):
            for rank, tileCenter in enumerate(tilesInfile[::-1]):
                tile = self._tile(tileCenter)
                detectedCircles = self._detectCircles(tile, tile.shape[0], int(self.fileStep*0.45), int(self.fileStep*0.5))

                if len(detectedCircles) == 0:
                    continue

                tileCenter = np.asarray(tile.shape[0:2])/2.0
                detectedCircles = sorted(detectedCircles, key=lambda circle: np.linalg.norm(tileCenter - np.asarray(circle[0:1])))
                *pieceCenter, pieceRadius = detectedCircles[0]
                if np.linalg.norm(tileCenter - np.asarray(pieceCenter)) > self.fileStep/3.1:
                    # print(tileCenter, " --- ", pieceCenter, " : ", np.linalg.norm(tileCenter - np.asarray(pieceCenter)), " = ", self.fileStep/3.1)
                    continue
                # cv.circle(tile, np.asarray(pieceCenter, dtype=int), int(pieceRadius), (0,255,0), 3)
                # cv.circle(tile, np.asarray(pieceCenter, dtype=int), 2, (0,0,255), 3)

                x, y = pieceCenter
                offset = pieceRadius*self.pieceSizeMultiplier
                tile = tile[max(int(y-offset), 0):int(y+offset), max(int(x-offset), 0):int(x+offset)]
                pieces.append((Position(file, rank), tile))
        return pieces


if __name__ == "__main__":
    import time
    from pathlib import Path
    from aiBoardGame.vision.xiangqiPieceClassifier import XiangqiPieceClassifier
    
    from aiBoardGame.logic.engine.utility import boardToStr

    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board/board2.jpg")
    boardImage = BoardImage(data=cv.imread(boardImagePath.as_posix()).copy())

    # classifier = XiangqiPieceClassifier(Path("finalWeights.pt"))

    # from PIL import Image
    # from torchvision import transforms
    # tile = Image.fromarray(boardImage.tiles[8,9][...,::-1])
    # print(classifier.predict(transforms.ToTensor()(tile)))

    # start = time.time()
    # board = classifier.predictBoard(boardImage)
    # print(f"predict time: {time.time() - start:.4f}s")

    # print(boardToStr(board))

    cv.imshow("roi", boardImage.roi)
    cv.waitKey(0)

    # for position, tile in boardImage.pieces:
    #     cv.imshow(f"{position}", tile)
    #     cv.waitKey(0)
    #     cv.destroyAllWindows()

    # tiles = boardImage.tiles
    # for rank in range(Board.rankCount):
    #     for file in range(Board.fileCount):
    #         cv.imshow(f"({file},{rank})", tiles[file][rank])
    #         cv.waitKey(0)
    #         cv.destroyAllWindows()

    # cv.imshow(f"{classifier.predictTile(boardImage[8,5])}", boardImage[8,5])
    # cv.imwrite("test.jpg", boardImage[8,5])
    # cv.waitKey(0)

    # boardImage.showPieces()

    cv.destroyAllWindows()