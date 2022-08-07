import logging
import cv2 as cv
import numpy as np
from typing import Iterator
from pathlib import Path
from dataclasses import dataclass
from aiBoardGame.model.board import Board

from aiBoardGame.vision.camera import RobotCamera, Resolution


logging.basicConfig(level=logging.DEBUG)

@dataclass
class Helper:
    path: Path

    def images(self) -> Iterator[np.ndarray]:
        imageFiles = self.path.glob("*.jpg")
        for imageFile in imageFiles:
            yield cv.imread(imageFile.as_posix())


def main() -> None:
    camRes = Resolution(3648, 2736)
    storedParams = Path("camParams.npz")
    if storedParams.exists():
        cam = RobotCamera.fromSavedParameters(camRes, storedParams)
    else:
        helper = Helper(Path("img/calib"))
        cam = RobotCamera(camRes)
        cam.calibrate(helper.images(), (8,6))
        cam.saveParameters("camParams.npz")

    distortedBoardImage = cv.imread("img/test4.jpg")
    undistortedBoardImage = cam.undistort(distortedBoardImage)
    xiangqiBoard: Board = cam.detectBoard(undistortedBoardImage)
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
