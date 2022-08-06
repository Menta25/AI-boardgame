import logging
import numpy as np
import cv2 as cv
from dataclasses import dataclass, field
from typing import ClassVar, Tuple, NamedTuple, Optional, Iterable

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


class CalibrationError(CameraError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class Camera:
    """Class for handling camera input"""
    resolution: Resolution
    _matrix: Optional[np.ndarray] = field(init=False, default=None)
    _distortionCoefficients: Optional[np.ndarray] = field(init=False, default=None)

    _newMatrix: Optional[np.ndarray] = field(init=False, default=None)
    _regionOfInterest: Optional[Tuple[float, float, float, float]] = field(init=False, default=None)

    _calibrationCritera: ClassVar[Tuple[int, int, float]] = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    _calibrationMinPatternCount: ClassVar[int] = 5

    def __post_init__(self) -> None:
        _cameraLogger.debug(f"Init camera with ({self.resolution}) resolution")

    @property
    def isCalibrated(self) -> bool:
        """Check if camera has been calibrated yet"""
        return self._matrix is not None and \
               self._distortionCoefficients is not None and \
               self._newMatrix is not None and \
               self._regionOfInterest is not None

    @property
    def focalLength(self) -> FocalLength:
        """
            Get focal length stored in the camera matrix

            :raises CalibrationError: Camera is not calibrated yet
        """
        if not self.isCalibrated:
            raise CalibrationError("Camera is not calibrated yet")
        return FocalLength(self._matrix[0][0], self._matrix[1][1])

    def calibrate(self, images: Iterable[np.ndarray], checkerBoardShape: Tuple[int, int] = (8,8)) -> None:
        """
            Calibrate camera with given image feed

            :raises CalibrationError: Not enough valid pattern input or reprojection error is too high
        """
        _cameraLogger.debug("[Calibrate camera]")
        objp = np.zeros((np.prod(checkerBoardShape),3), np.float32)
        objp[:,:2] = np.mgrid[0:checkerBoardShape[0],0:checkerBoardShape[1]].T.reshape(-1,2)

        objPoints = []
        imgPoints = []

        _cameraLogger.debug(f"Iterating over source feed to search for checkered board patterns (required checkered board image: {self._calibrationMinPatternCount})")
        patternCount = 0
        while (image := next(images, None)) is not None and patternCount < self._calibrationMinPatternCount:
            grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

            isPatternFound, corners = cv.findChessboardCorners(grayImage, checkerBoardShape, None)

            if isPatternFound:
                patternCount += 1
                _cameraLogger.debug(f"Found checkered board image, need {self._calibrationMinPatternCount - patternCount} more")
                objPoints.append(objp)

                cv.cornerSubPix(grayImage, corners, (11,11), (-1,-1), self._calibrationCritera)
                imgPoints.append(corners)

        if patternCount < self._calibrationMinPatternCount:
            raise CalibrationError(f"Not enough pattern found for calibration, found only {patternCount} out of {self._calibrationMinPatternCount}")

        _cameraLogger.debug("Calibrate camera")
        reprojectionError, cameraMatrix, distortionCoefficients, _, _ = cv.calibrateCamera(objPoints, imgPoints, self.resolution, None, None)

        if not 0 <= reprojectionError <= 1:
            raise CalibrationError(f"Reprojection error should be between 0.0 and 1.0 pixel, was {reprojectionError} pixel")

        self._matrix = cameraMatrix
        self._distortionCoefficients = distortionCoefficients
        _cameraLogger.debug(f"Camera matrix:\n{self._matrix}")
        _cameraLogger.debug(f"Distortion coefficients: {self._distortionCoefficients}")

        self._newMatrix, self._regionOfInterest = cv.getOptimalNewCameraMatrix(cameraMatrix, distortionCoefficients, self.resolution, 1, self.resolution)
        _cameraLogger.debug(f"New camera matrix:\n{self._newMatrix}")
        _cameraLogger.debug(f"Region of intereset: {self._regionOfInterest}")

        _cameraLogger.debug("Calibration finished")

        
    def undistort(self, image: np.ndarray) -> np.ndarray:
        """Undistort given image with camera matrices and distortion coefficients"""
        if not self.isCalibrated:
            raise CalibrationError("Camera is not calibrated yet")
        _cameraLogger.debug("[Undistort image]")
        undistortedImage = cv.undistort(image, self._matrix, self._distortionCoefficients, None, self._newMatrix)
        x, y, width, height = self._regionOfInterest
        _cameraLogger.debug(f"Finished undistorting")
        return undistortedImage[y:y+height, x:x+width]


@dataclass
class RobotCamera(Camera):
    """Camera subclass used for playing board games"""
    _boardRows: ClassVar[int] = 10
    _boardCols: ClassVar[int] = 9

    def detectBoard(self, image: np.ndarray, arucoDictEnum: int = cv.aruco.DICT_4X4_50) -> Board:
        """
            Detect game board on given image with the help of 4 ArUco markers and return a Board instance

            :raises CameraError: Not enough ArUco marker found on image
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        _cameraLogger.debug("[Detect board on image]")

        height, width, _ = image.shape

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
            [width, 0],
            [width, height],
            [0, height]
        ]))
        warpedBoard = cv.warpPerspective(image, mat, (width, height), flags=cv.INTER_LINEAR)
        paddedWarpedBoard = np.pad(warpedBoard, pad_width=self._getPaddings(width, height, self._boardRows, self._boardCols), mode="symmetric")
        _cameraLogger.debug(f"Transformed image size: {paddedWarpedBoard.shape[1::-1]}")
        _cameraLogger.debug("Creating Board from transformed image")
        return Board.create(paddedWarpedBoard, rows=self._boardRows, cols=self._boardCols)

    @staticmethod
    def _getPaddings(width: int, height: int, rows: int, cols: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Calculate padding widths based on row and column count"""
        padWidth = cols - width % cols
        padWidth = (padWidth // 2, padWidth - padWidth // 2)
        padHeight = rows - height % rows
        padHeight = (padHeight // 2, padHeight - padHeight // 2)
        return padHeight, padWidth, (0,0)
            