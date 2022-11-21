from __future__ import annotations

import time
import torch
import logging
import cv2 as cv
import numpy as np
from pathlib import Path
from torch import Tensor, tensor
from torch.nn import Module, Linear, CrossEntropyLoss
from torch.optim import Optimizer, SGD
from torch.optim.lr_scheduler import _LRScheduler, StepLR
from typing import Dict, List, Optional, Tuple, Union, ClassVar
from torchvision.models import ResNet18_Weights
from torchvision.models.resnet import ResNet
from torchvision import transforms
from PIL import Image

from aiBoardGame.logic.engine import BoardEntity, Board, Position
from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XiangqiPieceDataset, XiangqiPieceDataLoader, XIANGQI_PIECE_CLASSES
from aiBoardGame.vision.xiangqiPieceClassifier.earlyStopping import EarlyStopping
from aiBoardGame.vision.boardImage import BoardImage


class XiangqiPieceClassifier:
    batchSize: ClassVar[int] = 32
    epochCount: ClassVar[int] = 150

    classes: ClassVar[List[Optional[BoardEntity]]] = XIANGQI_PIECE_CLASSES

    def __init__(self, weights: Optional[Union[Path, Dict[str, Tensor]]] = None, device: str = "cpu") -> None:
        self._model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', weights=ResNet18_Weights.DEFAULT if weights is None else None)
        self.model.fc = Linear(self.model.fc.in_features, len(self.classes))

        if weights is not None:
            self.loadWeights(weights)

        self.device = device

    @property
    def model(self) -> ResNet:
        return self._model

    @property
    def device(self) -> str:
        return self._device

    @device.setter
    def device(self, value: str) -> None:
        self._device = value
        self.model.to(self._device)

    def loadWeights(self, weights: Union[Path, Dict[str, Tensor]]) -> None:
        if isinstance(weights, Path):
            weights: Dict[str, Tensor] = torch.load(weights)
        self.model.load_state_dict(weights)

    def saveWeights(self, savePath: Path) -> None:
        torch.save(self.model.state_dict(), savePath.with_suffix(".pt"))

    def trainFromScratch(self, trainDataLoader: XiangqiPieceDataLoader, validationDataLoader: XiangqiPieceDataLoader) -> XiangqiPieceClassifier:       
        criterion = CrossEntropyLoss()


        # NOTE: Freezing pretrained model and only training last layer

        for param in self.model.parameters():
            param.requires_grad = False
        for param in self.model.fc.parameters():
            param.requires_grad = True

        optimizer = SGD(self.model.parameters(), lr=1e-2, momentum=0.9)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        self.train(trainDataLoader, validationDataLoader, criterion, optimizer, scheduler)


        # NOTE: Fine Tuning

        for param in self.model.parameters():
            param.requires_grad = True

        optimizer = SGD(self.model.parameters(), lr=1e-3, momentum=0.9)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        self.train(trainDataLoader, validationDataLoader, criterion, optimizer, scheduler)


        return self

    def train(
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

    def predict(self, input: Tensor) -> List[Optional[BoardEntity]]:
        if len(input.shape) == 3:
            input = input.unsqueeze(0)
        elif len(input.shape) > 4:
            input = input.reshape(-1, *input.shape[-3:])

        self.model.eval()
        input = input.to(self.device)
        output = self.model(input)
        _, predictions = torch.max(output, 1)

        boardEntities = []
        for prediction in predictions:
            boardEntities.append(self.classes[prediction])
        return boardEntities

    def predictTile(self, tile: np.ndarray) -> Optional[BoardEntity]:
        if not (len(tile.shape) == 3 and tile.shape[-1] == 3):
            raise ValueError(f"Invalid tile shape, must be (..., ..., 3)")

        return self.predict(self._cvImagesToTensor(tile[np.newaxis]))[0]

    def predictTiles(self, tiles: np.ndarray) -> Board:
        if not (tiles.shape[:2] == (Board.fileCount, Board.rankCount) and tiles.shape[-1] == 3):
            raise ValueError(f"Invalid tiles shape, must be ({Board.fileCount}, {Board.rankCount}, ..., ..., 3)")
    
        tilePredicts = self.predict(self._cvImagesToTensor(tiles))
        
        board = Board()
        for rank in range(Board.rankCount):
            for file in range(Board.fileCount):
                tilePredict = tilePredicts[file*Board.rankCount+rank]
                if tilePredict is not None:
                    side, piece = tilePredict
                board[side][file, rank] = piece

        return board

    def predictPieces(self, pieces: List[Tuple[Position, np.ndarray]]) -> Board:
        positions, tiles = zip(*pieces)

        tilePredicts = self.predict(self._cvImagesToTensor(tiles))
        
        board = Board()
        for position, tilePredict in zip(positions, tilePredicts):
            print(position, tilePredict)
            if tilePredict is not None:
                side, piece = tilePredict
                board[side][position] = piece

        return board

    def predictBoard(self, boardImage: BoardImage, allTiles: bool = False) -> Board:
        return self.predictTiles(boardImage.tiles) if allTiles else self.predictPieces(boardImage.pieces)

    @staticmethod
    def _cvImagesToTensor(cvImages: Tuple[np.ndarray]) -> Tensor:
        tensors = [XiangqiPieceDataset.basicTransform(Image.fromarray(cv.cvtColor(cvImage, cv.COLOR_BGR2RGB))) for cvImage in cvImages]
        return torch.stack(tensors)
    

if __name__ == "__main__":
    import cv2 as cv
    from torchvision import transforms
    from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XiangqiPieceDataset

    logging.basicConfig(level=logging.DEBUG)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using {device} device")

    xiangqiDatasetRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes")
    train, validation, test = XiangqiPieceDataset.split(root=xiangqiDatasetRoot, batchSize=XiangqiPieceClassifier.batchSize, numWorkers=4)


    loadModelWeights = input("Do you want to load model weights? (yes/other) ") == "yes"
    if loadModelWeights is True:
        loadPathStr = input("Load Path: ")
        loadPath = Path(loadPathStr)
        classifier = XiangqiPieceClassifier(weights=loadPath, device=device)
    else:
        classifier = XiangqiPieceClassifier(device=device)
        classifier.trainFromScratch(train, validation)

    logging.info("")

    classifier.test(test)

    logging.info("")

    pieceImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes/None/cut_15.jpg")
    pieceImage = cv.imread(pieceImagePath.as_posix())
    pieceImage = cv.cvtColor(pieceImage, cv.COLOR_BGR2RGB)

    transform = transforms.Compose([
        transforms.ToTensor()
    ])

    prediction = classifier.predict(transform(pieceImage))[0]
    logging.info(f"Label: {pieceImagePath.parent.name}, Prediction: {prediction}")

    saveModelWeights = input("Do you want to save model weights? (yes/other) ") == "yes"
    if saveModelWeights is True:
        savePathStr = input("Save Path: ")
        savePath = Path(savePathStr)
        classifier.saveWeights(savePath)
