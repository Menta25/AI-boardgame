import logging
from pathlib import Path
from time import sleep
from typing import Optional

from aiBoardGame.logic.engine.move import InvalidMove
from aiBoardGame.logic.engine.utility import baseNotationToMove
from aiBoardGame.logic.engine.xiangqiEngine import XiangqiEngine, XiangqiError

def replayGame(gameRecord: Path, intermission: Optional[int] = None) -> None:
    game = XiangqiEngine()
    with gameRecord.open(mode="r") as gameRecordFile:
        for turn, notation in enumerate(gameRecordFile):
            logging.info(f"\nTurn {turn+1} - {game.currentSide}")
            start, end = baseNotationToMove(game.board, game.currentSide, notation.rstrip("\n"))
            if start is None or end is None:
                raise XiangqiError("Could not convert notation to move")
            game.move(start, end)
            if intermission is not None:
                sleep(intermission)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")
    try:
        gameRecord = Path(input("Gamerecord path: "))
        replayGame(gameRecord, 0)
    except (InvalidMove, XiangqiError) as error:
        logging.info(error)
    except:
        logging.exception("An error occurred during game replay")