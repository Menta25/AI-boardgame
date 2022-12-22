"""Camera control and image extraction"""

# pylint: disable=no-member

from __future__ import annotations

import logging
from time import sleep
from pathlib import Path
from threading import Thread, Event
from typing import ClassVar, Tuple, NamedTuple, Optional, Union, List
import numpy as np
import cv2 as cv

from aiBoardGame.logic.engine import Board
from aiBoardGame.vision.boardImage import BoardImage


_cameraLogger = logging.getLogger(__name__)


class Resolution(NamedTuple):
    """Named tuple for resolution"""
    width: int
    height: int

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


class CameraError(Exception):
    """Exception for camera errors"""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AbstractCameraInterface:
    """Class for handling camera output and calibration"""
    calibrated: ClassVar[Event] = Event()
    """Threading event set after calibration"""
    calibrationMinPatternCount: ClassVar[int] = 5
    """Minimum image count for calibration"""
    _calibrationCritera: ClassVar[Tuple[int, int, float]] = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    def __init__(self, resolution: Union[Resolution, Tuple[int, int]], intrinsicsFile: Optional[Path] = None) -> None:
        """
        :param resolution: Resolution of the camera
        :type resolution: Union[Resolution, Tuple[int, int]]
        :param intrinsicsFile: Calibration file that stores camera intrinsics, defaults to None
        :type intrinsicsFile: Optional[Path], optional
        """
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
        """Checks if camera is calibrated"""
        return self._intrinsicMatrix is not None and \
               self._distortionCoefficients is not None and \
               self._undistortedIntrinsicMatrix is not None and \
               self._regionOfInterest is not None

    def undistort(self, image: np.ndarray) -> np.ndarray:
        """Undistorts an image

        :param image: Image from camera
        :type image: np.ndarray
        :raises CameraError: Camera is not calibrated yet
        :return: Undistorted image
        :rtype: np.ndarray
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")
        return cv.undistort(image, self._intrinsicMatrix, self._distortionCoefficients, None, self._undistortedIntrinsicMatrix)

    @staticmethod
    def isSuitableForCalibration(image: np.ndarray, checkerBoardShape: Tuple[int, int]) -> bool:
        """Check if image is suitable for calibration.
        It is suitable if a checkerboard pattern is found on the image

        :param image: Image for calibration
        :type image: np.ndarray
        :param checkerBoardShape: Shape of the checkerboard (horizontal and vertical vertices)
        :type checkerBoardShape: Tuple[int, int]
        :return: Image is suitable or not
        :rtype: bool
        """
        logging.info(checkerBoardShape)
        grayImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        isPatternFound, _ = cv.findChessboardCorners(grayImage, checkerBoardShape, None)
        return isPatternFound


    def calibrate(self, checkerBoardImages: List[np.ndarray], checkerBoardShape: Tuple[int, int]) -> None:
        """Calibrate camera

        :param checkerBoardImages: Images containing checkerboard patterns in different poses
        :type checkerBoardImages: List[np.ndarray]
        :param checkerBoardShape: Shape of the checkerboard (horizontal and vertical vertices)
        :type checkerBoardShape: Tuple[int, int]
        :raises CameraError: Not enough pattern found
        :raises CameraError: High reprojection error
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

        self.calibrated.set()

    def saveParameters(self, filePath: Path) -> None:
        """Save camera intrinsics

        :param filePath: File to save to
        :type filePath: Path
        """
        _cameraLogger.debug("Saving camera parameters to {savePath}", savePath=filePath)
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
        """Load camera intrinsics

        :param filePath: File to load from
        :type filePath: Path
        :raises CameraError: Intrinsics file does not have required fields for calibration
        :raises CameraError: Intrinsics belong to a camera with different resolution
        """
        errorMessage = "Invalid parameter file, cannot load calibration"
        try:
            with np.load(filePath, mmap_mode="r") as parameters:
                if self.resolution == Resolution(parameters["cameraWidth"], parameters["cameraHeight"]):
                    self._intrinsicMatrix = parameters["intrinsicMatrix"]
                    self._distortionCoefficients = parameters["distortionCoefficients"]
                    self._undistortedIntrinsicMatrix = parameters["newIntrinsicMatrix"]
                    self._regionOfInterest = parameters["regionOfInterest"]
                    self.calibrated.set()
                else:
                    raise CameraError(errorMessage)
        except AttributeError as attributeError:
            raise CameraError(f"{errorMessage}\n{attributeError}") from attributeError


