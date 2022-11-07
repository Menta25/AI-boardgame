import numpy as np
from pathlib import Path
from torch import from_numpy
from itertools import chain
from math import floor, isclose
from collections import Counter
from torchvision import transforms
from torchvision.datasets import ImageFolder
from typing import ClassVar, List, Optional, Tuple
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler

from aiBoardGame.logic.pieces import PIECE_SET
from aiBoardGame.logic.auxiliary import Side, BoardEntity


XIANGQI_PIECE_CLASSES = sorted(chain((BoardEntity(side, piece) for side in Side for piece in PIECE_SET), [None]), key=str)


class XiangqiPieceDataLoader(DataLoader):
    pass


class XiangqiPieceDataset(ImageFolder):
    trainTransform: ClassVar[transforms.Compose] = transforms.Compose([
        transforms.RandomAffine(degrees=180, translate=(0.15, 0.15), scale=(0.8, 1.2)),
        transforms.ColorJitter(brightness=(0.9, 1.5), contrast=0.2, saturation=0.1, hue=0.04),
        transforms.RandomAdjustSharpness(sharpness_factor=1.5, p=0.3),
        transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 0.8)),
        transforms.ToTensor()
    ])
    splitSizeFractions: ClassVar[List[float]] = [0.8, 0.1, 0.1]

    def __init__(self, root: Path, transform: Optional[transforms.Compose] = None) -> None:
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
        basicDataset = XiangqiPieceDataset(root, transforms.Compose([transforms.ToTensor()]))
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

    datasetPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs")
    train, validation, test = XiangqiPieceDataset.split(root=datasetPath, batchSize=1, numWorkers=2)
    i = 0
    for inputs, labels in train:
        if i >= 50:
            break
        image = np.transpose(inputs[0].numpy(), (1, 2, 0))
        image = cv.cvtColor(image, cv.COLOR_RGB2BGR)
        cv.imshow("image", image)
        cv.waitKey(0)
        i += 1
    cv.destroyAllWindows()
