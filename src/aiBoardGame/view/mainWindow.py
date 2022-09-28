from logging import exception
import numpy as np
from pathlib import Path
from typing import Optional
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from aiBoardGame.view.cameraTabWidget import CameraTabWidget
from aiBoardGame.view.boardTabWidget import BoardTabWidget
from aiBoardGame.view.cameraThread import CameraThread


_UI_PATH = Path("src/aiBoardGame/view/ui/mainWindow.ui")


class MainWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, flags: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = CameraThread()

        self.cameraTabWidget = CameraTabWidget(self._cameraThread, self)
        self.boardTabWidget = BoardTabWidget(self._cameraThread, self)

        self.tabsWidget.addTab(self.cameraTabWidget, "Camera")
        self.tabsWidget.addTab(self.boardTabWidget, "Board")
