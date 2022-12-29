from pathlib import Path
import cv2 as cv

from aiBoardGame.vision.camera import RobotCameraInterface


class TestCamera:
    camera = RobotCameraInterface((1920, 1080), intrinsicsFile=Path("tests/data/camCalibs.npz"))

    def testBoardDetection(self) -> None:
        boardImagesRoot = Path("tests/data/boardImages")
        for path in boardImagesRoot.iterdir():
            if path.is_file() and path.suffix == ".jpg":
                image = cv.imread(path.as_posix())
                _ = self.camera.detectBoard(image)
