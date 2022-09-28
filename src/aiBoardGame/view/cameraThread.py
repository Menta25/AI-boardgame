import numpy as np
from typing import ClassVar, Optional
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QThread

from aiBoardGame.vision.camera import RobotCamera

class CameraThread(QThread):
    newCameraImageSignal: ClassVar[pyqtSignal] = pyqtSignal(np.ndarray)
    calibrated: ClassVar[pyqtSignal] = pyqtSignal()

    def __init__(self, capturePath: Path) -> None:
        super().__init__()
        self._isRunning = True
        self._capturePath = capturePath
        self._isUndistorted = False

        self.image = None
        self._camera = None

    @property
    def isUndistorted(self) -> bool:
        return self._isUndistorted

    @property
    def camera(self) -> Optional[RobotCamera]:
        return self._camera

    @isUndistorted.setter
    def isUndistorted(self, value: bool) -> None:
        self._isUndistorted = value

    def run(self):
        self._camera = RobotCamera(self._capturePath)
        self._camera.calibrated.connect(self.onCameraCalibrated)
        while self._isRunning:
            image = self._camera.read(undistorted=self._isUndistorted)
            if image is not None:
                self.image = image
                self.newCameraImageSignal.emit(self.image)
        self._camera.calibrated.disconnect(self.onCameraCalibrated)

    def stop(self):
        self._isRunning = False
        self.wait()

    @pyqtSlot()
    def onCameraCalibrated(self) -> None:
        self.calibrated.emit()
