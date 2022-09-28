import logging
import numpy as np
from pathlib import Path
from typing import Optional
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSlot

from aiBoardGame.view.cameraFeed import CameraFeed
from aiBoardGame.view.cameraFeed import CameraThread
from aiBoardGame.view.utils import imageToPixmap

from aiBoardGame.vision.camera import CameraError


_UI_PATH = Path("src/aiBoardGame/view/ui/boardTabWidget.ui")


class BoardTabWidget(QWidget):
    def __init__(self, cameraThread: CameraThread, parent: Optional[QWidget] = None, flags: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = cameraThread

        self.rawCameraFeed = CameraFeed(self._cameraThread)
        self.rawCameraFeed.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.leftLayout.insertWidget(0, self.rawCameraFeed)

        self._cameraThread.newCameraImageSignal.connect(self.updateBoard)

        self.board = None

    @pyqtSlot(np.ndarray)
    def updateBoard(self, image: np.ndarray) -> None:
        if self._cameraThread.isUndistorted:
            try:
                self.board = self._cameraThread.camera.detectBoard(image)
                qtPixmap = imageToPixmap(self.board.withGrid(10), self.boardView.width(), self.boardView.height())
                self.boardView.setPixmap(qtPixmap)
            except CameraError:
                pass
        