import sys
import logging
import cv2 as cv
import numpy as np
from typing import Iterator, List, Optional
from pathlib import Path
from dataclasses import dataclass
from aiBoardGame.model.board import Board
from PyQt6.QtWidgets import QApplication, QWidget, QComboBox, QCheckBox, QLabel
from PyQt6.QtGui import QPixmap, QColor, QImage, QCloseEvent
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QThread, Qt
from PyQt6 import uic
from aiBoardGame.vision.camera import RobotCamera, Resolution


logging.basicConfig(format="[{levelname:.1s}] [{asctime}.{msecs:<3.0f}] {module:>8} : {message}", datefmt="%H:%M:%S", style="{", level=logging.INFO)

class GUI(QWidget):
    def __init__(self) -> None:
        super().__init__()

        uiPath = Path("src/aiBoardGame/ui/mainWindow.ui")
        uic.load_ui.loadUi(uiPath.as_posix(), self)

        self.cameraThread: Optional[CameraThread] = None

        self.initCameraInputsComboBox()
        self.cameraInputsComboBox.currentTextChanged.connect(self.initCamera)
        self.undistortCheckBox.stateChanged.connect(self.setCameraUndistortion)

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.cameraThread is not None:
            self.cameraThread.stop()
        return super().closeEvent(a0)

    def initCameraInputsComboBox(self) -> None:
        cameras = self.listCameras()
        self.cameraInputsComboBox.addItems([camera.as_posix() for camera in cameras])
        self.cameraInputsComboBox.setCurrentIndex(-1)

    def listCameras(self) -> List[Path]:
        devPath = Path("/dev/")
        return list(devPath.glob("video*"))

    @pyqtSlot(str)
    def initCamera(self, cameraPathStr: str) -> None:
        if self.cameraThread is not None:
            self.cameraThread.stop()
            self.cameraThread.newCameraImageSignal.disconnect()

        self.undistortCheckBox.setEnabled(True)
        self.cameraThread = CameraThread(capturePath=Path(cameraPathStr), isUndistorted=self.undistortCheckBox.isChecked())
        self.cameraThread.newCameraImageSignal.connect(self.updateCameraFeedImage)
        self.cameraThread.start()

    @pyqtSlot(np.ndarray)
    def updateCameraFeedImage(self, image: np.ndarray) -> None:
        qtPixmap = self.imageToPixmap(image, self.cameraFeedLabel.width(), self.cameraFeedLabel.height())
        self.cameraFeedLabel.setPixmap(qtPixmap)

    @pyqtSlot(int)
    def setCameraUndistortion(self, value: int) -> None:
        if self.cameraThread is not None:
            self.cameraThread.isUndistorted = bool(value)

    def imageToPixmap(self, image: np.ndarray, toWidth: Optional[int] = None, toHeight: Optional[int] = None) -> QPixmap:
            """Convert from an opencv image to QPixmap"""
            rgbImage = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            height, width, channel = rgbImage.shape
            if toWidth is None:
                toWidth = width
            if toHeight is None:
                toHeight = height
            bytesPerLine = channel * width
            qImage = QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            scaledQImage = qImage.scaled(toWidth, toHeight, Qt.AspectRatioMode.KeepAspectRatio)
            return QPixmap.fromImage(scaledQImage)

class CameraThread(QThread):
    newCameraImageSignal = pyqtSignal(np.ndarray)

    def __init__(self, capturePath: Path, isUndistorted: bool = False) -> None:
        super().__init__()
        self._isRunning = True
        self._capturePath = capturePath
        self._isUndistorted = isUndistorted

    @property
    def isUndistorted(self, value: bool) -> None:
        self._isUndistorted = value

    def run(self):
        robotCamera = RobotCamera(self._capturePath)
        while self._isRunning:
            image = robotCamera.read(undistorted=self._isUndistorted)
            if image is not None:
                self.newCameraImageSignal.emit(image)

    def stop(self):
        self._isRunning = False
        self.wait()


def main() -> None:
    # storedParams = Path("camParams.npz")
    # cam = RobotCamera(feedInput=5, intrinsicsFile=storedParams if storedParams.exists() else None)
    # if not cam.isCalibrated:
    #     cam.calibrate((8,6))
    #     cam.saveParameters("camParams.npz")

    # xiangqiBoard: Board = cam.detectBoard(cam.read())
    # pieces = xiangqiBoard.pieces()

    app = QApplication([])
    window = GUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
