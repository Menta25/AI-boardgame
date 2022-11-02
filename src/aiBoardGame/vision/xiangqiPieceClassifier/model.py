from __future__ import annotations

import time
import logging
import torch
from pathlib import Path
from torch import Tensor
from torch.nn import Module, Linear, CrossEntropyLoss
from torch.optim import Optimizer, SGD
from torch.optim.lr_scheduler import _LRScheduler, StepLR
from typing import Dict, List, Optional, Union, ClassVar
from torchvision.models import ResNet18_Weights
from torchvision.models.resnet import ResNet

from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XiangqiPieceDataLoader, XIANGQI_PIECE_CLASSES
from aiBoardGame.vision.xiangqiPieceClassifier.earlyStopping import EarlyStopping
from aiBoardGame.logic.auxiliary import BoardEntity

class XiangqiPieceClassifier:
    batchSize: ClassVar[int] = 32
    epochCount: ClassVar[int] = 150

    classes: ClassVar[List[BoardEntity]] = XIANGQI_PIECE_CLASSES

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
        torch.save(self.model.state_dict(), savePath)

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
                
                epochLoss = runningLoss / len(dataLoader.sampler.indices)
                epochAccuracy = runningCorrects.double() / len(dataLoader.sampler.indices)

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

    def predict(self, image: Tensor) -> BoardEntity:
        self.model.eval()
        image = image.to(self.device)
        output = self.model(image.unsqueeze(0))
        _, prediction = torch.max(output, 1)
        return self.classes[prediction]


if __name__ == "__main__":
    import cv2 as cv
    from torchvision import transforms
    from aiBoardGame.vision.xiangqiPieceClassifier.dataset import XiangqiPieceDataset

    logging.basicConfig(level=logging.DEBUG)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using {device} device")

    xiangqiDatasetRoot = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs")
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

    pieceImagePath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/BlackElephant/cut_25.jpg")
    pieceImage = cv.imread(pieceImagePath.as_posix())
    pieceImage = cv.cvtColor(pieceImage, cv.COLOR_BGR2RGB)

    transform = transforms.Compose([
        transforms.ToTensor()
    ])

    prediction = classifier.predict(transform(pieceImage))
    logging.info(f"Label: {pieceImagePath.parent.name}, Prediction: {prediction}")

    saveModelWeights = input("Do you want to save model weights? (yes/other) ") == "yes"
    if saveModelWeights is True:
        savePathStr = input("Save Path: ")
        savePath = Path(savePathStr)
        classifier.saveWeights(savePath)