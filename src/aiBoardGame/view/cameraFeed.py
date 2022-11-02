import numpy as np
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.utility import imageToPixmap

class CameraFeed(QLabel):
    def __init__(self, cameraThread: CameraThread) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._cameraThread = cameraThread
        self._cameraThread.newCameraImageSignal.connect(self.updateCameraFeedImage)

    @pyqtSlot(np.ndarray)
    def updateCameraFeedImage(self, image: np.ndarray) -> None:
        qtPixmap = imageToPixmap(image, self.width(), self.height())
        self.setPixmap(qtPixmap)
