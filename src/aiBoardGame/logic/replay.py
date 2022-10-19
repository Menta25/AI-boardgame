import logging
from pathlib import Path
from time import sleep
from typing import Optional
from aiBoardGame.logic.move import InvalidMove
from aiBoardGame.logic.xiangqiEngine import XiangqiEngine, XiangqiError

def replayGame(gameRecord: Path, intermission: Optional[int] = None) -> None:
    game = XiangqiEngine()
    with gameRecord.open(mode="r") as gameRecordFile:
        for turn, notation in enumerate(gameRecordFile):
            logging.info(f"\nTurn {turn+1} - {game.currentSide}")
            game.moveFromNotation(notation.rstrip("\n"))
            if intermission is not None:
                sleep(intermission)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")
    try:
        gameRecord = Path(input("Gamerecord path: "))
        replayGame(gameRecord, 1)
    except (InvalidMove, XiangqiError) as error:
        logging.info(error)
    except:
        logging.exception("An error occurred during game replay")