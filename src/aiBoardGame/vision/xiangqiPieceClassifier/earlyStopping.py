import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from torch import nn, save


class EarlyStopping:
    def __init__(self, patience: int, delta: float = 0):
        self.patience = patience
        self.counter = 0
        self.bestScore = None
        self.isEarlyStop = False
        self.validationMinLoss = np.Inf
        self.delta = delta

        self._tempDir = TemporaryDirectory()
        self.checkpointPath = Path(self._tempDir.name, "checkpoint.pt")

    def __del__(self) -> None:
        if self._tempDir is not None:
            self._tempDir.cleanup()

    def __call__(self, model: nn.Module, validationLoss: float):
        accuracy = -validationLoss

        if self.bestScore is None:
            self.bestScore = accuracy
            self.saveCheckpoint(model, validationLoss)
        elif accuracy < self.bestScore + self.delta:
            self.counter += 1
            logging.debug(f"EarlyStopping Counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.isEarlyStop = True
        else:
            self.bestScore = accuracy
            self.saveCheckpoint(model, validationLoss)
            self.counter = 0

    def saveCheckpoint(self, model: nn.Module, validationLoss: float):
        logging.debug("Validation loss decreased, saving model...")
        save(model.state_dict(), self.checkpointPath)
        self.validationMinLoss = validationLoss
