import logging
import cv2 as cv
import numpy as np
from typing import Iterator
from pathlib import Path
from dataclasses import dataclass

from vision.camera import RobotCamera, Resolution


logging.basicConfig(level=logging.DEBUG)

@dataclass
class Helper:
    path: Path

    def images(self) -> Iterator[np.ndarray]:
        imageFiles = self.path.glob("*.jpg")
        for imageFile in imageFiles:
            yield cv.imread(imageFile.as_posix())


def main() -> None:
    logging.info("Reading images")
    helper = Helper(Path("../img/calib"))

    cam = RobotCamera(Resolution(3648, 2736))
    cam.calibrate(helper.images(), (8,6))

    distortedBoardImage = cv.imread("../img/test3.jpg")
    undistortedBoardImage = cam.undistort(distortedBoardImage)
    xiangqiBoard = cam.detectBoard(undistortedBoardImage)
    cv.imshow("board", cv.resize(xiangqiBoard.flatten(10, [255, 255, 255]), (500, 500)))
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
