from pathlib import Path
from typing import Optional, ClassVar
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed


_UI_PATH = Path("src/aiBoardGame/view/ui/calibrationWidget.ui")


class CalibrationWidget(QWidget):
    closed: ClassVar[pyqtSignal] = pyqtSignal()

    def __init__(self, cameraThread: CameraThread, parent: Optional['QWidget'] = None, flags: Qt.WindowType = Qt.WindowType.Dialog) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = cameraThread
        self.cameraFeedLabel = CameraFeed()
        self.calibrationLayout.insertWidget(1, self.cameraFeedLabel, stretch=1)

    @property
    def cameraThread(self) -> CameraThread:
        return self._cameraThread

    @cameraThread.setter
    def cameraThread(self, value: CameraThread) -> None:
        self._cameraThread = value
        self.cameraFeedLabel.cameraThread = self._cameraThread

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)