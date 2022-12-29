"""Convolutional neural network used for Xiangqi piece recognition"""

# pylint: disable=no-member

from __future__ import annotations

import time
import logging
from typing import Dict, List, Literal, Optional, Tuple, Union, ClassVar, cast
from pathlib import Path
import cv2 as cv
import numpy as np
import torch
from torch import Tensor
from torch.nn import Module, Linear, CrossEntropyLoss
from torch.optim import Optimizer, SGD
from torch.optim.lr_scheduler import _LRScheduler, StepLR
from torchvision.models import ResNet18_Weights
from torchvision.models.resnet import ResNet
from PIL import Image

from aiBoardGame.logic.engine import BoardEntity, Board, Position
from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XiangqiPieceDataset, XiangqiPieceDataLoader, XIANGQI_PIECE_CLASSES
from aiBoardGame.vision.xiangqiPieceClassifier.earlyStopping import EarlyStopping
from aiBoardGame.vision.boardImage import BoardImage


_WEIGHTS_PATH = Path("src/aiBoardGame/vision/xiangqiPieceClassifier/xiangqiWts.pt")


class XiangqiPieceClassifier:
    """Convolutional neural network model for classifying Xiangqi pieces achieved by transfer learning.
    Uses a pretrained ResNET18 model as a base, replaces the last fully connected layer of the
    model to suit the Xiangqi piece classification"""
    batchSize: ClassVar[int] = 32
    """Loaded image batch size"""
    epochCount: ClassVar[int] = 150
    """Maximum epochs to run training"""

    classes: ClassVar[List[Optional[BoardEntity]]] = XIANGQI_PIECE_CLASSES
    """All Xiangqi piece types and empty type"""
    baseWeightsPath: ClassVar[Path] = _WEIGHTS_PATH
    """Used for loading default model parameters"""

    def __init__(self, weights: Union[Path, Dict[str, Tensor]] = _WEIGHTS_PATH, device: str = "cpu") -> None:
        """
        :param weights: Weights used as model parameters, defaults to _WEIGHTS_PATH
        :type weights: Union[Path, Dict[str, Tensor]], optional
        :param device: CPU or GPU to use for training or prediction, defaults to "cpu"
        :type device: str, optional
        """
        self._model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', weights=ResNet18_Weights.DEFAULT if weights is None else None)
        self.model.fc = Linear(self.model.fc.in_features, len(self.classes))

        self.isTrained = False
        if weights is not None:
            self.loadWeights(weights)

        self.device = device

    @property
    def model(self) -> ResNet:
        """Model used for classifying"""
        return self._model

    @property
    def device(self) -> str:
        """Device in use"""
        return self._device

    @device.setter
    def device(self, value: str) -> None:
        self._device = value
        self.model.to(self._device)

    @staticmethod
    def getAvailableDevice() -> Literal["cuda", "cpu"]:
        """List available devices

        :return: Available devices
        :rtype: str
        """
        return "cuda" if torch.cuda.is_available() else "cpu"

    def loadWeights(self, weights: Union[Path, Dict[str, Tensor]]) -> None:
        """Load weights into model

        :param weights: File containing model parameters
        :type weights: Union[Path, Dict[str, Tensor]]
        """
        if isinstance(weights, Path):
            weights: Dict[str, Tensor] = torch.load(weights)
        self.model.load_state_dict(weights)
        self.isTrained = True

    def saveWeights(self, savePath: Path) -> None:
        """Save model weights to a file

        :param savePath: File to save to
        :type savePath: Path
        """
        torch.save(self.model.state_dict(), savePath.with_suffix(".pt"))

    def trainFromScratch(self, trainDataLoader: XiangqiPieceDataLoader, validationDataLoader: XiangqiPieceDataLoader) -> XiangqiPieceClassifier:
        """Trains the model from scratch. Freezes all pretrained ResNET18 layer, only the last layer
        remains trainable. Runs for given epoch or until early-stopping is activated, then unfreezes
        all layers and fine tunes the model

        :param trainDataLoader: DataLoader for training data
        :type trainDataLoader: XiangqiPieceDataLoader
        :param validationDataLoader: DataLoader for validation data
        :type validationDataLoader: XiangqiPieceDataLoader
        :return: Model after transfer learning
        :rtype: XiangqiPieceClassifier
        """
        criterion = CrossEntropyLoss()


        # NOTE: Freezing pretrained model and only training last layer

        for param in self.model.parameters():
            param.requires_grad = False
        for param in self.model.fc.parameters():
            param.requires_grad = True

        optimizer = SGD(self.model.parameters(), lr=1e-2, momentum=0.9)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        self._train(trainDataLoader, validationDataLoader, criterion, optimizer, scheduler)


        # NOTE: Fine Tuning

        for param in self.model.parameters():
            param.requires_grad = True

        optimizer = SGD(self.model.parameters(), lr=1e-3, momentum=0.9)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        self._train(trainDataLoader, validationDataLoader, criterion, optimizer, scheduler)

        self.isTrained = True

        return self

    def _train(
        self, trainDataLoader: XiangqiPieceDataLoader, validationDataLoader: XiangqiPieceDataLoader,
        criterion: Module, optimizer: Optimizer, scheduler: _LRScheduler
    ) -> XiangqiPieceClassifier:
        phases = {
            "train": trainDataLoader,
            "validation": validationDataLoader
        }

        earlyStopping = EarlyStopping(patience=15)

        logging.info("Started training model")
        since = time.time()

        for epoch in range(self.epochCount):
            logging.debug(f"Epoch {epoch+1}/{self.epochCount}")
            logging.debug("-"*10)

            for phase, dataLoader in phases.items():
                if phase == "train":
                    self.model.train()
                else:
                    self.model.eval()

                runningLoss = 0.0
                runningCorrects = 0

                for data in dataLoader:
                    inputs, labels = data[0].to(self.device), data[1].to(self.device)

                    optimizer.zero_grad()

                    with torch.set_grad_enabled(phase == "train"):
                        outputs = self.model(inputs)
                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        if phase == "train":
                            loss.backward()
                            optimizer.step()

                    runningLoss += loss.item() * inputs.size(0)
                    runningCorrects += torch.sum(preds == labels.data)

                if phase == "train":
                    scheduler.step()

                epochLoss = runningLoss / len(dataLoader.dataset.indices)
                epochAccuracy = runningCorrects.double() / len(dataLoader.dataset.indices)

                logging.debug(f"{phase.capitalize()} Loss: {epochLoss:.4f} Accuracy: {epochAccuracy:.4f}")

                if phase == "validation":
                    earlyStopping(self.model, epochLoss)

            if earlyStopping.isEarlyStop:
                logging.debug("")
                logging.debug("Early stopping")
                logging.debug("")
                break

            logging.debug("")

        timeElapsed = time.time() - since
        logging.info(f"Training complete in {timeElapsed // 60:.0f}m {timeElapsed % 60:.0f}s")

        self.loadWeights(earlyStopping.checkpointPath)
        return self

    def test(self, testDataLoader: XiangqiPieceDataLoader) -> None:
        """Tests model accuracy on a dataset

        :param testDataLoader: DataLoader for test data
        :type testDataLoader: XiangqiPieceDataLoader
        """
        self.model.eval()

        correctPredictions = {pieceClass: 0 for pieceClass in self.classes}
        totalPredictions = {pieceClass: 0 for pieceClass in self.classes}

        with torch.no_grad():
            for data in testDataLoader:
                inputs, labels = data[0].to(self.device), data[1].to(self.device)
                outputs = self.model(inputs)
                _, predictions = torch.max(outputs, 1)
                for label, prediction in zip(labels, predictions):
                    if label == prediction:
                        correctPredictions[self.classes[label]] += 1
                    totalPredictions[self.classes[label]] += 1

        for pieceClass, correctCount in correctPredictions.items():
            accuracy = 100 * float(correctCount) / totalPredictions[pieceClass]
            logging.info(f"Accuracy for class: {pieceClass} is {accuracy:.1f} %")

    def predict(self, inputTensor: Tensor) -> List[Optional[BoardEntity]]:
        """Predicts the piece class of the given input

        :param inputTensor: A single or a batch of piece images
        :type inputTensor: Tensor
        :return: Class of given input, can be nothing
        :rtype: List[Optional[BoardEntity]]
        """
        if len(inputTensor.shape) == 3:
            inputTensor = inputTensor.unsqueeze(0)
        elif len(inputTensor.shape) > 4:
            inputTensor = inputTensor.reshape(-1, *inputTensor.shape[-3:])

        self.model.eval()
        inputTensor = inputTensor.to(self.device)
        output = self.model(inputTensor)
        _, predictions = torch.max(output, 1)

        boardEntities = []
        for prediction in predictions:
            boardEntities.append(self.classes[prediction])
        return boardEntities

    def predictTile(self, tile: np.ndarray) -> Optional[BoardEntity]:
        """Predicts the class of a single tile

        :param tile: Tile from an image of a board
        :type tile: np.ndarray
        :raises ValueError: Invalid tile shape
        :return: Class of given tile, can be nothing
        :rtype: Optional[BoardEntity]
        """
        if not (len(tile.shape) == 3 and tile.shape[-1] == 3):
            raise ValueError("Invalid tile shape, must be (..., ..., 3)")

        return self.predict(self._cvImagesToInput(tile[np.newaxis]))[0]

    def predictBoard(self, boardImage: BoardImage, allTiles: bool = False) -> Board:
        """Predicts a board state

        :param boardImage: Image of a board
        :type boardImage: BoardImage
        :param allTiles: Use all tiles from the image or filter only the tiles that have a piece. The latter takes longer but has higher accuracy, defaults to False
        :type allTiles: bool, optional
        :return: Predicted board state
        :rtype: Board
        """
        board = Board()
        if allTiles:
            positions, tiles = [Position(file, rank) for file in range(Board.fileCount) for rank in range(Board.rankCount)], boardImage.tiles
        else:
            pieceTiles = boardImage.pieceTiles
            if len(pieceTiles) > 0:
                positions, tiles = zip(*pieceTiles)
                positions = cast(List[Position], positions)
                tiles = cast(np.ndarray, tiles)
            else:
                return board

        tilePredicts = self.predict(self._cvImagesToInput(tiles))

        for position, tilePredict in zip(positions, tilePredicts):
            if tilePredict is not None:
                side, piece = tilePredict
                board[side][position] = piece

        return board

    @staticmethod
    def _cvImagesToInput(cvImages: Tuple[np.ndarray]) -> Tensor:
        tensors = [XiangqiPieceDataset.basicTransform(Image.fromarray(cv.cvtColor(cvImage, cv.COLOR_BGR2RGB))) for cvImage in cvImages]
        return torch.stack(tensors)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    DEVICE = XiangqiPieceClassifier.getAvailableDevice()
    logging.info(f"Using {DEVICE} device")

    xiangqiDatasetRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes")
    train, validation, test = XiangqiPieceDataset.split(root=xiangqiDatasetRoot, batchSize=XiangqiPieceClassifier.batchSize, numWorkers=4)


    loadModelWeights = input("Do you want to load model weights? (yes/other) ") == "yes"
    if loadModelWeights is True:
        loadPathStr = input("Load Path: ")
        loadPath = Path(loadPathStr)
        classifier = XiangqiPieceClassifier(weights=loadPath, device=DEVICE)
    else:
        classifier = XiangqiPieceClassifier(device=DEVICE)
        classifier.trainFromScratch(train, validation)

    logging.info("")

    classifier.test(test)

    logging.info("")

    pieceImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes/BLACKChariot/15.jpg")
    pieceImage = cv.imread(pieceImagePath.as_posix())
    pieceImage = cv.cvtColor(pieceImage, cv.COLOR_BGR2RGB)

    pred = classifier.predictTile(pieceImage)
    logging.info(f"Label: {pieceImagePath.parent.name}, Prediction: {pred}")

    saveModelWeights = input("Do you want to save model weights? (yes/other) ") == "yes"
    if saveModelWeights is True:
        savePathStr = input("Save Path: ")
        savePth = Path(savePathStr)
        classifier.saveWeights(savePth)
