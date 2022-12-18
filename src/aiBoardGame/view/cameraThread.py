import numpy as np
from typing import ClassVar, Optional
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QThread

from aiBoardGame.vision import RobotCamera, Resolution


class CameraThread(QThread):
    newCameraImageSignal: ClassVar[pyqtSignal] = pyqtSignal(np.ndarray)
    calibrated: ClassVar[pyqtSignal] = pyqtSignal()

    def __init__(self, captureIndex: Optional[int] = None) -> None:
        super().__init__()
        self._isRunning = True
        self.captureIndex = captureIndex
        self._isUndistorted = False

        self.image = None
        self._camera = None

    @property
    def camera(self) -> Optional[RobotCamera]:
        return self._camera

    @property
    def isUndistorted(self) -> bool:
        return self._isUndistorted

    @isUndistorted.setter
    def isUndistorted(self, value: bool) -> None:
        if value is True and not self._camera.isCalibrated:
            return

        self._isUndistorted = value

    def run(self):
        self._camera = RobotCamera(self.captureIndex, Resolution(1920, 1080))
        self._camera.calibrated.connect(self.onCameraCalibrated)
        self._isUndistorted = False
        self._isRunning = True
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
