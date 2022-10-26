import torch
from torch import nn
from typing import Any, ClassVar, Dict, List


class CnOCR(nn.Module):
    _defaultVGGConv2dArgs: ClassVar[Dict[str, Any]] = {
        "kernel_size": 3,
        "stride": 1,
        "padding": 1
    }
    _defaultVGGMaxPoolingArgs: ClassVar[Dict[str, Any]] = {
        "kernel_size": 2,
        "stride": 2
    }

    def __init__(self, classesCount: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            *CnOCR.createVGG8Part(3, 32),
            *CnOCR.createVGG8Part(32, 64, conv2dCount=2),
            *CnOCR.createVGG8Part(64, 128, conv2dCount=3)
        )
        self.averagePool = nn.AdaptiveAvgPool2d((16,16))
        self.classifier = nn.Sequential(
            nn.Linear(in_features=32768, out_features=1024, bias=True),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(in_features=1024, out_features=classesCount, bias=True)
        )
        self.apply(CnOCR._init_weights)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.averagePool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x
    
    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Conv2d):
            nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
        elif isinstance(module, nn.BatchNorm2d):
            nn.init.constant_(module.weight, 1)
            nn.init.constant_(module.bias, 0)
        elif isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, 0, 0.01)
            nn.init.constant_(module.bias, 0)

    @staticmethod
    def createVGG8Part(inChannels: int, outChannels: int, conv2dCount: int = 1) -> List[nn.Module]:
        sequentialArgs = []
        for inChannel in [inChannels] + [outChannels] * (conv2dCount-1):
            sequentialArgs.extend([
                nn.Conv2d(inChannel, outChannels, **CnOCR._defaultVGGConv2dArgs),
                nn.BatchNorm2d(outChannels),
                nn.ReLU(inplace=True)
            ])
        sequentialArgs[0].in_channels = inChannels
        sequentialArgs.append(nn.MaxPool2d(**CnOCR._defaultVGGMaxPoolingArgs))
        return sequentialArgs


if __name__ == "__main__":    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using {device} device")

    model = CnOCR(1000).to(device)
    x = torch.randn(1,3,128,128).to(device)
    y = model(x)
    print(y.shape)
        