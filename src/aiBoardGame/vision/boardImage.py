from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from typing import ClassVar, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from aiBoardGame.logic.engine import Board, Position



@dataclass(frozen=True)
class BoardImage:
    """A game board represented by a ndarray"""
    data: np.ndarray

    _x: Optional[int] = None
    _y: Optional[int] = None
    _width: Optional[int] = None
    _height: Optional[int] = None

    positions: np.ndarray = field(init=False)

    fileStep: int = field(init=False)
    rankStep: int = field(init=False)
    tileSize: np.ndarray = field(init=False)

    tileSizeMultiplier: ClassVar[float] = 1.6
    pieceSizeMultiplier: ClassVar[float] = 1.2
    pieceThresholdDivisor: ClassVar[float] = 3.1

    # hsvRanges: ClassVar[Tuple[np.ndarray]] = (
    #     np.array([15,128,150])[np.newaxis,:] + np.array([[15,128,150], [15,127,100]]) * np.array([[-1],[1]]),
    #     np.array([164,128,150])[np.newaxis,:] + np.array([[15,128,150], [15,127,100]]) * np.array([[-1],[1]]),
    #     np.array([130,15,160])[np.newaxis,:] + np.array([[30,20,25], [30,20,25]]) * np.array([[-1],[1]])
    # )
    
    hsvRanges: ClassVar[Tuple[np.ndarray]] = [np.array([[0,61,0], [30,255,255]])]


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
        boardMask = cv.inRange(imageHSV, cls.hsvRanges[0], cls.hsvRanges[1])

        # cv.imshow("mask", boardMask)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        erosionKernel = np.ones((3,3), np.uint8)
        dilationKernel = np.ones((9,9), np.uint8)
        erosion = cv.erode(boardMask, erosionKernel, iterations=4)
        dilate = cv.dilate(erosion, dilationKernel, iterations=2)

        # cv.imshow("dilate", dilate)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        boardContours, _ = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        boardContours = np.vstack([boardContour for boardContour in boardContours if cv.contourArea(boardContour) > 50_000])
        return cv.boundingRect(boardContours)

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
        blurredImage = cv.medianBlur(claheImage, 7)
        pieces = cv.HoughCircles(blurredImage, cv.HOUGH_GRADIENT, dp=2, minDist=minDist, param1=20, param2=50, minRadius=minRadius, maxRadius=maxRadius)
        return pieces[0] if pieces is not None else np.array([])

    @property
    def pieces(self) -> List[Tuple[Position, np.ndarray]]:
        pieces = []
        for file in range(Board.fileCount):
            for rank in range(Board.rankCount):
                position = Position(file, rank)
                piece = self.findPiece(position)
                if piece is not None:
                    pieces.append((position, piece))
        return pieces

    @property
    def pieceTiles(self) -> List[Tuple[Position, np.ndarray]]:
        pieceTiles = []
        for position, (x, y, radius) in self.pieces:
            offset = radius * self.pieceSizeMultiplier
            tile = self.data[max(int(y-offset), 0):int(y+offset), max(int(x-offset), 0):int(x+offset)]
            pieceTiles.append((position, tile))
        return pieceTiles

    def findPiece(self, position: Position) -> Optional[np.ndarray]:
        tileCenter = self.positions[position.file, Board.rankCount - position.rank - 1]
        tile = self._tile(tileCenter)
        detectedCircles = self._detectCircles(tile, tile.shape[0], int(self.fileStep*0.45), int(self.fileStep*0.5))

        if len(detectedCircles) == 0:
            return None

        normalizedTileCenter = np.asarray(tile.shape[0:2])/2.0
        detectedCircles = sorted(detectedCircles, key=lambda circle: np.linalg.norm(normalizedTileCenter - np.asarray(circle[0:1])))
        circle = np.asarray(detectedCircles[0])
        circle[:2] += (tileCenter - self.tileSize/2).astype(np.uint16)
        logging.debug(f"{tileCenter} ---> {circle[:2]} : {np.linalg.norm(tileCenter - circle[:2])} <= {self.fileStep/self.pieceThresholdDivisor} ?")
        if np.linalg.norm(tileCenter - circle[:2]) > self.fileStep/self.pieceThresholdDivisor:
            return None

        return circle[:3]


if __name__ == "__main__":
    import time
    from pathlib import Path
    
    from aiBoardGame.logic.engine.utility import prettyBoard

    from aiBoardGame.vision.camera import RobotCameraInterface, RobotCamera, CameraError
    from aiBoardGame.vision.xiangqiPieceClassifier import XiangqiPieceClassifier

    logging.basicConfig(level=logging.DEBUG, format="")

    classifier = XiangqiPieceClassifier(device=XiangqiPieceClassifier.getAvailableDevice())
    cameraIntrinsicsPath = Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz")
    # camera = RobotCameraInterface(resolution=(1920, 1080), intrinsicsFile=cameraIntrinsicsPath)
    # imagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board/example2.jpg")
    # image = camera.undistort(cv.imread(imagePath.as_posix()))

    camera = RobotCamera(feedInput=2, resolution=(1920,1080), interval=0.1, intrinsicsFile=cameraIntrinsicsPath)
    camera.activate()
    image = camera.read()
    try:
        boardImage = camera.detectBoard(image)

        cv.imshow("roi", boardImage.roi)
        cv.waitKey(0)

        for position, tile in boardImage.pieceTiles:
            cv.imshow(f"{position}", tile)
            cv.waitKey(0)
            cv.destroyAllWindows()

        start = time.time()
        board = classifier.predictBoard(boardImage)
        logging.info(f"predict time: {time.time() - start:.4f}s")

        logging.info(prettyBoard(board, colors=True))

    except CameraError:
        logging.exception("Cannot test board image")
