import logging
from pathlib import Path
from typing import Tuple

from aiBoardGame.logic.engine import XiangqiEngine, XiangqiError, Position, InvalidMove
from aiBoardGame.logic.stockfish import FairyStockfish


def main() -> None:
    game = XiangqiEngine()
    stockfish = FairyStockfish(binaryPath=Path("/home/Menta/Workspace/Projects/AI-boardgame/src/aiBoardGame/logic/stockfish/fairy-stockfish-largeboard_x86-64"))
    play(game, stockfish)


def play(game: XiangqiEngine, stockfish: FairyStockfish) -> None:
    while True:
        logging.info("Player's turn:")
        continuePlay, wasUndo = playerTurn(game)
        if continuePlay is False:
            break
        if wasUndo is False:
            logging.info("Robot's turn:")
            robotTurn(game, stockfish)


def playerTurn(game: XiangqiEngine) -> Tuple[bool, bool]:
    while True:
        command = input("Command: ")
        try:
            if command == "undo":
                game.undoMove()
                game.undoMove()
                logging.info("Undo turn")
                return True, True
            elif command == "end":
                logging.info("Ending game")
                return False, False
            else:
                commandParts = command.split(" ")
                if len(commandParts) == 2:
                    startPositionStrs = commandParts[0].split(",")
                    endPositionStrs = commandParts[1].split(",")
                    if len(startPositionStrs) == 2 and len(endPositionStrs) == 2:
                        start = Position(int(startPositionStrs[0]), int(startPositionStrs[1]))
                        end = Position(int(endPositionStrs[0]), int(endPositionStrs[1]))
                        game.move(start, end)
                        logging.info(f"From {*start,} to {*end,}\n")
                        return True, False
                logging.info("Invalid command")
        except (XiangqiError, InvalidMove) as error:
            logging.info(error)
        except:
            pass


def robotTurn(game: XiangqiEngine, stockfish: FairyStockfish) -> None:
    fen =  game.FEN
    start, end = stockfish.nextMove(fen)
    game.move(start, end)
    logging.info(f"From {*start,} to {*end,}\n")


if __name__ == "__main__":
    logging.basicConfig(format="", level=logging.INFO)

    main()