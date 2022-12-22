"""Piece dataset used for training the recognition model"""

# pylint: disable=unnecessary-pass

from pathlib import Path
from itertools import chain
from math import floor, isclose
from collections import Counter
from typing import ClassVar, List, Optional, Tuple
import numpy as np
from torch import from_numpy  # pylint: disable=no-name-in-module
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler
from torchvision import transforms
from torchvision.datasets import ImageFolder

from aiBoardGame.logic.engine import Side, BoardEntity
from aiBoardGame.logic.engine.pieces import PIECE_SET


XIANGQI_PIECE_CLASSES = sorted(chain((BoardEntity(side, piece) for side in Side for piece in PIECE_SET), [None]), key=str)


class XiangqiPieceDataLoader(DataLoader):
    """Custom DataLoader for type checking"""
    pass


class XiangqiPieceDataset(ImageFolder):
    """Custom ImageFolder dataset for finding, transforming Xianqi piece images 
    and providing them to the convolutional neural network model"""
    basicTransform: ClassVar[transforms.Compose] = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    ])
    """Transforms used for normalizing input"""
    trainTransform: ClassVar[transforms.Compose] = transforms.Compose([
        basicTransform.transforms[0],
        transforms.RandomAffine(degrees=180, translate=(0.15, 0.15), scale=(0.8, 1.2)),
        transforms.ColorJitter(brightness=(0.9, 1.5), contrast=0.2, saturation=0.1, hue=0.04),
        transforms.RandomAdjustSharpness(sharpness_factor=1.5, p=0.3),
        transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 0.8)),
        *basicTransform.transforms[-2:]
    ])
    """Transforms used for broadening dataset"""
    splitSizeFractions: ClassVar[List[float]] = [0.8, 0.1, 0.1]
    """Ratios used for splitting the dataset to train, validation and test data"""

    def __init__(self, root: Path, transform: Optional[transforms.Compose] = None) -> None:
        """
        :param root: Root of the image folders
        :type root: Path
        :param transform: Transforms applied to images found under the root directory, defaults to None
        :type transform: Optional[transforms.Compose], optional
        :raises FileNotFoundError: Root does not contain all Xiangqi piece class folder
        """
        super().__init__(root.as_posix(), transform)

        if Counter(self.classes) != Counter(str(pieceClass) for pieceClass in XIANGQI_PIECE_CLASSES):
            raise FileNotFoundError(f"{root.as_posix()} does not contain all class folders")

    @staticmethod
    def _calculateSplits(datasetSize: int) -> List[int]:
        splitSizes = [floor(fraction * datasetSize) for fraction in XiangqiPieceDataset.splitSizeFractions]
        splitSizes[0] += datasetSize - sum(splitSizes)
        splits = [0]
        for splitSize in splitSizes:
            splits.append(splits[-1] + splitSize)
        return splits

    @staticmethod
    def _generateSubsets(root: Path) -> List[Subset]:
        basicDataset = XiangqiPieceDataset(root, XiangqiPieceDataset.basicTransform)
        augmentedDataset = XiangqiPieceDataset(root, XiangqiPieceDataset.trainTransform)

        datasetSize = len(basicDataset)

        splits = XiangqiPieceDataset._calculateSplits(datasetSize)
        indices = list(range(datasetSize))
        np.random.shuffle(indices)
        subsets = []
        for subsetBase, i in zip([augmentedDataset, basicDataset, basicDataset], range(1, len(splits))):
            start, end = splits[i-1], splits[i]
            subsets.append(Subset(subsetBase, indices[start:end]))

        return subsets

    @staticmethod
    def split(root: Path, batchSize: int, numWorkers: int) -> Tuple[XiangqiPieceDataLoader, XiangqiPieceDataLoader, XiangqiPieceDataLoader]:
        """Splits dataset into train, validation and test DataLoader

        :param root: Root of the image folders
        :type root: Path
        :param batchSize: Loaded image batch size
        :type batchSize: int
        :param numWorkers: Multi-process data loading, specifies number of loader worker processes
        :type numWorkers: int
        :return: Train, validation and test DataLoader
        :rtype: Tuple[XiangqiPieceDataLoader, XiangqiPieceDataLoader, XiangqiPieceDataLoader]
        """
        assert len(XiangqiPieceDataset.splitSizeFractions) == 3
        assert isclose(sum(XiangqiPieceDataset.splitSizeFractions), 1.0)

        subsets = XiangqiPieceDataset._generateSubsets(root)

        targets = np.array(subsets[0].dataset.targets)[subsets[0].indices]
        classSizes = sorted(Counter(targets).items())
        classWeights = [1./size for _, size in classSizes]

        samplesWeight = from_numpy(np.array([classWeights[target] for target in targets])).double()
        trainSampler = WeightedRandomSampler(samplesWeight, len(samplesWeight))

        dataLoaderArgs = zip(subsets, [trainSampler, None, None])
        dataLoaders = [XiangqiPieceDataLoader(
            subset, sampler=sampler,
            batch_size=batchSize, num_workers=numWorkers
        ) for subset, sampler in dataLoaderArgs]

        return dataLoaders


if __name__ == "__main__":
    import logging
    import cv2 as cv

    logging.basicConfig(level=logging.INFO)

    datasetPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs/classes")
    train, validation, test = XiangqiPieceDataset.split(root=datasetPath, batchSize=1, numWorkers=2)
    j = 0
    for inputs, labels in train:
        if j >= 50:
            break
        image = np.transpose(inputs[0].numpy(), (1, 2, 0))
        image = cv.cvtColor(image, cv.COLOR_RGB2BGR)
        cv.imshow("image", image)
        cv.waitKey(0)
        j += 1
    cv.destroyAllWindows()
