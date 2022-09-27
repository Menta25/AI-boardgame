import numpy as np
from typing import ClassVar
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, QThread

from aiBoardGame.vision.camera import RobotCamera

class CameraThread(QThread):
    newCameraImageSignal: ClassVar[pyqtSignal] = pyqtSignal(np.ndarray)

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
