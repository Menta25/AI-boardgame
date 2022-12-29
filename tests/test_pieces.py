from typing import List

from aiBoardGame.logic.engine.auxiliary import Board, Side, Position
from aiBoardGame.logic.engine.pieces import General, Advisor, Elephant, Horse, Chariot, Cannon, Soldier


def sortMoves(moveList: List[Position]) -> List[Position]:
    sortedMoves = sorted(moveList, key=lambda position: position[0])
    return sorted(sortedMoves, key=lambda position: position[1])


class TestGeneral:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,1] = General
        assert sortMoves(General.getPossibleMoves(board, Position(4,1))) == sortMoves([
            Position(file=3, rank=1),
            Position(file=4, rank=2),
            Position(file=5, rank=1),
            Position(file=4, rank=0)
        ])

    def testBounds(self) -> None:
        board = Board()
        board[Side.RED][4,2] = General
        assert Position(4,3) not in General.getPossibleMoves(board, Position(4,2))

    def testFlyingGeneral(self) -> None:
        board = Board()
        board[Side.RED][4,0] = General
        board[Side.BLACK][4,9] = General
        assert Position(4,9) in General.getPossibleMoves(board, Position(4,0))
        assert Position(4,0) in General.getPossibleMoves(board, Position(4,9))

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,0] = General
        board[Side.BLACK][4,1] = Soldier
        assert Position(4,1) in General.getPossibleMoves(board, Position(4,0))


class TestAdvisor:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,1] = Advisor
        assert sortMoves(Advisor.getPossibleMoves(board, Position(4,1))) == sortMoves([
            Position(file=3, rank=0),
            Position(file=3, rank=2),
            Position(file=5, rank=2),
            Position(file=5, rank=0)
        ])

    def testBounds(self) -> None:
        board = Board()
        board[Side.RED][5,2] = Advisor
        possibleMoves = Advisor.getPossibleMoves(board, Position(5,2))
        assert Position(4,3) not in possibleMoves
        assert Position(6,3) not in possibleMoves
        assert Position(6,1) not in possibleMoves

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,1] = Advisor
        board[Side.BLACK][3,2] = Soldier
        assert Position(3,2) in Advisor.getPossibleMoves(board, Position(4,1))


