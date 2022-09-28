import logging
from pathlib import Path
from typing import Optional, ClassVar
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QProgressBar, QSpinBox, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed
from aiBoardGame.view.calibrationWidget import CalibrationWidget

from aiBoardGame.vision.camera import RobotCamera, CameraError


_UI_PATH = Path("src/aiBoardGame/view/ui/calibrationTypesWidget.ui")


class CalibrationTypesWidget(QWidget):
    closed: ClassVar[pyqtSignal] = pyqtSignal()
    calibrated: ClassVar[pyqtSlot] = pyqtSignal()

    def __init__(self, cameraThread: Optional[CameraThread], parent: Optional['QWidget'] = None, flags: Qt.WindowType = Qt.WindowType.Dialog) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = cameraThread

        self.calibrationWidget = CalibrationWidget(self._cameraThread, self)
        self.calibrationWidget.closed.connect(self.closeWindow)

        self.loadCalibrationFileDialog = QFileDialog(self, caption="Load calibration", filter="Numpy save format (*.npz)")
        self.loadCalibrationFileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        self.loadCalibrationFileDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        self.manualCalibrationButton.clicked.connect(self.showCalibrationWidget)
        self.loadCalibrationButton.clicked.connect(self.showLoadCalibrationFileDialog)
        self.loadCalibrationFileDialog.fileSelected.connect(self.loadCalibration)

    @property
    def cameraThread(self) -> Optional[CameraThread]:
        return self._cameraThread

    @cameraThread.setter
    def cameraThread(self, value: CameraThread) -> None:
        self._cameraThread = value
        self.calibrationWidget.cameraThread = self._cameraThread

    @pyqtSlot()
    def showCalibrationWidget(self) -> None:
        self.hide()
        self.calibrationWidget.show()

    @pyqtSlot()
    def showLoadCalibrationFileDialog(self) -> None:
        self.loadCalibrationFileDialog.show()

    @pyqtSlot(str)
    def loadCalibration(self, npzPathStr: str) -> None:
        npzPath = Path(npzPathStr)

        if npzPath.suffix == ".npz":
            try:
                self._cameraThread.camera.loadParameters(npzPath)
            except CameraError:
                logging.exception()
            finally:
                self.close()


    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)

    @pyqtSlot()
    def closeWindow(self) -> None:
        self.close()