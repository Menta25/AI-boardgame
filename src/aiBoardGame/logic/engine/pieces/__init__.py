from aiBoardGame.logic.engine.pieces.piece import Piece
from aiBoardGame.logic.engine.pieces.general import General
from aiBoardGame.logic.engine.pieces.advisor import Advisor
from aiBoardGame.logic.engine.pieces.elephant import Elephant
from aiBoardGame.logic.engine.pieces.horse import Horse
from aiBoardGame.logic.engine.pieces.chariot import Chariot
from aiBoardGame.logic.engine.pieces.cannon import Cannon
from aiBoardGame.logic.engine.pieces.soldier import Soldier


PIECE_SET = [
    Advisor,
    Cannon,
    Chariot,
    Elephant,
    General,
    Horse,
    Soldier
]


BASE_ABBREVIATION_TO_PIECE = {piece.abbreviations["base"]: piece for piece in PIECE_SET}
FEN_ABBREVIATION_TO_PIECE = {piece.abbreviations["fen"]: piece for piece in PIECE_SET}

BASE_TO_FEN_ABBREVIATION = {piece.abbreviations["base"]: piece.abbreviations["fen"] for piece in PIECE_SET}
FEN_TO_BASE_ABBREVIATION = {piece.abbreviations["fen"]: piece.abbreviations["base"] for piece in PIECE_SET}


__all__ = [
    "Piece",
    "General",
    "Advisor",
    "Elephant",
    "Horse",
    "Chariot",
    "Cannon",
    "Soldier",
    "BASE_ABBREVIATION_TO_PIECE",
    "FEN_ABBREVIATION_TO_PIECE",
    "BASE_TO_FEN_ABBREVIATION", "FEN_TO_BASE_ABBREVIATION",
]
