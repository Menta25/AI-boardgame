from typing import Tuple
import numpy as np
import cv2 as cv
from pathlib import Path

from aiBoardGame.vision.camera import RobotCameraInterface, Resolution, CameraError
from aiBoardGame.vision.boardImage import BoardImage


def searchParams(camera: RobotCameraInterface, imagesPath: Path) -> Tuple[int, float, int, int]:
    for imagePath in imagesPath.iterdir():
        # if imagePath.stem in ["31"]:
        image = cv.imread(imagePath.as_posix())
        image = camera.undistort(image)

        board = camera.detectBoard(image)
        # board = BoardImage(data=cv.imread(imagePath.as_posix()).copy())
        board.pieces

        # for file in board.positions: 
        #     for tileCenter in file:
        #         cv.circle(board.data, tileCenter, 1, (255,0,0), 2)

        cv.imshow(f"{imagePath}", board.roi)
        cv.waitKey(0)
        cv.destroyAllWindows()


if __name__ == "__main__":
    camera = RobotCameraInterface(resolution=Resolution(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz"))

    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/BlackAdvisor")
    # searchParams(camera, imagesPath)

    imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/RedSoldier")
    searchParams(camera, imagesPath)

    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board")
    # searchParams(camera, imagesPath)

    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/BlackGeneral")
    # searchParams(camera, imagesPath)

    # imagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/BlackGeneral/58.jpg")
    # bruh(camera, imagePath)
    
    # imagesPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic/RedSoldier")
    # searchParams(camera, imagesPath)