import logging
import cv2 as cv
import numpy as np
from typing import Iterator
from pathlib import Path
from dataclasses import dataclass
from aiBoardGame.model.board import Board

from aiBoardGame.vision.camera import RobotCamera, Resolution


logging.basicConfig(format="[{levelname:.1s}] [{asctime}.{msecs:<3.0f}] {module:>8} : {message}", datefmt="%H:%M:%S", style="{", level=logging.DEBUG)


def main() -> None:
    storedParams = Path("camParams.npz")
    cam = RobotCamera(feedInput=5, intrinsicsFile=storedParams if storedParams.exists() else None)
    if not cam.isCalibrated:
        cam.calibrate((8,6))
        cam.saveParameters("camParams.npz")

    xiangqiBoard: Board = cam.detectBoard(cam.read())
    pieces = xiangqiBoard.pieces()

    boardCopy = xiangqiBoard.data.copy()
    for i in pieces:
        cv.circle(boardCopy, (i[0], i[1]), i[2], (0,255,0), 20)
        cv.circle(boardCopy, (i[0], i[1]), 5, (0,0,255), 30)

    cv.imshow("circles", cv.resize(boardCopy, (boardCopy.shape[1]//3, boardCopy.shape[0]//3)))
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
