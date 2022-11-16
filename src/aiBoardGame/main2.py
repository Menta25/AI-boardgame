from pathlib import Path
import cv2 as cv

from aiBoardGame.logic.engine.utility import boardToStr
from aiBoardGame.vision import XiangqiPieceClassifier, RobotCamera, Resolution

def main():
    classifier = XiangqiPieceClassifier(weights=Path("newModelParams.pt"))
    camera = RobotCamera(2, Resolution(1920, 1080), intrinsicsFile=Path("camCalibs.npz"))


    boardImage = camera.detectBoard(camera.read(undistorted=True))

    cv.imshow("board roi", boardImage.roi)
    cv.waitKey(0)

    tiles = boardImage.tiles

    print(tiles.shape)
    print(boardImage.positions.shape)

    board = classifier.predictBoard(boardImage)

    print(boardToStr(board))

    print(classifier.predictTile(boardImage[1,4]))

    # for i, file in enumerate(boardImage.tiles):
    #     for j, tile in enumerate(file):
    #         cv.imshow(f"{board[i,j]}", tile)
    #         cv.waitKey(0)
    #         cv.destroyAllWindows()


if __name__ == "__main__":
    main()
    cv.destroyAllWindows()