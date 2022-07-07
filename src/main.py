import cv2 as cv

from vision.detection import detectBoard


def main() -> None:
    inputImage = cv.imread("../img/test3.jpg")
    xiangqi = detectBoard(inputImage)
    cv.imshow("board", cv.resize(xiangqi.flatten(10, [255, 255, 255]), (500, 500)))
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