class RobotCameraInterface(AbstractCameraInterface):
    """AbstractCameraInterface subclass used for playing boardgames"""

    _boardImageRatio: ClassVar[float] = 3/4


    def __init__(self, resolution: Union[Resolution, Tuple[int, int]], intrinsicsFile: Optional[Path] = None) -> None:
        """
        :param resolution: Resolution of the camera
        :type resolution: Union[Resolution, Tuple[int, int]]
        :param intrinsicsFile: Calibration file that stores camera intrinsics, defaults to None
        :type intrinsicsFile: Optional[Path], optional
        """
        super().__init__(resolution, intrinsicsFile)

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

        mask = np.zeros(imageHSV.shape[:2], dtype=np.uint8)
        for hsvRange in BoardImage.hsvRanges:
            hsvMask = cv.inRange(imageHSV, hsvRange[0], hsvRange[1])
            mask = cv.bitwise_or(mask, hsvMask)
            # cv.imshow("hsv", hsvMask)
            # cv.waitKey(0)
            # cv.destroyAllWindows()

        erosionKernel = np.ones((3,3), np.uint8)
        dilationKernel = np.ones((9,9), np.uint8)
        erosion = cv.erode(mask, erosionKernel, iterations=4)
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
        """Detect board on image. Tries to detect corners with HSV ranges, if it fails then
        it falls back to aruco markers. After corner detection it transforms the image to
        top view with a perspective transform and creates a board image

        :param image: Image with a board
        :type image: np.ndarray
        :raises CameraError: Camera is not calibrated yet
        :raises CameraError: Could not detect board
        :return: Topdown board image
        :rtype: BoardImage
        """
        if not self.isCalibrated:
            raise CameraError("Camera is not calibrated yet")

        try:
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
        except CameraError as error:
            raise CameraError("Could not detect board") from error


class RobotCamera(RobotCameraInterface):
    """RobotCameraInterface subclass used for extracting output from a camera feed"""
    def __init__(self, feedInput: Union[int, Path, str], resolution: Union[Resolution, Tuple[int, int]], interval: float = 0.1, intrinsicsFile: Optional[Path] = None) -> None:
        """
        :param feedInput: Camera identifier. Index or device path
        :type feedInput: Union[int, Path, str]
        :param resolution: Resolution of the camera
        :type resolution: Union[Resolution, Tuple[int, int]]
        :param interval: Interval to extract image from feed, defaults to 0.1
        :type interval: float, optional
        :param intrinsicsFile: Calibration file that stores camera intrinsics, defaults to None
        :type intrinsicsFile: Optional[Path], optional
        :raises CameraError: Invalid camera input type
        :raises CameraError: Cannot open camera
        """
        super().__init__(resolution, intrinsicsFile)

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

        self.interval = interval
        self.isActive = False
        self._thread: Optional[Thread] = None
        self._frame: Optional[np.ndarray] = None

    def activate(self) -> None:
        """Activates camera feed extration on an interval
        """
        if not self.isActive:
            self.isActive = True
            self._thread = Thread(target=self._update, daemon=True)
            self._thread.start()
            sleep(self.interval+1)

    def deactivate(self) -> None:
        """Deactivates camera feed
        """
        if self.isActive:
            self.isActive = False
            self._thread.join()

    def _update(self) -> None:
        while self.isActive:
            _, self._frame = self._capture.read()
            sleep(self.interval)

    def read(self, undistorted: bool = True) -> np.ndarray:
        """Get last image extracted from camera

        :param undistorted: Undistort extracted image, defaults to True
        :type undistorted: bool, optional
        :raises CameraError: Camera is not active
        :raises CameraError: Read was not successful
        :return: Extracted image
        :rtype: np.ndarray
        """
        if not self.isActive:
            raise CameraError("Camera is not active, cannot read from camera")
        elif self._frame is None:
            raise CameraError("Capture device read was not successful")
        return self.undistort(self._frame) if undistorted else self._frame

    # def __del__(self) -> None:
    #     if self.isActive:
    #         self.deactivate()
    #     self._capture.release()


if __name__ == "__main__":
    camera = RobotCameraInterface(Resolution(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/camCalibs.npz"))
    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/0.jpg")
    board = camera.detectBoard(cv.imread(boardImagePath.as_posix()))
    cv.imwrite(Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/top0.jpg").as_posix(), cv.resize(board.data, (900,1000)))
