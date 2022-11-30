import numpy as np
import cv2 as cv
from pathlib import Path
from enum import Enum, auto, unique
from typing import Tuple, Optional, Literal, overload, Generator

from aiBoardGame.vision.camera import RobotCameraInterface, CameraError
from aiBoardGame.vision.boardImage import BoardImage
from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XIANGQI_PIECE_CLASSES


XIANGQI_PIECE_CLASSES_STR = [str(xiangqiClass) for xiangqiClass in XIANGQI_PIECE_CLASSES]

@unique
class GenerateMode(Enum):
    DATA = auto()
    ROI = auto()
    TILES = auto()
    PIECES = auto()


def getBoardImage(image: np.ndarray, camera: Optional[RobotCameraInterface]) -> BoardImage:
    if camera is not None:
        return camera.detectBoard(camera.undistort(image))
    else:
        return BoardImage(data=image)


def iterateDataset(rawImagesRoot: Path) -> Generator[Tuple[BoardImage, Path], None, None]:
    for rawImagesPath in rawImagesRoot.iterdir():
        if rawImagesPath.is_dir() and rawImagesPath.name in XIANGQI_PIECE_CLASSES_STR:
            for rawImagePath in rawImagesPath.iterdir():
                if rawImagePath.suffix == ".jpg":
                    rawImage = cv.imread(rawImagePath.as_posix())
                    yield rawImage, rawImagePath


@overload
def generateTrainDataset(rawImagesRoot: Path, destinationRoot: Path, camera: Literal[None], generate: Literal[GenerateMode.ROI, GenerateMode.TILES, GenerateMode.PIECES]) -> None:
    ...


@overload
def generateTrainDataset(rawImagesRoot: Path, destinationRoot: Path, camera: RobotCameraInterface, generate: Literal[GenerateMode.DATA, GenerateMode.ROI, GenerateMode.TILES, GenerateMode.PIECES]) -> None:
    ...


def generateTrainDataset(rawImagesRoot: Path, destinationRoot: Path, camera: Optional[RobotCameraInterface], generate: GenerateMode) -> None:
    for rawImage, rawImagePath in iterateDataset(rawImagesRoot):
        try:
            boardImage = getBoardImage(rawImage, camera)
            xiangqiClass = rawImagePath.parent.name
            if generate == GenerateMode.PIECES:
                if xiangqiClass == "None":
                    saveTiles(destinationRoot, boardImage, rawImagePath)
                else:
                    savePieces(destinationRoot, boardImage, rawImagePath)
            elif generate == GenerateMode.TILES:
               saveTiles(destinationRoot, boardImage, rawImagePath)
            elif generate == GenerateMode.DATA:
                saveData(destinationRoot, boardImage, rawImagePath)
            elif generate == GenerateMode.ROI:
                saveROI(destinationRoot, boardImage, rawImagePath)
        except CameraError:
            print(rawImagePath, "Error")


def savePieces(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    object.__setattr__(boardImage, "pieceThresholdDivisor", 2.1)
    pieceImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not pieceImagesDir.exists():
        pieceImagesDir.mkdir(parents=True, exist_ok=True)
    offset = len([path for path in pieceImagesDir.iterdir() if path.suffix == ".jpg"])
    pieces = boardImage.pieces
    if len(pieces) == 0:
        print(rawImagePath, "None")
    for j, (_, pieceImage) in enumerate(pieces, start=offset):
        pieceImagePath = Path(pieceImagesDir, f"{j}.jpg")
        cv.imwrite(pieceImagePath.as_posix(), pieceImage)


def saveTiles(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    xiangqiClass = rawImagePath.parent.name
    tileImagesDir = Path(destinationRoot, xiangqiClass)
    if not tileImagesDir.exists():
        tileImagesDir.mkdir(parents=True, exist_ok=True)
    j = len([path for path in tileImagesDir.iterdir() if path.suffix == ".jpg"])
    for tilesInFile in boardImage.tiles:
        for tile in tilesInFile:
            if xiangqiClass == "None":
                offset = ((np.asarray(tile.shape[0:2]) - np.array([boardImage.fileStep, boardImage.rankStep]))/2).astype(int)
                tile = tile[offset[1]:-offset[1], offset[0]:-offset[0]]
            tileImagePath = Path(destinationRoot, xiangqiClass, f"{j}.jpg")
            cv.imwrite(tileImagePath.as_posix(), tile)
            j += 1


def saveData(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    dataImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not dataImagesDir.exists():
        dataImagesDir.mkdir(parents=True, exist_ok=True)
    dataPath = Path(dataImagesDir, rawImagePath.name)
    cv.imwrite(dataPath.as_posix(), boardImage.data)


def saveROI(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    roiImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not roiImagesDir.exists():
        roiImagesDir.mkdir(parents=True, exist_ok=True)
    roiPath = Path(roiImagesDir, rawImagePath.name)
    cv.imwrite(roiPath.as_posix(), boardImage.roi)


if __name__ == "__main__":
    camera = RobotCameraInterface(resolution=(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz"))
    rawImagesRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic")
    destinationRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes4")
    generate = GenerateMode.DATA
    generateTrainDataset(rawImagesRoot, destinationRoot, camera, generate)
