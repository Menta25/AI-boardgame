from __future__ import annotations

import logging
import numpy as np
import cv2 as cv
from pathlib import Path
from typing import ClassVar, Iterator, Tuple, NamedTuple, Optional, Union, List
from PyQt6.QtCore import pyqtSignal, QObject

from aiBoardGame.logic.engine import Board
from aiBoardGame.vision.boardImage import BoardImage


_cameraLogger = logging.getLogger(__name__)


class Resolution(NamedTuple):
    """Store width and height in pixel"""
    width: int
    height: int

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


class FocalLength(NamedTuple):
    horizontal: float
    vertical: float


class CameraError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AbstractCameraInterface(QObject):
    """Class for handling camera input"""
    calibrated: ClassVar[pyqtSignal] = pyqtSignal()
    calibrationMinPatternCount: ClassVar[int] = 5
    _calibrationCritera: ClassVar[Tuple[int, int, float]] = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    def __init__(self, resolution: Resolution, intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.resolution = resolution

        self._intrinsicMatrix: Optional[np.ndarray] = None
        self._distortionCoefficients: Optional[np.ndarray] = None
        self._undistortedIntrinsicMatrix: Optional[np.ndarray] = None
        self._regionOfInterest: Optional[Tuple[float, float, float, float]] = None

        if intrinsicsFile is not None:
            self.loadParameters(intrinsicsFile)

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

            :raises CameraError: Camera is not calibrated yet
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        return FocalLength(self._intrinsicMatrix[0][0], self._intrinsicMatrix[1][1])

    def _undistort(self, image: np.ndarray) -> np.ndarray:
        if not self.isCalibrated:
                raise CameraError("Camera is not calibrated yet")
        undistortedImage = cv.undistort(image, self._intrinsicMatrix, self._distortionCoefficients, None, self._undistortedIntrinsicMatrix)
        x, y, width, height = self._regionOfInterest
        return undistortedImage[y:y+height, x:x+width]

    @staticmethod
    def isSuitableForCalibration(image: np.ndarray, checkerBoardShape: Tuple[int, int]) -> bool:
        logging.info(checkerBoardShape)
        grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        isPatternFound, _ = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
        return isPatternFound


    def calibrate(self, checkerBoardImages: List[np.ndarray], checkerBoardShape: Tuple[int, int]) -> None:
        """
            Calibrate camera with given image feed

            :raises CameraError: Not enough valid pattern input or reprojection error is too high
        """
        _cameraLogger.debug("[Calibrate camera]")
        objp = np.zeros((np.prod(checkerBoardShape),3), np.float32)
        objp[:,:2] = np.mgrid[0:checkerBoardShape[0],0:checkerBoardShape[1]].T.reshape(-1,2)

        objPoints = []
        imgPoints = []

        _cameraLogger.debug(f"Iterating over source feed to search for checkered board patterns (required checkered board image: {self.calibrationMinPatternCount})")
        patternCount = 0
        for image in checkerBoardImages:
            if patternCount >= self.calibrationMinPatternCount:
                break

            grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            isPatternFound, corners = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
            if isPatternFound:
                patternCount += 1
                _cameraLogger.debug(f"Found checkered board image, need {self.calibrationMinPatternCount - patternCount} more")
                objPoints.append(objp)

                cv.cornerSubPix(grayImage, corners, (11,11), (-1,-1), self._calibrationCritera)
                imgPoints.append(corners)

        if patternCount < self.calibrationMinPatternCount:
            raise CameraError(f"Not enough pattern found for calibration, found only {patternCount} out of {self.calibrationMinPatternCount}")

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
        self.calibrated.emit()

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
        try:
            with np.load(filePath, mmap_mode="r") as parameters:
                if self.resolution == Resolution(parameters["cameraWidth"], parameters["cameraHeight"]):
                    self._intrinsicMatrix = parameters["intrinsicMatrix"]
                    self._distortionCoefficients = parameters["distortionCoefficients"]
                    self._undistortedIntrinsicMatrix = parameters["newIntrinsicMatrix"]
                    self._regionOfInterest = parameters["regionOfInterest"]
                    self.calibrated.emit()
                else:
                    _cameraLogger.error("Camera resolutions do not match, cannot import parameters")
        except AttributeError as attributeError:
            raise CameraError(f"Invalid parameter file, cannot load calibration\n{attributeError}")


class RobotCameraInterface(AbstractCameraInterface):
    """Camera subclass used for playing board games"""

    _boardImageRatio: ClassVar[float] = 3/4

    def __init__(self, resolution: Resolution, intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(resolution, intrinsicsFile, parent)

        self._boardHeight = int(min(self.resolution.width, self.resolution.height) * self._boardImageRatio)
        self._boardHeight -= self._boardHeight % Board.rankCount
        self._boardWidth = int(self._boardHeight * Board.fileCount / Board.rankCount)
        self._boardWidth -= self._boardHeight % Board.fileCount

        self._robotToCameraTransform: Optional[np.ndarray] = None

    def detectBoard(self, image: np.ndarray) -> BoardImage:
        """
            Detect game board on given image with the help of 4 ArUco markers and return a Board instance

            :raises CameraError: Not enough ArUco marker found on image
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        _cameraLogger.debug("[Detect board on image]")

        _cameraLogger.debug("Get ArUco dictionary")
        arucoDict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
        arucoParams = cv.aruco.DetectorParameters_create()

        _cameraLogger.debug("Detecting ArUco markers")
        markerCorners, markerIDs, _ = cv.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)

        if markerIDs is None or len(markerIDs) != 4:
            raise CameraError(f"Not enough ArUco marker found, found only {len(markerIDs) if markerIDs is not None else 0} out of 4")

        _cameraLogger.debug(f"Marker IDs: {markerIDs.flatten()}")

        markers = zip(markerIDs, markerCorners)
        markers = {markerId[0]-1: markerCorners for markerId, markerCorners in markers}

        _cameraLogger.debug("Transforming detected board image")
        board = np.array([markers[i][0][i] for i in range(4)])
        mat = cv.getPerspectiveTransform(board, np.float32([
            [0, 0],
            [self._boardWidth, 0],
            [self._boardWidth, self._boardHeight],
            [0, self._boardHeight]
        ]))
        warpedBoard = cv.warpPerspective(image, mat, (self._boardWidth, self._boardHeight), flags=cv.INTER_LINEAR)
        return BoardImage(warpedBoard)

    # TODO: Implement
    def calculateRobotToCameraTransform(self, robotPoints: np.ndarray, board: BoardImage) -> None:
        if len(robotPoints) != 4:
            raise CameraError(f"Robot to camera transform calculation needs 4 points in the robot's coordinate system, got {len(robotPoints)}")


class RobotCamera(RobotCameraInterface):
    def __init__(self, feedInput: Union[int, Path, str], resolution: Resolution, intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(resolution, intrinsicsFile, parent)

        if isinstance(feedInput, (int, str)):
            self._capture = cv.VideoCapture(feedInput, cv.CAP_V4L2)
        elif isinstance(feedInput, Path):
            self._capture = cv.VideoCapture(feedInput.as_posix(), cv.CAP_V4L2)
        else:
            raise CameraError("Invalid camera input type, must be int, Path or str")

        if not self._capture.isOpened():
            raise CameraError("Cannot open camera, invalid feed input")

        self._capture.set(cv.CAP_PROP_FRAME_WIDTH, resolution.width)
        self._capture.set(cv.CAP_PROP_FRAME_HEIGHT, resolution.height)

    def read(self, undistorted: bool = True) -> Optional[np.ndarray]:
        wasSuccessful, image = self._capture.read()
        if wasSuccessful:
            return image if undistorted is False else self._undistort(image)
        else:
            return None

    def feed(self, undistorted: bool = True) -> Iterator[np.ndarray]:
        while True:
            image = self.read(undistorted)
            if image is not None:
                yield image

    def __del__(self) -> None:
        self._capture.release()
