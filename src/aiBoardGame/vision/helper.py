import cv2 as cv

from pathlib import Path
from aiBoardGame.vision.camera import RobotCameraInterface, Resolution

def main():
    paramsPath = Path("")
    camInterface = RobotCameraInterface(Resolution(1920, 1080), paramsPath)

    imgsBasePath = Path("")
    for sidePath in imgsBasePath.iterdir():
        for piecePath in sidePath.iterdir():
            for img in piecePath.iterdir():
                img = cv.imread(img.as_posix())
                img = camInterface.detectBoard(img)
                cv.imshow("piece", img)
                cv.waitKey(0)
                cv.destroyAllWindows()
                return

if __name__ == "__main__":
    main()