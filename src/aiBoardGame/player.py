from dataclasses import dataclass
from abc import ABC, abstractmethod

from aiBoardGame.logic import XiangqiEngine, FairyStockfish
from aiBoardGame.robot import RobotArm, RobotArmException

from aiBoardGame.utility import retry, rerunAfterCorrection


@dataclass(frozen=True)
class Player(ABC):
    @abstractmethod
    def makeMove(self, engine: XiangqiEngine) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented getPossibleMoves method")


@dataclass(frozen=True)
class HumanPlayer(Player):
    def makeMove(self, _: XiangqiEngine) -> None:
        input("Press any key if you want to finish the turn...")


@dataclass(frozen=True)
class RobotPlayer(Player):
    arm: RobotArm
    stockfish: FairyStockfish

    @retry(times=1, exceptions=(RobotArmException), callback=rerunAfterCorrection)
    def makeMove(self, engine: XiangqiEngine) -> None:
        robotMove = self.stockfish.nextMove(fen=engine.FEN)
        # TODO: Implement robot movement
        self.arm.resetPosition()
