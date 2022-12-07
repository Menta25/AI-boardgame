from PyQt6.QtWidgets import QMainWindow

from aiBoardGame.view.ui.xiangqiWindow import Ui_xiangqiWindow

class XianqiWindow(QMainWindow, Ui_xiangqiWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
