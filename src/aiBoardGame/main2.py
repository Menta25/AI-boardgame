from pathlib import Path
import cv2 as cv

from aiBoardGame.logic.engine.utility import boardToStr
from aiBoardGame.vision import XiangqiPieceClassifier, RobotCamera, RobotCameraInterface, Resolution

def main():
    classifier = XiangqiPieceClassifier(weights=Path("xiangqiWts.pt"))
    # camera = RobotCamera(2, Resolution(1920, 1080), intrinsicsFile=Path("newCamCalibs.npz"))


    # boardImage = camera.detectBoard(camera.read(undistorted=True))
    camera = RobotCameraInterface(resolution=(1920,1080), intrinsicsFile=Path("newCamCalibs.npz"))
    boardImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/board/example0.jpg")

    boardImage = camera.detectBoard(camera.undistort(cv.imread(boardImagePath.as_posix())))

    cv.imshow("board roi", boardImage.roi)
    cv.waitKey(0)

    # tiles = boardImage.tiles

    # print(tiles.shape)
    # print(boardImage.positions.shape)

    board = classifier.predictBoard(boardImage)

    print(boardToStr(board))

    print(classifier.predictTile(boardImage[1,4]))

    # for i, file in enumerate(boardImage.tiles):
    #     for j, tile in enumerate(file):
    #         cv.imshow(f"{board[i,j]}", tile)
    #         cv.waitKey(0)
    #         cv.destroyAllWindows()

    # tile = boardImage[2,6].copy()

    # blurredBoard = cv.medianBlur(tile, 5)
    # grayBlurredBoard = cv.cvtColor(blurredBoard, cv.COLOR_BGR2GRAY)

    # import numpy as np

    # pieces = cv.HoughCircles(grayBlurredBoard, cv.HOUGH_GRADIENT, dp=1.5, minDist=tile.shape[0], param1=30, param2=46, minRadius=int(tile.shape[0]/3.0), maxRadius=int(tile.shape[0]/2.0))
    # print(pieces[0])
    # for piece in pieces[0].astype(np.uint16):
    #     center = piece[0:2]
    #     radius = piece[2]
    #     cv.circle(tile, center, 2, (0,0,255), 3)
    #     cv.circle(tile, center, radius, (0,255,0), 3)
    # cv.imshow("tile", tile)
    # cv.waitKey(0)


if __name__ == "__main__":
    main()
    cv.destroyAllWindows()