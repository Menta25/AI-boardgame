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

    def __init__(self, resolution: Union[Resolution, Tuple[int, int]], intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        if isinstance(resolution, tuple):
            resolution = Resolution(*resolution)

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

    def undistort(self, image: np.ndarray) -> np.ndarray:
        if not self.isCalibrated:
                raise CameraError("Camera is not calibrated yet")
        return cv.undistort(image, self._intrinsicMatrix, self._distortionCoefficients, None, self._undistortedIntrinsicMatrix)

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
        objp = np.zeros((np.prod(checkerBoardShape),3), np.float32)
        objp[:,:2] = np.mgrid[0:checkerBoardShape[0],0:checkerBoardShape[1]].T.reshape(-1,2)

        objPoints = []
        imgPoints = []

        patternCount = 0
        for image in checkerBoardImages:
            if patternCount >= self.calibrationMinPatternCount:
                break

            grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            isPatternFound, corners = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
            if isPatternFound:
                patternCount += 1
                objPoints.append(objp)

                cv.cornerSubPix(grayImage, corners, (11,11), (-1,-1), self._calibrationCritera)
                imgPoints.append(corners)

        if patternCount < self.calibrationMinPatternCount:
            raise CameraError(f"Not enough pattern found for calibration, found only {patternCount} out of {self.calibrationMinPatternCount}")

        reprojectionError, cameraMatrix, distortionCoefficients, _, _ = cv.calibrateCamera(objPoints, imgPoints, self.resolution, None, None)

        if not 0 <= reprojectionError <= 1:
            raise CameraError(f"Reprojection error should be between 0.0 and 1.0 pixel after calibration, was {reprojectionError} pixel")

        self._intrinsicMatrix = cameraMatrix
        self._distortionCoefficients = distortionCoefficients

        self._undistortedIntrinsicMatrix, self._regionOfInterest = cv.getOptimalNewCameraMatrix(cameraMatrix, distortionCoefficients, self.resolution, 1, self.resolution)

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
        errorMessage = "Invalid parameter file, cannot load calibration"
        try:
            with np.load(filePath, mmap_mode="r") as parameters:
                if self.resolution == Resolution(parameters["cameraWidth"], parameters["cameraHeight"]):
                    self._intrinsicMatrix = parameters["intrinsicMatrix"]
                    self._distortionCoefficients = parameters["distortionCoefficients"]
                    self._undistortedIntrinsicMatrix = parameters["newIntrinsicMatrix"]
                    self._regionOfInterest = parameters["regionOfInterest"]
                    self.calibrated.emit()
                else:
                    raise CameraError(errorMessage)
        except AttributeError as attributeError:
            raise CameraError(f"{errorMessage}\n{attributeError}")


class RobotCameraInterface(AbstractCameraInterface):
    """Camera subclass used for playing board games"""

    _boardImageRatio: ClassVar[float] = 3/4


    def __init__(self, resolution: Union[Resolution, Tuple[int, int]], intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(resolution, intrinsicsFile, parent)

        self._boardHeight = int(min(self.resolution.width, self.resolution.height) * self._boardImageRatio)
        self._boardHeight -= self._boardHeight % Board.rankCount
        self._boardWidth = int(self._boardHeight * Board.fileCount / Board.rankCount)
        self._boardWidth -= self._boardHeight % Board.fileCount

        self._boardOffset = np.around(np.array([self._boardWidth, self._boardHeight], dtype=np.float32) * 0.1)

        self._robotToCameraTransform: Optional[np.ndarray] = None
    
    @staticmethod
    def _generateCorners(hull: np.ndarray) -> np.ndarray:
        if len(hull) > 5:
            return np.array([])

        coordinateSums = np.sum(hull, axis=1)
        sortedCoordinateSums = np.argsort(coordinateSums)
        topLeft, bottomRight = hull[sortedCoordinateSums[0]], hull[sortedCoordinateSums[-1]]

        coordinateDiffs = np.diff(hull, axis=1).squeeze(1)
        sortedCoordinateDiffs = np.argsort(coordinateDiffs)
        topRight, bottomLeft = hull[sortedCoordinateDiffs[0]], hull[sortedCoordinateDiffs[-1]]

        return np.array([topRight, bottomRight, bottomLeft, topLeft], dtype=np.float32)

    @classmethod
    def _detectCorners(cls, image: np.ndarray) -> np.ndarray:
        imageHSV = cv.cvtColor(image, cv.COLOR_BGR2HSV)

        # cv.imshow("hsv", cv.resize(imageHSV, (960,540)))
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        hsvMask1 = cv.inRange(imageHSV, BoardImage.hsvRanges[0][0], BoardImage.hsvRanges[0][1])
        hsvMask2 = cv.inRange(imageHSV, BoardImage.hsvRanges[1][0], BoardImage.hsvRanges[1][1])
        hsvMask3 = cv.inRange(imageHSV, BoardImage.hsvRanges[2][0], BoardImage.hsvRanges[2][1])


        # cv.imshow("hsv1", hsvMask1)
        # cv.waitKey(0)
        # cv.destroyAllWindows()
        
        # cv.imshow("hsv2", hsvMask2)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        # cv.imshow("hsv3", hsvMask3)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        boardMask = cv.bitwise_or(hsvMask1, hsvMask2)
        boardMask = cv.bitwise_or(boardMask, hsvMask3)

        # cv.imshow("mask", boardMask)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        erosionKernel = np.ones((3,3), np.uint8)
        dilationKernel = np.ones((9,9), np.uint8)
        erosion = cv.erode(boardMask, erosionKernel, iterations=4)
        dilate = cv.dilate(erosion, dilationKernel, iterations=2)

        # cv.imshow("dilate", dilate)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        boardContours, _ = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        boardContours = [boardContour for boardContour in boardContours if cv.contourArea(boardContour) > 50_000]
        
        if len(boardContours) == 0:
            return np.array([])

        boardContours = np.vstack(boardContours)

        # testContours = np.zeros(image.shape[0:2])
        # cv.drawContours(testContours, boardContours, -1, (255), 1)
        # cv.imshow("testContours", testContours)
        # cv.waitKey(0)
        # cv.destroyAllWindows()

        boardHull = cv.convexHull(np.vstack(boardContours))
        approxBoardHull = cv.approxPolyDP(boardHull, epsilon=0.01* cv.arcLength(boardHull, True), closed=True).squeeze(1)

        # for hullPoint in approxBoardHull:
        #     cv.circle(image, hullPoint, 1, (255,0,0), 2)
        # cv.imshow("image", image)
        # cv.waitKey(0)
        # cv.destroyAllWindows()
        
        return cls._generateCorners(approxBoardHull)

    @staticmethod
    def _detectArUcoCorners(image: np.ndarray) -> np.ndarray:
        arucoDict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
        arucoParams = cv.aruco.DetectorParameters_create()

        grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        markerCorners, markerIDs, _ = cv.aruco.detectMarkers(grayImage, arucoDict, parameters=arucoParams)

        if markerIDs is None or len(markerIDs) != 4:
            raise CameraError(f"Not enough ArUco marker found, found only {len(markerIDs) if markerIDs is not None else 0} out of 4")

        markers = zip(markerIDs, markerCorners)
        markers = {markerId[0]-1: markerCorners.squeeze(0) for markerId, markerCorners in markers}
        return np.array([markers[i][(i+2)%4] for i in range(4)])

    def detectBoard(self, image: np.ndarray) -> BoardImage:
        """
            Detect game board on given image with the help of 4 ArUco markers and return a Board instance

            :raises CameraError: Not enough ArUco marker found on image
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")

        corners = self._detectCorners(image)
        if len(corners) != 4:
            corners = self._detectArUcoCorners(image)

        transformedCorners = np.array([
            [0, 0],
            [self._boardWidth, 0],
            [self._boardWidth, self._boardHeight],
            [0, self._boardHeight]
        ], dtype=np.float32) + self._boardOffset

        warpMatrix = cv.getPerspectiveTransform(corners, transformedCorners)

        warpSize = (np.array([self._boardWidth, self._boardHeight]) + 2*self._boardOffset).astype(int)
        warpedBoard = cv.warpPerspective(image, warpMatrix, warpSize, flags=cv.INTER_LINEAR)
        return BoardImage(warpedBoard, int(self._boardOffset[0]), int(self._boardOffset[1]), int(self._boardWidth), int(self._boardHeight))

    # TODO: Implement
    def calculateRobotToCameraTransform(self, robotPoints: np.ndarray, board: BoardImage) -> None:
        if len(robotPoints) != 4:
            raise CameraError(f"Robot to camera transform calculation needs 4 points in the robot's coordinate system, got {len(robotPoints)}")


class RobotCamera(RobotCameraInterface):
    def __init__(self, feedInput: Union[int, Path, str], resolution: Union[Resolution, Tuple[int, int]], intrinsicsFile: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(resolution, intrinsicsFile, parent)

        if isinstance(feedInput, (int, str)):
            self._capture = cv.VideoCapture(feedInput, cv.CAP_V4L2)
        elif isinstance(feedInput, Path):
            self._capture = cv.VideoCapture(feedInput.as_posix(), cv.CAP_V4L2)
        else:
            raise CameraError("Invalid camera input type, must be int, Path or str")

        if not self._capture.isOpened():
            raise CameraError("Cannot open camera, invalid feed input")

        self._capture.set(cv.CAP_PROP_FRAME_WIDTH, self.resolution.width)
        self._capture.set(cv.CAP_PROP_FRAME_HEIGHT, self.resolution.height)

    def read(self, undistorted: bool = True) -> np.ndarray:
        wasSuccessful, image = self._capture.read()
        if not wasSuccessful:
            raise CameraError("Cannot read from camera")
        return image if undistorted is False else self.undistort(image)

    def feed(self, undistorted: bool = True) -> Iterator[np.ndarray]:
        while True:
            image = self.read(undistorted)
            if image is not None:
                yield image

    def __del__(self) -> None:
        self._capture.release()


if __name__ == "__main__":
    camera = RobotCameraInterface(Resolution(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz"))
    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/0.jpg")
    board = camera.detectBoard(cv.imread(boardImagePath.as_posix()))
    cv.imwrite(Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/top0.jpg").as_posix(), cv.resize(board.data, (900,1000)))