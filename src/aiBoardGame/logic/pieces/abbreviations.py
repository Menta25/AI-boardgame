from aiBoardGame.logic.pieces.chariot import Chariot
from aiBoardGame.logic.pieces.horse import Horse
from aiBoardGame.logic.pieces.elephant import Elephant
from aiBoardGame.logic.pieces.advisor import Advisor
from aiBoardGame.logic.pieces.general import General
from aiBoardGame.logic.pieces.cannon import Cannon
from aiBoardGame.logic.pieces.soldier import Soldier


ABBREVIATION_TO_PIECE = {
    "R": Chariot,
    "N": Horse,
    "B": Elephant,
    "A": Advisor,
    "K": General,
    "C": Cannon,
    "P": Soldier
}
