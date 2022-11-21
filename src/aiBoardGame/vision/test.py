from typing import Tuple
import numpy as np
import cv2 as cv
from pathlib import Path

from aiBoardGame.vision.camera import RobotCameraInterface, Resolution, CameraError
from aiBoardGame.vision.boardImage import BoardImage

def test(image: np.ndarray) -> np.ndarray:
    imageHSV = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    boardHSV = np.array([15,89,153])
    boardMask = cv.inRange(imageHSV, boardHSV-np.array([10,80,120]), boardHSV+np.array([5,166,50]))

    kernel = np.ones((5, 5), np.uint8)
    erosion = cv.erode(boardMask, kernel, iterations=3)
    dilate = cv.dilate(erosion, kernel, iterations=3)

    boardContours, _ = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    boardHull = cv.convexHull(np.vstack(boardContours))
    approxBoardHull = cv.approxPolyDP(boardHull, epsilon=0.01* cv.arcLength(boardHull, True), closed=True).squeeze(1)
    
    return orderCorners(approxBoardHull)

def orderCorners(corners: np.ndarray) -> np.ndarray:
    coordinateSums = np.sum(corners, axis=1)
    sortedCoordinateSums = np.argsort(coordinateSums)
    topLeft, bottomRight = corners[sortedCoordinateSums[0]], corners[sortedCoordinateSums[-1]]

    coordinateDiffs = np.diff(corners, axis=1).squeeze(1)
    sortedCoordinateDiffs = np.argsort(coordinateDiffs)
    topRight, bottomLeft = corners[sortedCoordinateDiffs[0]], corners[sortedCoordinateDiffs[-1]]

    return np.array([topLeft, topRight, bottomRight, bottomLeft])

def searchParams(imagesPath: Path) -> Tuple[int, float, int, int]:
    blurBounds = (3,15)
    dpBounds = (1.0,5.0)
    param1Bounds = (1,150)
    param2Bounds = (1,150)

    blur = blurBounds[0]
    while blur < blurBounds[1]:
        dp = dpBounds[0]
        while dp < dpBounds[1]:
            param1 = param1Bounds[0]
            while param1 < param1Bounds[1]:
                param2 = param2Bounds[0]
                while param2 < param2Bounds[1]:
                    print(blur, dp, param1, param2)
                    all2 = True
                    for imagePath in imagesPath.iterdir():
                        image = cv.imread(imagePath.as_posix())
                        image = camera.undistort(image)

                        board = camera.detectBoard(image)
                        circles = board._detectCircles2(blur, dp, param1, param2)
                        if len(circles) != 2:
                            all2 = False
                            break
                    if all2:
                        return blur, dp, param1, param2
                    param2 += 5
                param1 += 5
            dp += 0.1
        blur += 2

if __name__ == "__main__":
    camera = RobotCameraInterface(resolution=Resolution(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz"))

    imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/Black/BlackAdvisor")

    print("\n"*5,searchParams(imagesPath))
