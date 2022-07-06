import cv2 as cv
import numpy as np


def main():
    image: np.ndarray = cv.imread("../../img/test.jpg")
    out = image.copy()

    arucoDict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_50)
    arucoParams = cv.aruco.DetectorParameters_create()

    markerCorners, markerIds, rejectedCandidates = cv.aruco.detectMarkers(image, arucoDict, parameters=arucoParams)
    cv.aruco.drawDetectedMarkers(out, markerCorners, markerIds)
    out = cv.resize(out, (1000, 1000))
    cv.imshow("image", out)
    cv.waitKey(0)


if __name__ == "__main__":
    main()
