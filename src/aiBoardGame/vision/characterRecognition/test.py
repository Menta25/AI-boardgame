import time
import torch
from copy import deepcopy
from torch.utils.data.dataloader import DataLoader
from torch import nn
from torch import optim

from aiBoardGame.vision.characterRecognition.casiaDataSet import CASIAHWDB
from aiBoardGame.vision.characterRecognition.cnOCR import CnOCR

if __name__ == "__main__":
    from pathlib import Path

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using {device} device")

    batchSize = 32
    epochCount = 75

    trainDatasetRoot = Path("/run/media/Menta/Western Digital/Documents/Programming/Xiangqi/archive/CASIA-HWDB_Train/Train")
    trainDataset = CASIAHWDB(root=trainDatasetRoot)
    trainLoader = DataLoader(trainDataset, batch_size=batchSize, shuffle=False, num_workers=2)

    model = CnOCR(classesCount=len(trainDataset.classes)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    expScheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)
    
    model.train()

    print("Started Training")
    since = time.time()
    for epoch in range(epochCount):
        print(f"Epoch {epoch+1}/{epochCount}")
        print("-"*10)
        runningLoss = 0.0
        runningCorrects = 0
        for data in trainLoader:
            inputs, labels = data[0].to(device), data[1].to(device)

            optimizer.zero_grad()

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            runningLoss += loss.item() * inputs.size(0)
            runningCorrects += torch.sum(preds == labels.data)
        expScheduler.step()
        epochLoss = runningLoss / len(trainDataset)
        epochAcc = runningCorrects.double() / len(trainDataset)
        print(f"Loss: {epochLoss:.4f} Acc: {epochAcc:.4f}\n")
    timeElapsed = time.time() - since
    print(f"Training complete in {timeElapsed // 60:.0f}m {timeElapsed % 60:.0f}s")

    saveModelPath = Path("./CnOCR.pth")
    torch.save(model.state_dict(), saveModelPath)

    model.eval()
    testDatasetRoot = Path("/run/media/Menta/Western Digital/Documents/Programming/Xiangqi/archive/CASIA-HWDB_Test/Test")
    testDataset = CASIAHWDB(root=testDatasetRoot)
    testLoader = DataLoader(testDataset, batch_size=batchSize, shuffle=False, num_workers=2)

    dataIter = iter(testLoader)
    data = next(dataIter)
    inputs, labels = data[0].to(device), data[1].to(device)

    print("GroundTruth: ", " ".join(f"{model.classes[labels[j]]:5s}" for j in range(4)))

    outputs = model(inputs)

    _, predicted = torch.max(outputs, 1)
    print("Predicted: ", " ".join(f"{model.classes[predicted[j]]:5s}" for j in range(4)))

    correct = 0
    total = 0
    with torch.no_grad():
        for data in testLoader:
            inputs, labels = data[0].to(device), data[1].to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f"Accuracy of the network on the 10000 test images: {100 * correct // total} %")

    correctPred = {classname: 0 for classname in model.classes}
    totalPred = {classname: 0 for classname in model.classes}

    with torch.no_grad():
        for data in testLoader:
            inputs, labels = data[0].to(device), data[1].to(device)
            outputs = model(inputs)
            _, predictions = torch.max(outputs, 1)
            for label, prediction in zip(labels, predictions):
                if label == prediction:
                    correctPred[model.classes[label]] += 1
                totalPred[model.classes[label]] += 1


    for classname, correct_count in correctPred.items():
        accuracy = 100 * float(correct_count) / totalPred[classname]
        print(f"Accuracy for class: {classname:5s} is {accuracy:.1f} %")

    del dataIter
