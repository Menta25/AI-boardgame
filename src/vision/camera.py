from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Iterator, Tuple, NamedTuple, Optional, Iterable
import numpy as np
import cv2 as cv

from model.board import Board


class Resolution(NamedTuple):
    """Store width and height in pixel"""
    width: float
    height: float


class FocalLength(NamedTuple):
    horizontal: float
    vertical: float


class CameraError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class Camera:
    resolution: Resolution
    _matrix: Optional[np.ndarray] = field(init=False, default=None)
    _distortionCoefficients: Optional[np.ndarray] = field(init=False, default=None)

    _newMatrix: Optional[np.ndarray] = field(init=False, default=None)
    _regionOfInterest: Optional[Tuple[float, float, float, float]] = field(init=False, default=None)

    _calibrationCritera: ClassVar[Tuple[int, int, float]] = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    _calibrationMinPatternCount: ClassVar[int] = 5

    @property
    def isCalibrated(self) -> bool:
        return self._matrix is not None and \
               self._distortionCoefficients is not None and \
               self._newMatrix is not None and \
               self._regionOfInterest is not None

    @property
    def focalLength(self) -> FocalLength:
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        return FocalLength(self._matrix[0][0], self._matrix[1][1])

    def calibrate(self, images: Iterable[np.ndarray], chessBoardShape: Tuple[int, int] = (8,8)) -> None:
        objp = np.zeros((np.prod(chessBoardShape),3), np.float32)
        objp[:,:2] = np.mgrid[0:chessBoardShape[0],0:chessBoardShape[1]].T.reshape(-1,2)

        objPoints = []
        imgPoints = []

        patternCount = 0
        while (image := next(images, None)) is not None and patternCount < self._calibrationMinPatternCount:
            grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

            isPatternFound, corners = cv.findChessboardCorners(grayImage, chessBoardShape, None)

            if isPatternFound:
                patternCount += 1
                objPoints.append(objp)

                cv.cornerSubPix(grayImage, corners, (11,11), (-1,-1), self._calibrationCritera)
                imgPoints.append(corners)

        reprojectionError, cameraMatrix, distortionCoefficients, _, _ = cv.calibrateCamera(objPoints, imgPoints, self.resolution, None, None)

        if not 0 <= reprojectionError <= 1:
            raise CameraError(f"Failed to calibrate camera, reprojection error should be between 0.0 and 1.0 pixel (was {reprojectionError} pixel)")

        self._matrix = cameraMatrix
        self._distortionCoefficients = distortionCoefficients

        self._newMatrix, self._regionOfInterest = cv.getOptimalNewCameraMatrix(cameraMatrix, distortionCoefficients, self.resolution, 1, self.resolution)

        
    def undistort(self, image: np.ndarray) -> np.ndarray:
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        undistortedImage = cv.undistort(image, self._matrix, self._distortionCoefficients, None, self._newMatrix)
        x, y, width, height = self._regionOfInterest
        return undistortedImage[y:y+height, x:x+width]


@dataclass
class RobotCamera(Camera):
    def detectBoard(self, image: np.ndarray) -> Board:
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")

        height, width, _ = image.shape

        arucoDict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
        arucoParams = cv.aruco.DetectorParameters_create()

        markerCorners, markerIds, _ = cv.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)
        markers = zip(markerIds, markerCorners)
        markers = {markerId[0]-1: markerCorners for markerId, markerCorners in markers}

        board = np.array([markers[i][0][(i+2) % 4] for i in range(4)])
        mat = cv.getPerspectiveTransform(board, np.float32([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ]))
        warpedBoard = cv.warpPerspective(image, mat, (width, height), flags=cv.INTER_LINEAR)
        return Board.create(warpedBoard, rows=10, cols=9)

@dataclass
class Helper:
    path: Path

    def images(self) -> Iterator[np.ndarray]:
        imageFiles = self.path.glob("*.jpeg")
        for imageFile in imageFiles:
            yield cv.imread(imageFile.as_posix())
            