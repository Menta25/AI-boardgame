import sys
import logging
from PyQt6.QtWidgets import QApplication

from aiBoardGame.view.mainWindow import MainWindow

logging.basicConfig(format="[{levelname:.1s}] [{asctime}.{msecs:<3.0f}] {module:>8} : {message}", datefmt="%H:%M:%S", style="{", level=logging.INFO)


def main() -> None:
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
