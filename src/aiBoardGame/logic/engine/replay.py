"""Replay a game from stored matches"""

import logging
from pathlib import Path
from time import sleep
from typing import Optional

from aiBoardGame.logic.engine.move import InvalidMove
from aiBoardGame.logic.engine.utility import baseNotationToMove
from aiBoardGame.logic.engine.xiangqiEngine import XiangqiEngine


def replayGame(gameRecordPath: Path, intermission: Optional[int] = None) -> None:
    """Replay a Xiangqi game

    :param gameRecordPath: File with moves made during the game
    :type gameRecordPath: Path
    :param intermission: Time between moves, defaults to None
    :type intermission: Optional[int], optional
    :raises InvalidMove: Could not convert notation to move
    """
    game = XiangqiEngine()
    with gameRecordPath.open(mode="r") as gameRecordFile:
        for turn, notation in enumerate(gameRecordFile):
            logging.info("\nTurn {turn} - {side}", turn=turn+1, side=game.currentSide)
            start, end = baseNotationToMove(game.board, game.currentSide, notation.rstrip("\n"))
            if start is None or end is None:
                raise InvalidMove(None, None, None, "Could not convert notation to move")
            game.move(start, end)
            if intermission is not None:
                sleep(intermission)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")
    try:
        gameRecord = Path(input("Gamerecord path: "))
        replayGame(gameRecord, 0)
    except InvalidMove as error:
        logging.info(error)
    except Exception:
        logging.exception("An error occurred during game replay")
