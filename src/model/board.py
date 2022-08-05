from __future__ import annotations

import logging
import numpy as np
from typing import Union, Sequence
from dataclasses import dataclass

_boardLogger = logging.getLogger(__name__)

Numeric = Union[int, float, complex, np.number]


@dataclass(repr=False, eq=False, frozen=True)
class Board:
    """A game board represented by a ndarray with [rows, cols, tileHeight, tileWidth, ...] dimensions"""
    data: np.ndarray

    def __post_init__(self) -> None:
        _boardLogger.debug(f"Created Board(rows={self.rows}; cols={self.cols}; tileSize={self.tileWidth}x{self.tileHeight})")

    @classmethod
    def create(cls, ndarray: np.ndarray, rows: int = 10, cols: int = 9) -> Board:
        """Create a board from a 2D matrix or an image"""
        boardHeight = ndarray.shape[0]
        boardWidth = ndarray.shape[1]
        tileHeight = int(boardHeight / rows)
        tileWidth = int(boardWidth / cols)
        return Board(data=ndarray.reshape([cols, rows, tileHeight, tileWidth, 3]))

    @property
    def cols(self) -> int:
        return self.data.shape[0]

    @property
    def rows(self) -> int:
        return self.data.shape[1]

    @property
    def tileHeight(self) -> int:
        return self.data.shape[2]

    @property
    def tileWidth(self) -> int:
        return self.data.shape[3]

    def tile(self, row: int, col: int) -> np.ndarray:
        """Return the given tile's ndarray representation"""
        return self.data[col, row]

    def flatten(self, gridSize: int = 0, gridValue: Union[int, Sequence[Numeric]] = np.array([255, 255, 255])) -> np.ndarray:
        """Flatten the board representation to a one dimensional ndarray"""
        flattenedBoard = self.data.reshape([self.rows * self.tileHeight, self.cols * self.tileWidth, -1])
        if gridSize > 0:
            verticalGridLines = np.repeat(np.arange(self.tileWidth, flattenedBoard.shape[1], step=self.tileWidth), gridSize, axis=0)
            horizontalGridLines = np.repeat(np.arange(self.tileHeight, flattenedBoard.shape[0], step=self.tileHeight), gridSize, axis=0)
            flattenedBoard = np.insert(flattenedBoard, verticalGridLines, gridValue, axis=1)
            flattenedBoard = np.insert(flattenedBoard, horizontalGridLines, gridValue, axis=0)
        return flattenedBoard