class TestElephant:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Elephant
        assert sortMoves(Elephant.getPossibleMoves(board, Position(4,2))) == sortMoves([
            Position(file=2, rank=0),
            Position(file=2, rank=4),
            Position(file=6, rank=4),
            Position(file=6, rank=0)
        ])

    def testRedBounds(self) -> None:
        board = Board()
        board[Side.RED][2,4] = Elephant
        possibleMoves = Elephant.getPossibleMoves(board, Position(2,4))
        assert Position(0,6) not in possibleMoves
        assert Position(4,6) not in possibleMoves

    def testBlackBounds(self) -> None:
        board = Board()
        board[Side.BLACK][2,5] = Elephant
        possibleMoves = Elephant.getPossibleMoves(board, Position(2,5))
        assert Position(0,3) not in possibleMoves
        assert Position(4,3) not in possibleMoves

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Elephant
        board[Side.BLACK][2,4] = Soldier
        assert Position(2,4) in Elephant.getPossibleMoves(board, Position(4,2))

    def testBlock(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Elephant
        board[Side.BLACK][5,3] = Soldier
        assert Position(6,4) not in Elephant.getPossibleMoves(board, Position(4,2))


class TestHorse:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Horse
        assert sortMoves(Horse.getPossibleMoves(board, Position(4,2))) == sortMoves([
            Position(file=3, rank=0),
            Position(file=2, rank=1),
            Position(file=2, rank=3),
            Position(file=3, rank=4),
            Position(file=5, rank=4),
            Position(file=6, rank=3),
            Position(file=6, rank=1),
            Position(file=5, rank=0)
        ])

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Horse
        board[Side.BLACK][3,4] = Soldier
        assert Position(3,4) in Horse.getPossibleMoves(board, Position(4,2))

    def testBlock(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Horse
        board[Side.BLACK][4,3] = Soldier
        possibleMoves = Horse.getPossibleMoves(board, Position(4,2))
        assert Position(3,4) not in possibleMoves
        assert Position(5,4) not in possibleMoves


class TestChariot:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Chariot
        assert sortMoves(Chariot.getPossibleMoves(board, Position(4,2))) == sortMoves([
            Position(file=0, rank=2),
            Position(file=1, rank=2),
            Position(file=2, rank=2),
            Position(file=3, rank=2),
            Position(file=5, rank=2),
            Position(file=6, rank=2),
            Position(file=7, rank=2),
            Position(file=8, rank=2),
            Position(file=4, rank=0),
            Position(file=4, rank=1),
            Position(file=4, rank=3),
            Position(file=4, rank=4),
            Position(file=4, rank=5),
            Position(file=4, rank=6),
            Position(file=4, rank=7),
            Position(file=4, rank=8),
            Position(file=4, rank=9),
        ])

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Chariot
        board[Side.BLACK][4,9] = Soldier
        assert Position(4,9) in Chariot.getPossibleMoves(board, Position(4,2))

    def testBlock(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Chariot
        board[Side.BLACK][4,5] = Soldier
        possibleMoves = Chariot.getPossibleMoves(board, Position(4,2))
        assert Position(4,6) not in possibleMoves
        assert Position(4,7) not in possibleMoves
        assert Position(4,8) not in possibleMoves
        assert Position(4,9) not in possibleMoves


class TestCannon:
    def testValidMoves(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Cannon
        assert sortMoves(Cannon.getPossibleMoves(board, Position(4,2))) == sortMoves([
            Position(file=0, rank=2),
            Position(file=1, rank=2),
            Position(file=2, rank=2),
            Position(file=3, rank=2),
            Position(file=5, rank=2),
            Position(file=6, rank=2),
            Position(file=7, rank=2),
            Position(file=8, rank=2),
            Position(file=4, rank=0),
            Position(file=4, rank=1),
            Position(file=4, rank=3),
            Position(file=4, rank=4),
            Position(file=4, rank=5),
            Position(file=4, rank=6),
            Position(file=4, rank=7),
            Position(file=4, rank=8),
            Position(file=4, rank=9),
        ])

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Cannon
        board[Side.BLACK][4,5] = Cannon
        board[Side.BLACK][4,9] = Soldier
        possibleMoves = Cannon.getPossibleMoves(board, Position(4,2))
        assert Position(4,5) not in possibleMoves
        assert Position(4,9) in possibleMoves

    def testBlock(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Cannon
        board[Side.BLACK][4,5] = Soldier
        possibleMoves = Cannon.getPossibleMoves(board, Position(4,2))
        assert Position(4,6) not in possibleMoves
        assert Position(4,7) not in possibleMoves
        assert Position(4,8) not in possibleMoves
        assert Position(4,9) not in possibleMoves

    
class TestSoldier:
    def testRedValidMovesBeforeRiver(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Soldier
        assert sortMoves(Soldier.getPossibleMoves(board, Position(4,2))) == sortMoves([
            Position(file=4, rank=3)
        ])

    def testBlackValidMovesBeforeRiver(self) -> None:
        board = Board()
        board[Side.BLACK][4,7] = Soldier
        assert sortMoves(Soldier.getPossibleMoves(board, Position(4,7))) == sortMoves([
            Position(file=4, rank=6)
        ])

    def testRedValidMovesAfterRiver(self) -> None:
        board = Board()
        board[Side.RED][4,5] = Soldier
        assert sortMoves(Soldier.getPossibleMoves(board, Position(4,5))) == sortMoves([
            Position(file=3, rank=5),
            Position(file=4, rank=6),
            Position(file=5, rank=5)
        ])

    def testBlackValidMovesAfterRiver(self) -> None:
        board = Board()
        board[Side.BLACK][4,4] = Soldier
        assert sortMoves(Soldier.getPossibleMoves(board, Position(4,4))) == sortMoves([
            Position(file=3, rank=4),
            Position(file=4, rank=3),
            Position(file=5, rank=4)
        ])

    def testCapture(self) -> None:
        board = Board()
        board[Side.RED][4,2] = Soldier
        board[Side.BLACK][4,3] = Soldier
        assert Position(4,3) in Soldier.getPossibleMoves(board, Position(4,2))
