import cv2 as cv

def main():
    bruh = returnCameraIndexes()
    print(bruh)
    # cap = cv.VideoCapture(bruh[0])
    # ret, frame = cap.read()
    # cv.imshow("cam", frame)
    # cv.waitKey()
    # cv.destroyAllWindows()
    # cap.release()

def returnCameraIndexes():
    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        cap = cv.VideoCapture(index)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
        i -= 1
    return arr

if __name__ == "__main__":
    main()
