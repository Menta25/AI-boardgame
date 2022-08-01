import cv2 as cv
from pathlib import Path

from cv2 import undistort

from vision.camera import RobotCamera, Helper, Resolution


def main() -> None:
    print("Reading images")
    helper = Helper(Path("../img/calib"))

    print("Init camera")
    cam = RobotCamera(Resolution(1599,1200))
    print("Calibrating camera")
    cam.calibrate(helper.images(), (9,6))
    print("Calibration finished")

    print("Undistorting image")
    distortedBoardImage = cv.imread("../img/test3_1599x1200.jpg")  # NOTE: Different camera
    undistortedBoardImage = cam.undistort(distortedBoardImage)
    cv.imshow("asd", undistortedBoardImage)
    cv.waitKey(0)
    cv.destroyAllWindows()

    xiangqiBoard = cam.detectBoard(undistortedBoardImage)
    cv.imshow("board", cv.resize(xiangqiBoard.flatten(10, [255, 255, 255]), (500, 500)))
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
