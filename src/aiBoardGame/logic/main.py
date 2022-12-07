import logging
from typing import Tuple

from aiBoardGame.logic.engine import XiangqiEngine, Position, InvalidMove
from aiBoardGame.logic.engine.utility import boardToStr
from aiBoardGame.logic.stockfish import FairyStockfish


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
                        moveOnBoard(game, start, end)
                        return True, False
                logging.info("Invalid command")
        except InvalidMove as error:
            logging.info(error)
        except:
            pass


def robotTurn(game: XiangqiEngine, stockfish: FairyStockfish) -> None:
    fen =  game.FEN
    start, end = stockfish.nextMove(fen)
    moveOnBoard(game, start, end)


def moveOnBoard(game: XiangqiEngine, start: Position, end: Position) -> None:
    game.move(start, end)
    logging.info(boardToStr(game.board))
    logging.info(f"From {*start,} to {*end,}\n")


if __name__ == "__main__":
    from pathlib import Path

    logging.basicConfig(format="", level=logging.INFO)

    game = XiangqiEngine()
    stockfish = FairyStockfish(binaryPath=Path("/home/Menta/Workspace/Projects/AI-boardgame/src/aiBoardGame/logic/stockfish/fairy-stockfish-largeboard_x86-64"))
    play(game, stockfish)
    # from aiBoardGame.logic.engine.utility import createXiangqiBoard
    # from aiBoardGame.logic.engine.pieces import Chariot, Horse
    # from aiBoardGame.logic.engine import Side
    # nextBoard, _ = createXiangqiBoard()
    # nextBoard[1,0] = None
    # nextBoard[Side.Red][2,2] = Horse
    # game.update(nextBoard)
    # logging.info(boardToStr(game.board))
