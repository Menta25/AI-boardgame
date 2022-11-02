import numpy as np
from math import floor
from pathlib import Path
from collections import Counter
from torchvision import transforms
from torchvision.datasets import ImageFolder
from typing import ClassVar, List, Optional, Tuple
from torch.utils.data import DataLoader, SubsetRandomSampler

from aiBoardGame.logic.pieces import PIECE_SET
from aiBoardGame.logic.auxiliary import Side, BoardEntity


XIANGQI_PIECE_CLASSES = [BoardEntity(side, piece) for side in Side for piece in PIECE_SET]


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
    def split(root: Path, batchSize: int, numWorkers: int) -> Tuple[XiangqiPieceDataLoader, XiangqiPieceDataLoader, XiangqiPieceDataLoader]:
        assert len(XiangqiPieceDataset.splitSizeFractions) == 3
        assert sum(XiangqiPieceDataset.splitSizeFractions) == 1.0

        trainDataset = XiangqiPieceDataset(root, XiangqiPieceDataset.trainTransform)
        testAndValidationDataset = XiangqiPieceDataset(root, transforms.Compose([transforms.ToTensor()]))

        datasetSize = len(trainDataset)

        splitSizes = [floor(fraction * datasetSize) for fraction in XiangqiPieceDataset.splitSizeFractions]
        splitSizes[0] += datasetSize - sum(splitSizes)
        splits = [0]
        for splitSize in splitSizes:
            splits.append(splits[-1] + splitSize)

        indices = list(range(datasetSize))
        np.random.shuffle(indices)
        samplers = []
        for i in range(1, len(splits)):
            start, end = splits[i-1], splits[i]
            samplers.append(SubsetRandomSampler(indices[start:end]))

        dataLoaderArgs = zip([trainDataset, testAndValidationDataset, testAndValidationDataset], samplers)
        dataLoaders = [XiangqiPieceDataLoader(
            dataset, sampler=sampler,
            batch_size=batchSize, num_workers=numWorkers
        ) for dataset, sampler in dataLoaderArgs]

        train, validation, test = dataLoaders

        return train, validation, test


if __name__ == "__main__":
    import logging
    import cv2 as cv

    logging.basicConfig(level=logging.INFO)

    datasetPath = Path("/home/Menta/Workspace/Projects/XiangqiPieceImgs/imgs")
    dataset = XiangqiPieceDataset(root=datasetPath, transform=XiangqiPieceDataset.trainTransform)
    logging.info(len(dataset))
    img, label = dataset[3]
    logging.info(label)
    logging.info(dataset.classes)
    img = img.permute(1, 2, 0).numpy()
    logging.info(img.shape)
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    cv.imshow("eg", img)
    cv.waitKey(0)
    cv.destroyAllWindows()