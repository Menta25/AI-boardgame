from aiBoardGame.logic.engine.pieces.piece import Piece
from aiBoardGame.logic.engine.pieces.general import General
from aiBoardGame.logic.engine.pieces.advisor import Advisor
from aiBoardGame.logic.engine.pieces.elephant import Elephant
from aiBoardGame.logic.engine.pieces.horse import Horse
from aiBoardGame.logic.engine.pieces.chariot import Chariot
from aiBoardGame.logic.engine.pieces.cannon import Cannon
from aiBoardGame.logic.engine.pieces.soldier import Soldier

from aiBoardGame.logic.engine.pieces.abbreviations import ABBREVIATION_TO_PIECE


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
    "ABBREVIATION_TO_PIECE"
]
