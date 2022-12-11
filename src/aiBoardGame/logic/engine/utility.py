import re
from enum import Enum
from math import floor
from collections import defaultdict
from typing import Dict, Literal, Tuple, Union

from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side
from aiBoardGame.logic.engine.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier, BASE_ABBREVIATION_TO_PIECE, FEN_ABBREVIATION_TO_PIECE


SOLDIER_RANK_OFFSET = 3
CANNON_RANK_OFFSET = 2

STR_BOARD = """\
┏━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┓
┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
┣━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┫
┃                               ┃
┣━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┫
┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃
┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃
┗━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┛\
"""

class FontFormat(Enum):
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

def createXiangqiBoard() -> Tuple[Board, Dict[Side, Tuple[int, int]]]:
    board = Board()

    uniquePieces = [Chariot, Horse, Elephant, Advisor, General]
    for rank, side in [(Board.rankBounds[0], Side.Red), (Board.rankBounds[1]-1, Side.Black)]:
        for file, piece in enumerate(uniquePieces + uniquePieces[-2::-1]):
            board[side][file, rank] = piece

    for rank, side in [(Board.rankBounds[0]+SOLDIER_RANK_OFFSET, Side.Red), (Board.rankBounds[1]-SOLDIER_RANK_OFFSET-1, Side.Black)]:
        for file in range(Board.fileBounds[0], Board.fileBounds[1], 2):
            board[side][file, rank] = Soldier

    for rank, side in [(Board.rankBounds[0]+CANNON_RANK_OFFSET, Side.Red), (Board.rankBounds[1]-CANNON_RANK_OFFSET-1, Side.Black)]:
        for file in [Board.fileBounds[0]+1, Board.fileBounds[1]-2]:
            board[side][file, rank] = Cannon

    generals = {
        Side.Red: Position(Board.fileCount // 2, Board.rankBounds[0]),
        Side.Black: Position(Board.fileCount // 2, Board.rankBounds[1] - 1)
    }

    return board, generals

_OPERATOR_MAP = {
    "+": lambda x: x,
    "-": lambda x: -x
}

def baseNotationToMove(board: Board, side: Side, notation: str) -> Union[Tuple[Position, Position], Tuple[Literal[None], Literal[None]]]:
    try:
        notationRegEx = re.match(r"(?P<tandem>[+-])?(?P<piece>\w)(?P<formerFile>\d)?(?P<direction>[+-=.,])(?P<newFileOrDeltaRank>\d)", notation)
        if notationRegEx is None:
            return None
        if notationRegEx["piece"] is not None and notationRegEx["piece"].upper() not in BASE_ABBREVIATION_TO_PIECE and not ((side == Side.Red and notationRegEx["piece"].isupper()) or (side == Side.Black and notationRegEx["piece"].islower())):
            return None
        
        start, end = None, None
        if notationRegEx["piece"] is not None:
            notatedPiece = BASE_ABBREVIATION_TO_PIECE[notationRegEx["piece"].upper()]

            groupByFile = defaultdict(list)
            for position, piece in board[side].items():
                if piece == notatedPiece:
                    groupByFile[position.file].append(position.rank)

            if notationRegEx["formerFile"] is not None:
                formerFile = int(notationRegEx["formerFile"]) - 1 if side == Side.Black else Board.fileCount - int(notationRegEx["formerFile"])
                start = Position(formerFile, groupByFile[formerFile][floor(len(groupByFile[formerFile])/2)])
            else:
                for file, ranks in groupByFile.items():
                    ranks.sort(reverse=(side == Side.Black))
                    if len(ranks) >= 2:
                        startRank = ranks[0] if notationRegEx["tandem"] == "-" else ranks[-1]
                        start = Position(file, startRank)
                        break

            if notationRegEx["direction"] in ["=", ".", ","]:
                newFile = int(notationRegEx["newFileOrDeltaRank"]) - 1 if side == Side.Black else Board.fileCount - int(notationRegEx["newFileOrDeltaRank"])
                end = Position(newFile, start.rank)
            else:
                if notatedPiece in [Soldier, Chariot, Cannon, General]:
                    ranksTraversed = int(notationRegEx["newFileOrDeltaRank"])
                    end = start + Delta(0, _OPERATOR_MAP[notationRegEx["direction"]](ranksTraversed) * side)
                else:
                    newFile = int(notationRegEx["newFileOrDeltaRank"]) - 1 if side == Side.Black else Board.fileCount - int(notationRegEx["newFileOrDeltaRank"])
                    if notatedPiece == Advisor:
                        rankDelta = 1
                    elif notatedPiece == Elephant:
                        rankDelta = 2
                    else:
                        rankDelta = 1 if abs(start.file - newFile) == 2 else 2
                    end = Position(newFile, start.rank + _OPERATOR_MAP[notationRegEx["direction"]](rankDelta) * side)          
                
        return start, end
    except:
        return None, None


def fenToBoard(fen: str) -> Board:
    fenParts = fen.split(" ")

    if len(fenParts) != 6:
        raise ValueError

    boardFenParts = fenParts[0].split("/")

    if len(boardFenParts) != 10:
        raise ValueError

    board = Board()
    for rank, rankFEN in enumerate(boardFenParts):
        file = 0
        for char in rankFEN:
            if char.isdigit():
                file += int(char)
            else:
                side = Side.Red if char.isupper() else Side.Black
                board[side][file, Board.rankCount - rank - 1] = FEN_ABBREVIATION_TO_PIECE[char.upper()]
                file += 1
    return board


def boardToStr(board: Board) -> str:
    boardStr = ""
    for rank in range(board.rankCount - 1, -1, -1):
        for file in range(board.fileCount):
            if file == board.fileBounds[0]:
                if rank == board.rankBounds[0]:
                    char = " ┗"
                elif rank == board.rankBounds[1] - 1:
                    char = " ┏"
                else:
                    char = " ┣"
            elif file == board.fileBounds[1] - 1:
                if rank == board.rankBounds[0]:
                    char = "━┛"
                elif rank == board.rankBounds[1] - 1:
                    char = "━┓"
                else:
                    char = "━┫"
            else:
                if rank in [board.rankBounds[0], board.rankCount//2]:
                    char = "━┻"
                elif rank in [board.rankBounds[1] - 1, board.rankCount//2-1]:
                    char = "━┳"
                else:
                    char = "━╋"

            boardStr += f"{str(board[file, rank].side.name)[0].lower()}{board[file, rank].piece.abbreviations['base']}" if board[file, rank] != None else char
            boardStr += "━━"
        boardStr = boardStr[:-2]

        if rank == board.rankCount//2:
            boardStr += "\n ┃                               ┃\n"
        elif rank == board.rankBounds[1] - 1 or rank == board.rankBounds[0] + 2:
            boardStr += "\n ┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃\n"
        elif rank == board.rankBounds[1] - 2 or rank == board.rankBounds[0] + 1:
            boardStr += "\n ┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃\n"
        else:
            boardStr += "\n ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃\n"
    boardStr = boardStr[:-36]
    return boardStr


def boardToStr2(board: Board) -> str:
    for postion, (side, piece) in board.pieces:



if __name__ == "__main__":
    fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    print(boardToStr(fenToBoard(fen)))

    print(f"start {bcolors.BOLD} warning color {bcolors.ENDC} end")

    print(STR_BOARD)