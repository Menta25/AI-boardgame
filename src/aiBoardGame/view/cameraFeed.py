import numpy as np
import cv2 as cv
from typing import Optional
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage

from .cameraThread import CameraThread

class CameraFeed(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cameraThread = None

    @property
    def cameraThread(self) -> CameraThread:
        return self._cameraThread

    @cameraThread.setter
    def cameraThread(self, value: CameraThread) -> None:
        if self._cameraThread is not None:
            self.cameraThread.newCameraImageSignal.disconnect(self.updateCameraFeedImage)

        self._cameraThread = value
        self._cameraThread.newCameraImageSignal.connect(self.updateCameraFeedImage)


    @pyqtSlot(np.ndarray)
    def updateCameraFeedImage(self, image: np.ndarray) -> None:
        qtPixmap = self._imageToPixmap(image, self.width(), self.height())
        self.setPixmap(qtPixmap)

    @staticmethod
    def _imageToPixmap(image: np.ndarray, toWidth: Optional[int] = None, toHeight: Optional[int] = None) -> QPixmap:
        """Convert from an opencv image to QPixmap"""
        rgbImage = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        height, width, channel = rgbImage.shape
        if toWidth is None:
            toWidth = width
        if toHeight is None:
            toHeight = height
        bytesPerLine = channel * width
        qImage = QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qImage).scaled(toWidth, toHeight, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
