from typing import Tuple
import numpy as np
import cv2 as cv
from pathlib import Path

from aiBoardGame.vision.camera import RobotCameraInterface, Resolution, CameraError
from aiBoardGame.vision.boardImage import BoardImage


def searchParams(camera: RobotCameraInterface, imagesPath: Path) -> Tuple[int, float, int, int]:
    for imagePath in imagesPath.iterdir():
        # if imagePath.stem == "board2":
        image = cv.imread(imagePath.as_posix())
        image = camera.undistort(image)

        board = camera.detectBoard(image)
        # board = BoardImage(data=cv.imread(imagePath.as_posix()).copy())
        board.pieces
        cv.imshow(f"{imagePath}", board.roi)
        cv.waitKey(0)
        cv.destroyAllWindows()
        print("\n"*3)


if __name__ == "__main__":
    camera = RobotCameraInterface(resolution=Resolution(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz"))

    imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/BlackAdvisor")
    searchParams(camera, imagesPath)

    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/Black/BlackAdvisor")
    # searchParams(camera, imagesPath)

    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board")
    # searchParams(camera, imagesPath)
