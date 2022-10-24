from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from typing import Tuple, Union, Sequence
from dataclasses import dataclass, field

from aiBoardGame.logic.auxiliary import Board, Position

_boardLogger = logging.getLogger(__name__)

Numeric = Union[int, float, complex, np.number]


@dataclass(frozen=True)
class BoardImage:
    """A game board represented by a ndarray"""
    data: np.ndarray
    tileWidth: int = field(init=False)
    tileHeight: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tileWidth", int(self.data.shape[1] / Board.fileCount))
        object.__setattr__(self, "tileHeight", int(self.data.shape[0] / Board.rankCount))
        _boardLogger.info(f"Create Board(rows={Board.rankCount}; cols={Board.fileCount}; tileSize={self.tileWidth}x{self.tileHeight}) from {self.data.shape} array")

    @property
    def tiles(self) -> np.ndarray:
        return self.data.reshape(-1, Board.fileCount, self.tileWidth, 3).swapaxes(0, 1).reshape(Board.fileCount, Board.rankCount, self.tileHeight, self.tileWidth, 3)

    def tile(self, position: Position) -> np.ndarray:
        """Return the given tile's ndarray representation"""
        startY = position.rank*self.tileHeight
        startX = position.file*self.tileWidth
        return self.data[startY:startY+self.tileHeight, startX:startX+self.tileWidth]

    def __getitem__(self, key: Union[Position, Tuple[int, int]]) -> np.ndarray:
        if isinstance(key, tuple):
            key = Position(*key)
        if isinstance(key, Position):
            return self.tile(key)
        else:
            raise TypeError(f"Key has invalid type {key.__class__.__name__}")

    def withGrid(self, borderWidth: int, borderValue: Union[int, Sequence[Numeric]] = np.array([255, 255, 255])) -> np.ndarray:
        boardWithGrid = self.data.copy()
        verticalGridLines = np.repeat(np.arange(self.tileWidth, self.data.shape[1], step=self.tileWidth), borderWidth, axis=0)
        horizontalGridLines = np.repeat(np.arange(self.tileHeight, self.data.shape[0], step=self.tileHeight), borderWidth, axis=0)
        boardWithGrid = np.insert(boardWithGrid, verticalGridLines, borderValue, axis=1)
        boardWithGrid = np.insert(boardWithGrid, horizontalGridLines, borderValue, axis=0)
        return boardWithGrid

    # TODO: Rewrite ?
    def pieces(self) -> np.ndarray:
        blurredBoard = cv.medianBlur(self.data, 5)
        grayBlurredBoard = cv.cvtColor(blurredBoard, cv.COLOR_BGR2GRAY)

        pieces = cv.HoughCircles(grayBlurredBoard, cv.HOUGH_GRADIENT, dp=1.5, minDist=self.tileWidth, param1=30, param2=46, minRadius=int(self.tileWidth/2 - self.tileWidth/10), maxRadius=int(self.tileWidth/2 + self.tileWidth/10))
        if pieces is None:
            print("No piece found")
            return

        pieces = np.uint16(np.around(pieces))
        return pieces[0,:]
