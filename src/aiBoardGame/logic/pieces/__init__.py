from aiBoardGame.logic.pieces.piece import Piece
from aiBoardGame.logic.pieces.general import General
from aiBoardGame.logic.pieces.advisor import Advisor
from aiBoardGame.logic.pieces.elephant import Elephant
from aiBoardGame.logic.pieces.horse import Horse
from aiBoardGame.logic.pieces.chariot import Chariot
from aiBoardGame.logic.pieces.cannon import Cannon
from aiBoardGame.logic.pieces.soldier import Soldier

from aiBoardGame.logic.pieces.abbreviations import ABBREVIATION_TO_PIECE


PIECE_SET = [
    Advisor,
    Cannon,
    Chariot,
    Elephant,
    General,
    Horse,
    Soldier
]


__all__ = [
    "Piece",
    "General",
    "Advisor",
    "Elephant",
    "Horse",
    "Chariot",
    "Cannon",
    "Soldier",
    "ABBREVIATION_TO_PIECE",
]
