from aiBoardGame.logic.engine.pieces.chariot import Chariot
from aiBoardGame.logic.engine.pieces.horse import Horse
from aiBoardGame.logic.engine.pieces.elephant import Elephant
from aiBoardGame.logic.engine.pieces.advisor import Advisor
from aiBoardGame.logic.engine.pieces.general import General
from aiBoardGame.logic.engine.pieces.cannon import Cannon
from aiBoardGame.logic.engine.pieces.soldier import Soldier


ABBREVIATION_TO_PIECE = {
    "R": Chariot,
    "N": Horse,
    "B": Elephant,
    "A": Advisor,
    "K": General,
    "C": Cannon,
    "P": Soldier
}
