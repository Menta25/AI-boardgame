from __future__ import annotations

import logging
from turtle import circle
import numpy as np
import cv2 as cv
from typing import Union, Sequence
from dataclasses import dataclass, field

_boardLogger = logging.getLogger(__name__)

Numeric = Union[int, float, complex, np.number]


@dataclass(repr=False, eq=False, frozen=True)
class Board:
    """A game board represented by a ndarray"""
    data: np.ndarray
    rows: int = 10
    cols: int = 9
    tileWidth: int = field(init=False)
    tileHeight: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tileWidth", int(self.data.shape[1] / self.cols))
        object.__setattr__(self, "tileHeight", int(self.data.shape[0] / self.rows))
        _boardLogger.debug(f"Create Board(rows={self.rows}; cols={self.cols}; tileSize={self.tileWidth}x{self.tileHeight}) from {self.data.shape} array")

    @classmethod
    def create(cls, ndarray: np.ndarray, rows: int = 10, cols: int = 9) -> Board:
        """Create a board from a 2D matrix or an image"""
        boardHeight = ndarray.shape[0]
        boardWidth = ndarray.shape[1]
        tileHeight = int(boardHeight / rows)
        tileWidth = int(boardWidth / cols)
        board = ndarray.reshape(-1, cols, tileWidth, 3).swapaxes(0, 1).reshape(cols, rows, tileHeight, tileWidth, 3)
        return Board(data=board)

    @property
    def tiles(self) -> np.ndarray:
        return self.data.reshape(-1, self.cols, self.tileWidth, 3).swapaxes(0, 1).reshape(self.cols, self.rows, self.tileHeight, self.tileWidth, 3)

    def tile(self, row: int, col: int) -> np.ndarray:
        """Return the given tile's ndarray representation"""
        startY = row*self.tileHeight
        startX = col*self.tileWidth
        return self.data[startY:startY+self.tileHeight, startX:startX+self.tileWidth]

    def withGrid(self, borderWidth: int, borderValue: Union[int, Sequence[Numeric]] = np.array([255, 255, 255])) -> np.ndarray:
        boardWithGrid = self.data.copy()
        verticalGridLines = np.repeat(np.arange(self.tileWidth, self.data.shape[1], step=self.tileWidth), borderWidth, axis=0)
        horizontalGridLines = np.repeat(np.arange(self.tileHeight, self.data.shape[0], step=self.tileHeight), borderWidth, axis=0)
        boardWithGrid = np.insert(boardWithGrid, verticalGridLines, borderValue, axis=1)
        boardWithGrid = np.insert(boardWithGrid, horizontalGridLines, borderValue, axis=0)
        return boardWithGrid


    def pieces(self) -> np.ndarray:
        blurredBoard = cv.medianBlur(self.data, 5)
        grayBlurredBoard = cv.cvtColor(blurredBoard, cv.COLOR_BGR2GRAY)

        pieces = cv.HoughCircles(grayBlurredBoard, cv.HOUGH_GRADIENT, dp=1.2, minDist=self.tileWidth*3/4, param1=60, param2=50, minRadius=int(self.tileWidth/3), maxRadius=int(self.tileWidth/2.5))

        if pieces is None:
            print("No piece found")
            return

        pieces = np.uint16(np.around(pieces))

        return pieces[0,:]