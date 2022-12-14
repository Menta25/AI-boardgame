import logging
import numpy as np
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Optional, List
from PyQt6.QtWidgets import QMainWindow, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.logic import Difficulty
from aiBoardGame.vision import RobotCamera, CameraError

from aiBoardGame.view.ui.xiangqiWindow import Ui_xiangqiWindow
from aiBoardGame.view.utility import imageToPixmap


UPDATE_INTERVAL = 0.1


class XianqiWindow(QMainWindow, Ui_xiangqiWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.camera: Optional[RobotCamera] = None
        self.cameraThread: Optional[Thread] = None

        self.calibrationImages: List[np.ndarray] = []

        self.initCameraInputComboBox()
        self.initDifficultyComboBox()
        self.initLoadCalibrationFileDialog()
        self.initCalibrationProgressBar()

        self.connectSignals()

    def initCameraInputComboBox(self) -> None:
        for capturingDevice in Path("/dev").glob("video*"):
            self.cameraInputComboBox.addItem(capturingDevice.as_posix())
        self.cameraInputComboBox.setCurrentIndex(-1)

    def initDifficultyComboBox(self) -> None:
        difficultyCount = 0
        for difficulty in Difficulty:
            self.difficultyComboBox.addItem(difficulty.name)
            difficultyCount += 1
        self.difficultyComboBox.setCurrentIndex(difficultyCount // 2)

    def initLoadCalibrationFileDialog(self) -> None:
        fileDialog = QFileDialog(self, caption="Load calibration", filter="Numpy save format (*.npz)")
        fileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.loadCalibrationFileDialog = fileDialog

    def initCalibrationProgressBar(self) -> None:
        self.calibrationProgressBar.setMaximum(RobotCamera.calibrationMinPatternCount)

    def connectSignals(self) -> None:
        self.cameraInputComboBox.currentTextChanged.connect(self.initCamera)
        self.manualCalibrationButton.clicked.connect(self.showManualCalibration)
        self.loadCalibrationButton.clicked.connect(self.showLoadCalibrationFileDialog)
        self.calibrateButton.clicked.connect(self.collectCalibrationImage)
        self.cancelCalibrationButton.clicked.connect(self.showMain)
        self.loadCalibrationFileDialog.fileSelected.connect(self.loadCalibration)

    @pyqtSlot(str)
    def initCamera(self, capturingDevice: str) -> None:
        try:
            self.resetCameraWidgets()

            self.camera = RobotCamera(feedInput=capturingDevice, resolution=(1920,1080))
            self.cameraThread = Thread(target=self.updateCameraViews, kwargs={"cameraViews": [self.selectCameraView, self.calibrationCameraView]}, name="updateCameraThread")
        except CameraError as error:
            logging.error(str(error))
        else:
            self.cameraThread.start()
            self.manualCalibrationButton.setEnabled(True)
            self.loadCalibrationButton.setEnabled(True)
            self.calibrationPage.setEnabled(True)

    def resetCameraWidgets(self) -> None:
        self.calibrationPage.setEnabled(False)
        self.manualCalibrationButton.setEnabled(False)
        self.loadCalibrationButton.setEnabled(False)
        self.selectCameraView.clear()
        self.calibrationCameraView.clear()
        self.resetCalibration()
        self.gameCameraView.clear()
        self.gameTab.setEnabled(False)
        self.camera = None
        if self.cameraThread is not None:
            self.cameraThread.join()
    
    def updateCameraViews(self, cameraViews: List[QLabel]) -> None:
        while self.camera is not None:
            image = self.camera.read(undistorted=False)
            for cameraLabel in cameraViews:
                qtPixmap = imageToPixmap(image, cameraLabel.width(), cameraLabel.height())
                cameraLabel.setPixmap(qtPixmap)
            sleep(UPDATE_INTERVAL)

    @pyqtSlot()
    def showManualCalibration(self) -> None:
        self.stackedWidget.setCurrentIndex(1)

    @pyqtSlot()
    def showMain(self) -> None:
        self.stackedWidget.setCurrentIndex(0)

    @pyqtSlot()
    def showLoadCalibrationFileDialog(self) -> None:
        self.loadCalibrationFileDialog.show()

    @pyqtSlot(str)
    def loadCalibration(self, calibrationPathStr: str) -> None:
        if self.camera is not None:
            calibrationPath = Path(calibrationPathStr)
            if calibrationPath.suffix == ".npz":
                try:
                    self.camera.loadParameters(calibrationPath)
                except CameraError as error:
                    logging.error(str(error))
                else:
                    self.onCalibrated()

    @pyqtSlot()
    def collectCalibrationImage(self) -> None:
        image = self.camera.read(undistorted=False)
        if RobotCamera.isSuitableForCalibration(image, checkerBoardShape=(self.horizontalVerticiesSpinBox.value(), self.verticalVerticiesSpinBox.value())):
            if self.horizontalVerticiesSpinBox.isEnabled() or self.verticalVerticiesSpinBox.isEnabled():
                self.horizontalVerticiesSpinBox.setEnabled(False)
                self.verticalVerticiesSpinBox.setEnabled(False)

            self.calibrationImages.append(image)
            self.calibrationProgressBar.setValue(len(self.calibrationImages))

            if len(self.calibrationImages) >= RobotCamera.calibrationMinPatternCount:
                self.calibrateCamera()
    
    def calibrateCamera(self) -> None:
        try:
            self.camera.calibrate(checkerBoardImages=self.calibrationImages, checkerBoardShape=(self.horizontalVerticiesSpinBox.value(), self.verticalVerticiesSpinBox.value()))
        except CameraError:
            logging.exception("Calibration failed")
            QMessageBox(title="Calibration", text="Calibration failed", buttons=QMessageBox.StandardButton.Ok, parent=self).show()
        else:
            reply = QMessageBox.question(self, "Save Calibration", "Do you want to save the parameters used for camera calibration?")
            if reply == QMessageBox.StandardButton.Yes:
                self.showSaveCalibrationFileDialog()
        finally:
            self.resetCalibration()

    def showSaveCalibrationFileDialog(self) -> None:
        fileName, _ = QFileDialog.getSaveFileName(self, caption="Save calibration", filter="Numpy save format (*.npz)")
        savePath = Path(fileName).with_suffix(".npz")
        self.camera.saveParameters(savePath)
            
    def resetCalibration(self) -> None:
        self.horizontalVerticiesSpinBox.setEnabled(True)
        self.verticalVerticiesSpinBox.setEnabled(True)
        self.calibrationProgressBar.setValue(0)

    def onCalibrated(self) -> None:
        self.gameTab.setEnabled(True)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.camera = None
        if self.cameraThread is not None:
            self.cameraThread.join()
        return super().closeEvent(a0)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    window = XianqiWindow()
    window.show()
    sys.exit(app.exec())
