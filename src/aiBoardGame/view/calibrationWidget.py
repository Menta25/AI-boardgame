import logging
from pathlib import Path
from typing import Optional, ClassVar
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.view.cameraThread import CameraThread
from aiBoardGame.view.cameraFeed import CameraFeed

from aiBoardGame.vision.camera import RobotCameraInterface, CameraError


_UI_PATH = Path("src/aiBoardGame/view/ui/calibrationWidget.ui")


class CalibrationWidget(QWidget):
    closed: ClassVar[pyqtSignal] = pyqtSignal()

    def __init__(self, cameraThread: Optional[CameraThread], parent: Optional[QWidget] = None, flags: Qt.WindowType = Qt.WindowType.Widget) -> None:
        super().__init__(parent, flags)
        uic.load_ui.loadUi(_UI_PATH.as_posix(), self)

        self._cameraThread = cameraThread
        self.cameraFeedLabel = CameraFeed(self._cameraThread)
        self.calibrationLayout.insertWidget(1, self.cameraFeedLabel, stretch=1)

        self.calibrateButton.setEnabled(self._cameraThread is not None)

        self.calibrationProgressBar.setMaximum(RobotCameraInterface.calibrationMinPatternCount)
        self._calibrationImages = []
        self.calibrateButton.clicked.connect(self.collectCalibrationImage)

    def setVerticiesSpinBoxEnabled(self, value: bool) -> None:
        self.horizontalVerticiesSpinBox.setEnabled(value)
        self.verticalVerticiesSpinBox.setEnabled(value)

    def resetWidget(self) -> None:
        self.setVerticiesSpinBoxEnabled(True)
        self._calibrationImages.clear()
        self.calibrationProgressBar.setValue(0)

    @pyqtSlot()
    def collectCalibrationImage(self) -> None:
        image = self._cameraThread.image
        if RobotCameraInterface.isSuitableForCalibration(image, checkerBoardShape=(self.horizontalVerticiesSpinBox.value(), self.verticalVerticiesSpinBox.value())):
            if self.horizontalVerticiesSpinBox.isEnabled() or self.verticalVerticiesSpinBox.isEnabled():
                self.setVerticiesSpinBoxEnabled(False)

            self._calibrationImages.append(image)
            self.calibrationProgressBar.setValue(len(self._calibrationImages))

            if len(self._calibrationImages) >= RobotCameraInterface.calibrationMinPatternCount:
                self.calibrateCamera()

    def calibrateCamera(self) -> None:
        try:
            self._cameraThread.camera.calibrate(checkerBoardImages=self._calibrationImages, checkerBoardShape=(self.horizontalVerticiesSpinBox.value(), self.verticalVerticiesSpinBox.value()))
        except CameraError:
            logging.exception("Calibration failed")
            QMessageBox(title="Calibration", text="Calibration failed", buttons=QMessageBox.StandardButton.Ok, parent=self).show()
        else:
            reply = QMessageBox.question(self, "Save Calibration", "Do you want to save the parameters used for camera calibration?")
            if reply == QMessageBox.StandardButton.Yes:
                self.showSaveCalibrationFileDialog()
            self.hide()
        finally:
            self.resetWidget()

    def showSaveCalibrationFileDialog(self) -> None:
        fileName, _ = QFileDialog.getSaveFileName(self, caption="Save calibration", filter="Numpy save format (*.npz)")
        savePath = Path(fileName).with_suffix(".npz")
        self._cameraThread.camera.saveParameters(savePath)

    def hide(self) -> None:
        self.closed.emit()
        return super().hide()

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)