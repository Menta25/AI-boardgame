"""Utility functions to generate dataset from raw images"""

# pylint: disable=no-member

from pathlib import Path
from enum import Enum, auto, unique
from typing import Tuple, Optional, Literal, overload, Generator
import numpy as np
import cv2 as cv

from aiBoardGame.vision.camera import RobotCameraInterface, CameraError
from aiBoardGame.vision.boardImage import BoardImage
from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XIANGQI_PIECE_CLASSES


XIANGQI_PIECE_CLASSES_STR = [str(xiangqiClass) for xiangqiClass in XIANGQI_PIECE_CLASSES]

@unique
class GenerateMode(Enum):
    """Enum class for specifying generation target"""
    DATA = auto()
    ROI = auto()
    TILES = auto()
    PIECES = auto()


def getBoardImage(image: np.ndarray, camera: Optional[RobotCameraInterface]) -> BoardImage:
    """Generate board image from raw image

    :param image: Raw image path
    :type image: np.ndarray
    :param camera: Camera for prespective transform
    :type camera: Optional[RobotCameraInterface]
    :return: Generated board image
    :rtype: BoardImage
    """
    if camera is not None:
        return camera.detectBoard(camera.undistort(image))
    else:
        return BoardImage(data=image)


def iterateDataset(rawImagesRoot: Path) -> Generator[Tuple[np.ndarray, Path], None, None]:
    """Get dataset generator

    :param rawImagesRoot: Raw image root path
    :type rawImagesRoot: Path
    :yield: Raw image and its path
    :rtype: Generator[Tuple[BoardImage, Path], None, None]
    """
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
    """Main function to generate dataset

    :param rawImagesRoot: Raw image root path
    :type rawImagesRoot: Path
    :param destinationRoot: Destination path to save generated dataset
    :type destinationRoot: Path
    :param camera: Camera for prespective transform
    :type camera: Optional[RobotCameraInterface]
    :param generate: Generation target
    :type generate: GenerateMode
    """
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
    """Save pieces from board image

    :param destinationRoot: Destination path to save pieces
    :type destinationRoot: Path
    :param boardImage: Board image to search pieces on
    :type boardImage: BoardImage
    :param rawImagePath: Raw image to generate board image from
    :type rawImagePath: Path
    """
    object.__setattr__(boardImage, "pieceThresholdDivisor", 2.1)
    pieceImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not pieceImagesDir.exists():
        pieceImagesDir.mkdir(parents=True, exist_ok=True)
    offset = len([path for path in pieceImagesDir.iterdir() if path.suffix == ".jpg"])
    pieces = boardImage.pieceTiles
    if len(pieces) == 0:
        print(rawImagePath, "None")
    for j, (_, pieceImage) in enumerate(pieces, start=offset):
        pieceImagePath = Path(pieceImagesDir, f"{j}.jpg")
        cv.imwrite(pieceImagePath.as_posix(), pieceImage)


def saveTiles(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    """Save tiles from board image

    :param destinationRoot: Destination path to save tiles
    :type destinationRoot: Path
    :param boardImage: Board image to extract tiles from
    :type boardImage: BoardImage
    :param rawImagePath: Raw image to generate board image from
    :type rawImagePath: Path
    """
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
    """Save data from board image

    :param destinationRoot: Destination path to save data
    :type destinationRoot: Path
    :param boardImage: Board image to extract data from
    :type boardImage: BoardImage
    :param rawImagePath: Raw image to generate board image from
    :type rawImagePath: Path
    """
    dataImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not dataImagesDir.exists():
        dataImagesDir.mkdir(parents=True, exist_ok=True)
    dataPath = Path(dataImagesDir, rawImagePath.name)
    cv.imwrite(dataPath.as_posix(), boardImage.data)


def saveROI(destinationRoot: Path, boardImage: BoardImage, rawImagePath: Path) -> None:
    """Save ROI from board image

    :param destinationRoot: Destination path to save ROI
    :type destinationRoot: Path
    :param boardImage: Board image to extract ROI from
    :type boardImage: BoardImage
    :param rawImagePath: Raw image to generate board image from
    :type rawImagePath: Path
    """
    roiImagesDir = Path(destinationRoot, rawImagePath.parent.name)
    if not roiImagesDir.exists():
        roiImagesDir.mkdir(parents=True, exist_ok=True)
    roiPath = Path(roiImagesDir, rawImagePath.name)
    cv.imwrite(roiPath.as_posix(), boardImage.roi)


if __name__ == "__main__":
    cam = RobotCameraInterface(resolution=(1920, 1080), intrinsicsFile=Path("/home/Menta/Workspace/Projects/AI-boardgame/newCamCalibs.npz"))
    rawImgsRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/zips/basic")
    destRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes4")
    gen = GenerateMode.DATA
    generateTrainDataset(rawImgsRoot, destRoot, cam, gen)
