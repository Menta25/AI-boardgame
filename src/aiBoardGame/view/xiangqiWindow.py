import logging
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Optional, List
from PyQt6.QtWidgets import QMainWindow, QLabel, QFileDialog
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

        self.loadCalibrationFileDialog = QFileDialog(self, caption="Load calibration", filter="Numpy save format (*.npz)")
        self.loadCalibrationFileDialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        self.loadCalibrationFileDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        self.initCameraInputComboBox()
        self.initDifficultyComboBox()

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

    def connectSignals(self) -> None:
        self.cameraInputComboBox.currentTextChanged.connect(self.initCamera)
        self.manualCalibrationButton.clicked.connect(self.showManualCalibration)
        self.loadCalibrationButton.clicked.connect(self.showLoadCalibrationFileDialog)
        self.cancelCalibrationButton.clicked.connect(self.showMain)
        self.loadCalibrationFileDialog.fileSelected.connect(self.loadCalibration)

    @pyqtSlot(str)
    def initCamera(self, capturingDevice: str) -> None:
        try:
            self.calibrationPage.setEnabled(False)
            self.manualCalibrationButton.setEnabled(False)
            self.loadCalibrationButton.setEnabled(False)
            self.selectCameraView.clear()
            self.calibrationCameraView.clear()
            self.gameCameraView.clear()
            self.gameTab.setEnabled(False)
            self.camera = None
            if self.cameraThread is not None:
                self.cameraThread.join()

            self.camera = RobotCamera(feedInput=capturingDevice, resolution=(1920,1080))
            self.cameraThread = Thread(target=self.updateCameraViews, kwargs={"cameraViews": [self.selectCameraView, self.calibrationCameraView]}, name="updateCameraThread")
        except CameraError as error:
            logging.error(str(error))
        else:
            self.cameraThread.start()
            self.manualCalibrationButton.setEnabled(True)
            self.loadCalibrationButton.setEnabled(True)
            self.calibrationPage.setEnabled(True)
    
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
