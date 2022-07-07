import numpy as np
import cv2 as cv

from datatypes.board import Board


def detectBoard(image: np.ndarray) -> Board:
    arucoDict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
    arucoParams = cv.aruco.DetectorParameters_create()

    markerCorners, markerIds, rejectedCandidates = cv.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)
    markers = zip(markerIds, markerCorners)
    markers = {markerId[0]-1: markerCorners for markerId, markerCorners in markers}

    board = np.array([markers[i][0][(i+2) % 4] for i in range(4)])
    mat = cv.getPerspectiveTransform(board, np.float32([
        [0, 0],
        [405, 0],
        [405, 400],
        [0, 400]
    ]))
    warpedBoard = cv.warpPerspective(image, mat, (405, 400), flags=cv.INTER_LINEAR)
    return Board.create(warpedBoard, rows=10, cols=9)

