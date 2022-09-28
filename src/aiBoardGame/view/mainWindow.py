import logging
from pathlib import Path
from typing import Optional, List
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed
from aiBoardGame.view.calibrationTypesWidget import CalibrationTypesWidget


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
        self.calibrateButton.clicked.connect(self.calibrationTypesWidget)

        self.calibrationTypesWidget = CalibrationTypesWidget(self._cameraThread, self)
        self.calibrationTypesWidget.closed.connect(self.showWindow)
        self.calibrationTypesWidget.calibrated.connect(self.showWindow)

    @property
    def cameraThread(self) -> Optional[CameraThread]:
        return self._cameraThread

    @cameraThread.setter
    def cameraThread(self, value: CameraThread) -> None:
        if self._cameraThread is not None:
            self._cameraThread.stop()
            self._cameraThread.calibrated.disconnect(self.enableUndistortButton)

        self._cameraThread = value
        self.calibrationTypesWidget.cameraThread = self._cameraThread
        self.cameraFeedLabel.cameraThread = self._cameraThread
        self._cameraThread.calibrated.connect(self.enableUndistortButton)
        self._cameraThread.start()

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.cameraThread is not None:
            self.cameraThread.stop()
        self.calibrationTypesWidget.closed.disconnect()
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
        self.cameraThread = CameraThread(capturePath=Path(cameraPathStr))

        if not self.calibrateButton.isEnabled():
            self.calibrateButton.setEnabled(True)

    @pyqtSlot(int)
    def setCameraUndistortion(self, value: int) -> None:
        if self.cameraThread is not None:
            self.cameraThread.isUndistorted = bool(value)

    @pyqtSlot()
    def calibrationTypesWidget(self) -> None:
        self.hide()
        self.calibrationTypesWidget.show()

    @pyqtSlot()
    def showWindow(self) -> None:
        self.show()

    @pyqtSlot()
    def enableUndistortButton(self) -> None:
        self.undistortCheckBox.setEnabled(self._cameraThread.camera.isCalibrated)
