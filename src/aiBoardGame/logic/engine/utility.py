import re
from math import floor
from collections import defaultdict
from typing import Dict, Literal, Optional, Tuple, Union, overload, Iterable, List, TypeVar, Callable

from aiBoardGame.logic.engine.auxiliary import Board, Delta, Position, Side
from aiBoardGame.logic.engine.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier, BASE_ABBREVIATION_TO_PIECE, FEN_ABBREVIATION_TO_PIECE


SOLDIER_RANK_OFFSET = 3
CANNON_RANK_OFFSET = 2

_STR_BOARD = """\
9 ┏━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┓
  ┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃
8 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃
7 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
6 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
5 ┣━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┫
  ┃                               ┃
4 ┣━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┫
  ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
3 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃   ┃
2 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃ \ ┃ / ┃   ┃   ┃   ┃
1 ┣━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━╋━━━┫
  ┃   ┃   ┃   ┃ / ┃ \ ┃   ┃   ┃   ┃
0 ┗━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┻━━━┛
  0   1   2   3   4   5   6   7   8\
"""


class FontFormat:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKCYAN = "\033[96m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        ENDC = "\033[0m"


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


@overload
def prettyBoard(board: Union[Board, str], colors: Literal[False], lastMove: Literal[None]) -> str:
    ...

@overload
def prettyBoard(board: Union[Board, str], colors: Literal[True], lastMove: Optional[Tuple[Position, Position]]) -> str:
    ...

def prettyBoard(board: Union[Board, str], colors: bool = False, lastMove: Optional[Tuple[Position, Position]] = None) -> str:
    if isinstance(board, Board):
        pieces = board.pieces
        if len(pieces) > 0:
            pieces = sorted(board.pieces, key=lambda item: item[0][0], reverse=True)
            pieces = sorted(pieces, key=lambda item: item[0][1])
            positions, pieces = zip(*pieces)
        else:
            positions = pieces = []
        getSide = lambda boardEntity: boardEntity.side
        getChar = lambda boardEntity: boardEntity.piece.abbreviations["fen"]
    elif isinstance(board, str):
        fenParts = board.split(" ")
        if len(fenParts) not in [1, 6]:
            raise ValueError("Invalid FEN")

        boardFenParts = fenParts[0].split("/")
        if len(boardFenParts) != 10:
            raise ValueError("Invalid FEN")

        positions = []
        pieces = []
        for rank, rankFen in enumerate(boardFenParts[::-1]):
            file = Board.fileCount - 1
            for char in rankFen[::-1]:
                if char.isdigit():
                    file -= int(char)
                else:
                    positions.append(Position(file, rank))
                    pieces.append(char)
                    file -= 1

        getSide = lambda char: Side.Red if char.isupper() else Side.Black
        getChar = lambda char: char
    else:
        raise TypeError(f"Invalid board type, must be Board or string, was {type(board)}")

    return _prettyBoard(positions, pieces, getSide, getChar, colors, lastMove)


T = TypeVar("T")


def _prettyBoard(positions: List[Position], pieces: Iterable[T], getSide: Callable[[T], Side], getChar: Callable[[T], str], colors: bool, lastMove: Optional[Tuple[Position, Position]]) -> str:
    if lastMove is not None:
        lastMoveStartIndex = (Board.rankCount - lastMove[0].rank - 1) * Board.fileCount * 8 + 2 + lastMove[0].file * 4
        boardStr = _STR_BOARD[:lastMoveStartIndex] + FontFormat.OKGREEN + _STR_BOARD[lastMoveStartIndex] + FontFormat.ENDC + _STR_BOARD[lastMoveStartIndex + 1:]
    else:
        boardStr = _STR_BOARD
    for position, piece in zip(positions, pieces):
        side = getSide(piece)
        convert = str.upper if side == Side.Red else str.lower
        char = convert(getChar(piece))
        if colors is True:
            if lastMove is not None and position == lastMove[1]:
                colorStart = FontFormat.OKGREEN
            else:
                colorStart = FontFormat.FAIL if side == Side.Red else FontFormat.OKBLUE
            colorStart += FontFormat.BOLD
            colorEnd = FontFormat.ENDC
        else:
            colorStart = colorEnd = ""
        index = (Board.rankCount - position.rank - 1) * Board.fileCount * 8 + 2 + position.file * 4
        if lastMove is not None and (lastMove[0].rank > position.rank or lastMove[0].rank == position.rank and lastMove[0].file < position.file):
            index += len(FontFormat.OKGREEN) + len(FontFormat.ENDC)
        boardStr = boardStr[:index] + f"{colorStart}{char}{colorEnd}" + boardStr[index + 1:]
    return boardStr


if __name__ == "__main__":
    fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"

    print(prettyBoard(fen, colors=True, lastMove=(Position(4,1),Position(4,3))))
