from aiBoardGame.logic.engine.xiangqiEngine import XiangqiEngine
from aiBoardGame.logic.stockfish.fairyStockfish import FairyStockfish


class TestStockfish:
    stockfish = FairyStockfish()

    def testMove(self) -> None:
        game = XiangqiEngine()
        start, end = self.stockfish.nextMove(game.fen)
        game.move(start, end)

    def testPlay(self) -> None:
        game = XiangqiEngine()
        for _ in range(5):
            start, end = self.stockfish.nextMove(game.fen)
            game.move(start, end)
