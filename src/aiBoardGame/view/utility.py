"""Utility functions for GUI"""

# pylint: disable=no-name-in-module, no-member

from typing import Optional
import numpy as np
import cv2 as cv
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

def imageToPixmap(image: np.ndarray, toWidth: Optional[int] = None, toHeight: Optional[int] = None) -> QPixmap:
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
