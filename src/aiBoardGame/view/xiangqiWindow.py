# pylint: disable=no-name-in-module

import logging
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Optional, List
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSlot, QThread, Qt
from PyQt6.QtGui import QCloseEvent

from aiBoardGame.logic import Difficulty, Board
from aiBoardGame.logic.engine.utility import prettyBoard
from aiBoardGame.vision import RobotCamera, CameraError, BoardImage

from aiBoardGame.view.ui.xiangqiWindow import Ui_xiangqiWindow
from aiBoardGame.view.utility import imageToPixmap

from aiBoardGame.game import Xiangqi, HumanPlayer, RobotArmPlayer, GameplayError, PlayerError, utils
from aiBoardGame.robot import RobotArm, RobotArmException


UPDATE_INTERVAL = 0.1


class XianqiWindow(QMainWindow, Ui_xiangqiWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.camera: Optional[RobotCamera] = None
        self.cameraThread: Optional[Thread] = None

        self.robotArm: Optional[RobotArm] = None

        self.redSide: Optional[HumanPlayer] = None
        self.blackSide: Optional[RobotArmPlayer] = None
        self.game: Optional[Xiangqi] = None
        self.gameThread: Optional[QThread] = None

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
        self.newGameButton.clicked.connect(self.newGame)
        self.difficultyComboBox.currentTextChanged.connect(self.onDifficultyChange)

    @pyqtSlot(str)
    def initCamera(self, capturingDevice: str) -> None:
        try:
            self.resetCameraWidgets()

            self.camera = RobotCamera(feedInput=capturingDevice, resolution=(1920,1080))
            self.camera.activate()
            self.cameraThread = Thread(target=self.updateCameraViews, kwargs={"cameraViews": [self.selectCameraView, self.calibrationCameraView]}, name="updateCameraThread")
        except CameraError as error:
            logging.error(str(error))
        else:
            self.cameraThread.start()
            self.manualCalibrationButton.setEnabled(True)
            self.loadCalibrationButton.setEnabled(True)
            self.calibrationPage.setEnabled(True)

    @pyqtSlot()
    def newGame(self) -> None:
        try:
            if self.game is None:
                self.robotArm = RobotArm(speed=500_000)
                self.redSide = HumanPlayer()
                self.blackSide = RobotArmPlayer(arm=self.robotArm, camera=self.camera, difficulty=Difficulty[self.difficultyComboBox.currentText()])
                self.game = Xiangqi(camera=self.camera, redSide=self.redSide, blackSide=self.blackSide)
            else:
                self.gameThread.terminate()
                self.gameCameraView.clear()
                self.boardFENLabel.clear()
        except (CameraError, RobotArmException, PlayerError, GameplayError) as error:
            messageBox = QMessageBox(QMessageBox.Icon.Warning, "Error", "An error has occurred", buttons=QMessageBox.StandardButton.Ok, parent=self)
            messageBox.setDetailedText(str(error))
            messageBox.setTextFormat(Qt.TextFormat.AutoText)
            messageBox.exec()
        else:
            self.initGameThread()
            self.newGameButton.setEnabled(False)

    def initGameThread(self) -> None:
        self.gameThread = QThread()
        self.game.moveToThread(self.gameThread)
        self.redSide.moveToThread(self.gameThread)
        self.blackSide.moveToThread(self.gameThread)
        utils.moveToThread(self.gameThread)
        self.gameThread.started.connect(self.game.play)
        self.connectGameSignals()
        self.gameThread.start()

    def connectGameSignals(self) -> None:
        self.redSide.prepareStarted.connect(self.onPrepareStarted)
        self.redSide.makeMoveStarted.connect(self.onMakeMoveStarted)
        self.blackSide.loadLastCalibration.connect(self.onLoadLastCalibration)
        self.blackSide.calibrateCorner.connect(self.onCalibrateCorner)
        self.game.turnChanged.connect(self.updateTurnLabel)
        self.game.engineUpdated.connect(self.updateBoardFENLabel)
        self.game.over.connect(self.onGameOver)
        self.game.newBoardImage.connect(self.updateGameCameraView)
        self.game.invalidStartPosition.connect(self.onInvalidStartPosition)
        self.game.invalidMove.connect(self.onInvalidMove)
        utils.waitForCorrection.connect(self.onWaitForCorrection)
        utils.statusUpdate.connect(self.updateStatusBar)

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

    @pyqtSlot(BoardImage)
    def updateGameCameraView(self, boardImage: BoardImage) -> None:
        qtPixmap = imageToPixmap(boardImage.roi, self.gameCameraView.width(), self.gameCameraView.height())
        self.gameCameraView.setPixmap(qtPixmap)

    @pyqtSlot(str)
    def updateBoardFENLabel(self, fen: str) -> None:
        self.boardFENLabel.setText(prettyBoard(fen))

    @pyqtSlot(str)
    def updateStatusBar(self, status: str) -> None:
        self.statusBar.showMessage(status)

    @pyqtSlot(int)
    def updateTurnLabel(self, turn: int) -> None:
        self.turnLabel.setText(f"Turn {turn}")

    @pyqtSlot()
    def onGameOver(self) -> None:
        side, player = self.game.winner
        QMessageBox.information(self, "Game Over", f"{side.name} {player.__class__.__name__} won!", defaultButton=QMessageBox.StandardButton.Ok)
        self.newGameButton.setEnabled(True)

    @pyqtSlot(str)
    def onCalibrateCorner(self, corner: str) -> None:
        QMessageBox.information(self, "Robot Arm Calibration", f"Press OK if you've moved the robot arm to the {corner} corner (from the perspective of the RED side)", defaultButton=QMessageBox.StandardButton.Ok)
        utils.continueRun()

    @pyqtSlot(Board)
    def onInvalidStartPosition(self, board: Board) -> None:
        messageBox = QMessageBox(QMessageBox.Icon.Warning, "Invalid Start Position", "Press OK if you've set up start position", buttons=QMessageBox.StandardButton.Ok, parent=self)
        messageBox.setDetailedText(f"{board.fen}\n\n{prettyBoard(board)}")
        messageBox.setTextFormat(Qt.TextFormat.AutoText)
        messageBox.exec()
        utils.continueRun()

    @pyqtSlot(str, str)
    def onInvalidMove(self, errorMessage: str, fen: str) -> None:
        messageBox = QMessageBox(QMessageBox.Icon.Warning, "Invalid Move", "Press OK if you've corrected the previous move", buttons=QMessageBox.StandardButton.Ok, parent=self)
        messageBox.setDetailedText(f"{errorMessage}\n\n{fen}\n\n{prettyBoard(fen)}")
        messageBox.setTextFormat(Qt.TextFormat.AutoText)
        messageBox.exec()
        utils.continueRun()

    @pyqtSlot()
    def onPrepareStarted(self) -> None:
        QMessageBox.information(self, "Player Preparation", "Press OK if you've prepared for the game", defaultButton=QMessageBox.StandardButton.Ok)
        utils.continueRun()

    @pyqtSlot(str)
    def onDifficultyChange(self, difficulty: str) -> None:
        if self.game is not None:
            for side in self.game.sides.values():
                if isinstance(side, RobotArmPlayer):
                    side.difficulty = Difficulty[difficulty]

    @pyqtSlot(str)
    def onWaitForCorrection(self, message: str) -> None:
        QMessageBox.information(self, "Wating For Correction", message, defaultButton=QMessageBox.StandardButton.Ok)
        utils.continueRun()

    @pyqtSlot()
    def onMakeMoveStarted(self) -> None:
        QMessageBox.information(self, "Player's Turn", "Press OK if you've made your move", defaultButton=QMessageBox.StandardButton.Ok)
        utils.continueRun()

    @pyqtSlot()
    def onLoadLastCalibration(self) -> None:
        reply = QMessageBox.question(self, "Load Calibration", "Do you want to load last game's robot arm calibration?", defaultButton=QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            self.blackSide.loadCalibration()
        utils.continueRun()

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
            QMessageBox.critical(self, "Calibration", "Calibration failed", defaultButton=QMessageBox.StandardButton.Ok)
        else:
            reply = QMessageBox.question(self, "Save Calibration", "Do you want to save the parameters used for camera calibration?", defaultButton=QMessageBox.StandardButton.Yes)
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

    def closeEvent(self, event: QCloseEvent) -> None:
        self.camera = None
        if self.cameraThread is not None:
            self.cameraThread.join()
        if self.gameThread is not None:
            self.gameThread.terminate()
        return super().closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication  # pylint: disable=ungrouped-imports

    logging.basicConfig(level=logging.INFO, format="")

    app = QApplication([])
    window = XianqiWindow()
    window.show()
    sys.exit(app.exec())
