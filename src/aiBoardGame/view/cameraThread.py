import numpy as np
from typing import ClassVar
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, QThread

from aiBoardGame.vision.camera import RobotCamera

class CameraThread(QThread):
    newCameraImageSignal: ClassVar[pyqtSignal] = pyqtSignal(np.ndarray)

    def __init__(self, capturePath: Path) -> None:
        super().__init__()
        self._isRunning = True
        self._capturePath = capturePath
        self._isUndistorted = False

        self.image = None
        self.camera = None

    @property
    def isUndistorted(self) -> bool:
        return self._isUndistorted

    @isUndistorted.setter
    def isUndistorted(self, value: bool) -> None:
        self._isUndistorted = value

    def run(self):
        self.camera = RobotCamera(self._capturePath)
        while self._isRunning:
            image = self.camera.read(undistorted=self._isUndistorted)
            if image is not None:
                self.image = image
                self.newCameraImageSignal.emit(self.image)

    def stop(self):
        self._isRunning = False
        self.wait()
