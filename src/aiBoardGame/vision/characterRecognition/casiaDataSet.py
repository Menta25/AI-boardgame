from pathlib import Path
from typing import Union
from PIL.Image import Image
from torch import Tensor
from torchvision import transforms
from torchvision.transforms import functional
from torchvision.datasets import ImageFolder


class SquarePad:
    def __call__(self, image: Union[Image, Tensor]) -> Union[Image, Tensor]:
        maxWidthHeight = max(image.size)
        leftPadding, topPadding = [(maxWidthHeight - size) // 2 for size in image.size]
        rightPadding, bottomPadding = [maxWidthHeight - (size+padding) for size, padding in zip(image.size, [leftPadding, topPadding])]
        padding = (leftPadding, topPadding, rightPadding, bottomPadding)
        return functional.pad(image, padding, 255, "constant")


class CASIAHWDB(ImageFolder):
    def __init__(self, root: Path) -> None:
        transform = transforms.Compose([
            SquarePad(),
            transforms.Resize(128),
            transforms.ToTensor()
        ])
        super().__init__(root.as_posix(), transform)
        

if __name__ == "__main__":
    import cv2 as cv

    datasetPath = Path("/run/media/Menta/Western Digital/Documents/Programming/Xiangqi/archive/CASIA-HWDB_Train/Train")
    dataset = CASIAHWDB(root=datasetPath)
    print(len(dataset))
    img, label = dataset[0]
    print(label)
    img = img.permute(1, 2, 0).numpy()
    print(img.shape)
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    cv.imshow("eg", img)
    cv.waitKey(0)
    cv.destroyAllWindows()