# pylint: disable=no-name-in-module

import sys
import logging
from PyQt6.QtWidgets import QApplication

from aiBoardGame.view.xiangqiWindow import XianqiWindow

logging.basicConfig(format="[{levelname:.1s}] [{asctime}.{msecs:<3.0f}] {module:>8} : {message}", datefmt="%H:%M:%S", style="{", level=logging.INFO)


def main() -> None:
    app = QApplication([])
    window = XianqiWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
