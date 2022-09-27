from pathlib import Path
from typing import Optional, List
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed
from aiBoardGame.view.calibrationWidget import CalibrationWidget


_UI_PATH = Path("src/aiBoardGame/view/ui/mainWindow.ui")


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread: Optional[CameraThread] = None
        self.cameraFeedLabel = CameraFeed()
        self.rawCameraVerticalLayout.insertWidget(1, self.cameraFeedLabel, stretch=1)

        self.initCameraInputsComboBox()

        self.cameraInputsComboBox.currentTextChanged.connect(self.initCamera)
        self.undistortCheckBox.stateChanged.connect(self.setCameraUndistortion)
        self.calibrateButton.clicked.connect(self.showCalibrationWidget)

        self.calibrationWidget = CalibrationWidget(self)
        self.calibrationWidget.closed.connect(self.showWindow)

    @property
    def cameraThread(self) -> CameraThread:
        return self._cameraThread

    @cameraThread.setter
    def cameraThread(self, value: CameraThread) -> None:
        if self._cameraThread is not None:
            self._cameraThread.stop()

        self._cameraThread = value
        self.calibrationWidget.cameraThread = self._cameraThread
        self.cameraFeedLabel.cameraThread = self._cameraThread

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.cameraThread is not None:
            self.cameraThread.stop()
        self.calibrationWidget.closed.disconnect()
        return super().closeEvent(a0)

    def initCameraInputsComboBox(self) -> None:
        cameras = self.listCameras()
        self.cameraInputsComboBox.addItems([camera.as_posix() for camera in cameras])
        self.cameraInputsComboBox.setCurrentIndex(-1)

    def listCameras(self) -> List[Path]:
        devPath = Path("/dev/")
        return list(devPath.glob("video*"))

    @pyqtSlot(str)
    def initCamera(self, cameraPathStr: str) -> None:
        if self.cameraThread is not None:
            self.cameraThread.stop()

        self.cameraThread = CameraThread(capturePath=Path(cameraPathStr), isUndistorted=self.undistortCheckBox.isChecked())
        self.cameraThread.start()

    @pyqtSlot(int)
    def setCameraUndistortion(self, value: int) -> None:
        if self.cameraThread is not None:
            self.cameraThread.isUndistorted = bool(value)

    @pyqtSlot()
    def showCalibrationWidget(self) -> None:
        self.hide()
        self.calibrationWidget.show()

    @pyqtSlot()
    def showWindow(self) -> None:
        self.show()
