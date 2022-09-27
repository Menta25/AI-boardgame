from __future__ import annotations

import logging
from pathlib import Path
import numpy as np
import cv2 as cv
from typing import ClassVar, Iterator, Tuple, NamedTuple, Optional, Union, List

from aiBoardGame.model.board import Board


_cameraLogger = logging.getLogger(__name__)


class Resolution(NamedTuple):
    """Store width and height in pixel"""
    width: float
    height: float

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


class FocalLength(NamedTuple):
    horizontal: float
    vertical: float


class CameraError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message



class Camera:
    """Class for handling camera input"""

    _calibrationCritera: ClassVar[Tuple[int, int, float]] = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    _calibrationMinPatternCount: ClassVar[int] = 5

    def __init__(self, feedInput: Union[int, Path, str], intrinsicsFile: Optional[Path] = None) -> None:
        if isinstance(feedInput, (int, str)):
            self._capture = cv.VideoCapture(feedInput)
        elif isinstance(feedInput, Path):
            self._capture = cv.VideoCapture(feedInput.as_posix())
        else:
            raise CameraError("Invalid camera input type, must be int, Path or str")

        if not self._capture.isOpened():
            raise CameraError("Cannot open camera, invalid feed input")

        #_cameraLogger.debug(f"Init camera with ({self.resolution}) resolution")

        self._intrinsicMatrix: Optional[np.ndarray] = None
        self._distortionCoefficients: Optional[np.ndarray] = None

        self._undistortedIntrinsicMatrix: Optional[np.ndarray] = None
        self._regionOfInterest: Optional[Tuple[float, float, float, float]] = None

        if intrinsicsFile is not None:
            self.loadParameters(intrinsicsFile)

    def __del__(self) -> None:
        self._capture.release()

    @property
    def resolution(self) -> Resolution:
        return Resolution(self._capture.get(cv.CAP_PROP_FRAME_WIDTH), self._capture.get(cv.CAP_PROP_FRAME_HEIGHT))

    @property
    def isCalibrated(self) -> bool:
        """Check if camera has been calibrated yet"""
        return self._intrinsicMatrix is not None and \
               self._distortionCoefficients is not None and \
               self._undistortedIntrinsicMatrix is not None and \
               self._regionOfInterest is not None

    @property
    def focalLength(self) -> FocalLength:
        """
            Get focal length stored in the camera matrix

            :raises CalibrationError: Camera is not calibrated yet
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        return FocalLength(self._intrinsicMatrix[0][0], self._intrinsicMatrix[1][1])

    def read(self, undistorted: bool = True) -> Optional[np.ndarray]:
        wasSuccessful, image = self._capture.read()
        if wasSuccessful:
            return image if undistorted is False else self._undistort(image)
        else:
            return None

    def _undistort(self, image: np.ndarray) -> np.ndarray:
        if not self.isCalibrated:
                raise CameraError("Camera is not calibrated yet")
        undistortedImage = cv.undistort(image, self._intrinsicMatrix, self._distortionCoefficients, None, self._undistortedIntrinsicMatrix)
        x, y, width, height = self._regionOfInterest
        return undistortedImage[y:y+height, x:x+width]

    def feed(self, undistorted: bool = True) -> Iterator[np.ndarray]:
        while True:
            image = self.read(undistorted)
            if image is not None:
                yield image

    def isSuitableForCalibration(self, image: np.ndarray, checkerBoardShape: Tuple[int, int]) -> bool:
        grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        isPatternFound, _ = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
        return isPatternFound


    def calibrate(self, checkerBoardImages: List[np.ndarray], checkerBoardShape: Tuple[int, int]) -> None:
        """
            Calibrate camera with given image feed

            :raises CalibrationError: Not enough valid pattern input or reprojection error is too high
        """
        _cameraLogger.info("[Calibrate camera]")
        objp = np.zeros((np.prod(checkerBoardShape),3), np.float32)
        objp[:,:2] = np.mgrid[0:checkerBoardShape[0],0:checkerBoardShape[1]].T.reshape(-1,2)

        objPoints = []
        imgPoints = []

        _cameraLogger.debug(f"Iterating over source feed to search for checkered board patterns (required checkered board image: {self._calibrationMinPatternCount})")
        patternCount = 0
        for image in checkerBoardImages:
            if patternCount >= self._calibrationMinPatternCount:
                break

            grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            isPatternFound, corners = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
            if isPatternFound:
                patternCount += 1
                _cameraLogger.debug(f"Found checkered board image, need {self._calibrationMinPatternCount - patternCount} more")
                objPoints.append(objp)

                cv.cornerSubPix(grayImage, corners, (11,11), (-1,-1), self._calibrationCritera)
                imgPoints.append(corners)

        if patternCount < self._calibrationMinPatternCount:
            raise CameraError(f"Not enough pattern found for calibration, found only {patternCount} out of {self._calibrationMinPatternCount}")

        _cameraLogger.debug("Calibrate camera")
        reprojectionError, cameraMatrix, distortionCoefficients, _, _ = cv.calibrateCamera(objPoints, imgPoints, self.resolution, None, None)

        if not 0 <= reprojectionError <= 1:
            raise CameraError(f"Reprojection error should be between 0.0 and 1.0 pixel after calibration, was {reprojectionError} pixel")

        self._intrinsicMatrix = cameraMatrix
        self._distortionCoefficients = distortionCoefficients
        _cameraLogger.debug(f"Intrinsic matrix:\n{self._intrinsicMatrix}")
        _cameraLogger.debug(f"Distortion coefficients: {self._distortionCoefficients}")

        self._undistortedIntrinsicMatrix, self._regionOfInterest = cv.getOptimalNewCameraMatrix(cameraMatrix, distortionCoefficients, self.resolution, 1, self.resolution)
        _cameraLogger.debug(f"New intrinsic matrix:\n{self._undistortedIntrinsicMatrix}")
        _cameraLogger.debug(f"Region of intereset: {self._regionOfInterest}")

        _cameraLogger.debug("Calibration finished")

    def saveParameters(self, filePath: Path) -> None:
        _cameraLogger.debug(f"Saving camera parameters to {filePath}")
        resolution = self.resolution
        parameters = {
            "cameraWidth": resolution.width,
            "cameraHeight": resolution.height,
            "intrinsicMatrix": self._intrinsicMatrix,
            "distortionCoefficients": self._distortionCoefficients,
            "newIntrinsicMatrix": self._undistortedIntrinsicMatrix,
            "regionOfInterest": self._regionOfInterest
        }
        np.savez(filePath, **parameters)

    def loadParameters(self, filePath: Path) -> None:
        _cameraLogger.debug(f"Load camera parameters from {filePath}")
        with np.load(filePath, mmap_mode="r") as parameters:
            if self.resolution == Resolution(parameters["cameraWidth"], parameters["cameraHeight"]):
                self._intrinsicMatrix = parameters["intrinsicMatrix"]
                self._distortionCoefficients = parameters["distortionCoefficients"]
                self._undistortedIntrinsicMatrix = parameters["newIntrinsicMatrix"]
                self._regionOfInterest = parameters["regionOfInterest"]
            else:
                _cameraLogger.error("Camera resolutions do not match, cannot import parameters")


class RobotCamera(Camera):
    """Camera subclass used for playing board games"""
    _boardRows: ClassVar[int] = 10
    _boardCols: ClassVar[int] = 9

    def __init__(self, feedInput: Union[int, Path, str], intrinsicsFile: Optional[Path] = None) -> None:
        super().__init__(feedInput, intrinsicsFile)

        self._boardHeight = min(self.resolution.width, self.resolution.height)
        self._boardHeight -= self._boardHeight % self._boardRows
        self._boardWidth = int(self._boardHeight * self._boardCols / self._boardRows)
        self._boardWidth -= self._boardHeight % self._boardCols

        self._robotToCameraTransform: Optional[np.ndarray] = None

    def detectBoard(self, image: np.ndarray, arucoDictEnum: int = cv.aruco.DICT_4X4_50) -> Board:
        """
            Detect game board on given image with the help of 4 ArUco markers and return a Board instance

            :raises CameraError: Not enough ArUco marker found on image
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        _cameraLogger.info("[Detect board on image]")

        _cameraLogger.debug("Get ArUco dictionary")
        arucoDict = cv.aruco.getPredefinedDictionary(arucoDictEnum)
        arucoParams = cv.aruco.DetectorParameters_create()

        _cameraLogger.debug("Detecting ArUco markers")
        markerCorners, markerIDs, _ = cv.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)
        _cameraLogger.debug(f"Marker IDs: {markerIDs.flatten()}")

        if len(markerIDs) != 4:
            raise CameraError(f"Not enough ArUco marker found, found only {len(markerIDs)} out of 4")

        markers = zip(markerIDs, markerCorners)
        markers = {markerId[0]-1: markerCorners for markerId, markerCorners in markers}

        _cameraLogger.debug("Transforming detected board image")
        board = np.array([markers[i][0][(i+2) % 4] for i in range(4)])
        mat = cv.getPerspectiveTransform(board, np.float32([
            [0, 0],
            [self._boardWidth, 0],
            [self._boardWidth, self._boardHeight],
            [0, self._boardHeight]
        ]))
        warpedBoard = cv.warpPerspective(image, mat, (self._boardWidth, self._boardHeight), flags=cv.INTER_LINEAR)
        return Board(warpedBoard, rows=self._boardRows, cols=self._boardCols)

    def calculateRobotToCameraTransform(self, robotPoints: np.ndarray, board: Board) -> None:
        if len(robotPoints) != 4:
            raise CameraError(f"Robot to camera transform calculation needs 4 points in the robot's coordinate system, got {len(robotPoints)}")
