import logging
from pathlib import Path
from typing import Optional, List
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed
from aiBoardGame.view.calibrationTypesWidget import CalibrationTypesWidget


_UI_PATH = Path("src/aiBoardGame/view/ui/cameraTabWidget.ui")


class CameraTabWidget(QWidget):
    def __init__(self, cameraThread: CameraThread, parent: Optional[QWidget] = None, flags: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = cameraThread
        self._cameraThread.calibrated.connect(self.enableUndistortButton)

        self.cameraFeedLabel = CameraFeed(self._cameraThread)
        self.rawCameraVerticalLayout.insertWidget(1, self.cameraFeedLabel, stretch=1)

        self.initCameraInputsComboBox()

        self.cameraInputsComboBox.currentTextChanged.connect(self.initCamera)
        self.undistortCheckBox.stateChanged.connect(self.setCameraUndistortion)
        self.calibrateButton.clicked.connect(self.showCalibrationTypesWidget)

        self.calibrationTypesWidget = CalibrationTypesWidget(self._cameraThread)
        self.calibrationTypesWidget.closed.connect(self.showTrueParent)
        self.calibrationTypesWidget.calibrationWidget.closed.connect(self.showTrueParent)
        self.trueParent =  parent

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self._cameraThread.isRunning():
            self._cameraThread.stop()
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
        if self._cameraThread.isRunning():
            self._cameraThread.stop()

        self._cameraThread.capturePath = Path(cameraPathStr)
        self._cameraThread.start()

        if not self.calibrateButton.isEnabled():
            self.calibrateButton.setEnabled(True)

    @pyqtSlot(int)
    def setCameraUndistortion(self, value: int) -> None:
        if self._cameraThread is not None:
            self._cameraThread.isUndistorted = bool(value)

    @pyqtSlot()
    def showCalibrationTypesWidget(self) -> None:
        self.trueParent.hide()
        self.calibrationTypesWidget.show()

    @pyqtSlot()
    def showTrueParent(self) -> None:
        self.trueParent.show()

    @pyqtSlot()
    def enableUndistortButton(self) -> None:
        self.undistortCheckBox.setEnabled(self._cameraThread.camera.isCalibrated)
