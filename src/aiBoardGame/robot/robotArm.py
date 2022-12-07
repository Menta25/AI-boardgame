import logging
import time
from enum import IntEnum, Enum, auto, unique
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, ClassVar, Callable, Literal, overload
from threading import Thread
from functools import partial
from queue import Queue, Empty, Full
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports
from uarm.swift.protocol import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND

@unique
class Servo(IntEnum):
    Bottom = SERVO_BOTTOM
    Left = SERVO_LEFT
    Right = SERVO_RIGHT
    Hand = SERVO_HAND


@unique
class MoveType(Enum):
    Position = auto()
    Polar = auto()


@dataclass(frozen=True)
class RobotArmException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class RobotArm:
    swift: SwiftAPI
    thread: Thread
    isRunning: bool
    speed: int

    freeMoveHeightLimit: ClassVar[float] = 60.0

    def __init__(self, hardwareID: str = "USB VID:PID=2341:0042", speed: int = 1000) -> None:
        filters = {"hwid": hardwareID}
        if len(get_ports(filters=filters)) == 0:
            raise RobotArmException(f"Cannot initialize robot arm with hardware ID: {hardwareID}")

        self.swift = SwiftAPI(filters=filters, do_not_open=True)
        self.thread = Thread(target=self._loop)
        self.isRunning = False
        self.speed = speed

    @property
    def isConnected(self) -> bool:
        return bool(self.swift.connected)

    @property
    def info(self) -> Optional[Dict[str, str]]:
        info = self.swift.get_device_info()
        return info if isinstance(info, dict) else None

    @property
    def position(self) -> Optional[List[float]]:
        return self._getBase(self.swift.get_position)

    @property
    def polar(self) -> Optional[List[float]]:
        return self._getBase(self.swift.get_polar)

    @property
    def angle(self) -> Optional[List[float]]:
        return self._getBase(self.swift.get_servo_angle)

    @property
    def isAllAttached(self) -> bool:
        return self.swift.get_servo_attach(wait=True) == True

    @property
    def isPumpActive(self) -> bool:
        return self.swift.get_pump_status(wait=True) in [1,2]

    @property
    def isTouching(self) -> bool:
        return self.swift.get_limit_switch(wait=True) == True

    def _getBase(self, getFunc: Callable) -> Optional[List[float]]:
        if self.isAllAttached:
            info = getFunc(wait=True)
            return info if isinstance(info, list) else None
        else:
            return None

    def connect(self) -> None:
        try:
            self.swift.connect()
            self.swift.waiting_ready(timeout=3)
            logging.debug(f"Device info:\n{self.info}")
        except Exception:
            raise RobotArmException("Cannot connect to uArm Swift")
        else:
            self.swift.set_mode(mode=0)
            self.resetPosition(speed=500000, safe=False)

    def disconnect(self) -> None:
        if self.isConnected:
            self.detach(safe=True)
            self.swift.disconnect()

    def isAttached(self, servo: Servo) -> bool:
        return self.swift.get_servo_attach(servo.value, wait=True) == True

    def detach(self, safe: bool = True) -> None:
        if self.isAllAttached:
            if safe is True:
                self.resetPosition(lowerDown=True)
            self.swift.set_servo_detach()

    def attach(self) -> None:
        if not self.isAllAttached:
            self.swift.set_servo_attach()

    @overload
    def move(self, to: Tuple[float, float, Literal[None]], speed: Optional[int], safe: Literal[True], isPolar: bool) -> None:
        ...

    @overload
    def move(self, to: Tuple[float, float, float], speed: Optional[int], safe: bool, isPolar: bool) -> None:
        ...

    def move(self, to: Tuple[float, float, Optional[float]], speed: Optional[int] = None, safe: bool = True, isPolar: bool = False) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot move")

        isRelative = to[2] == None
        if isRelative:
            to = (to[0], to[1], self.freeMoveHeightLimit/2.5)
        if speed is None:
            speed = self.speed

        position = self.position
        if safe is True and (position is None or position[-1] < self.freeMoveHeightLimit):
            self.swift.set_position(z=self.freeMoveHeightLimit)
            self.swift.flush_cmd(wait_stop=True)

        if not isPolar:
            moveFunc = self.swift.set_position
            horizontalPartial = partial(moveFunc, x=to[0], y=to[1])
            verticalPartial = partial(moveFunc, z=to[2])
        else:
            moveFunc = self.swift.set_polar
            horizontalPartial = partial(moveFunc, stretch=to[0], rotation=to[1])
            verticalPartial = partial(moveFunc, height=to[2])

        extraArgs = {
            "speed": speed
        }

        horizontalPartial(**extraArgs)
        self.swift.flush_cmd(wait_stop=True)
        verticalPartial(**extraArgs)
        self.swift.flush_cmd(wait_stop=True)
        while isRelative and not self.isTouching:
            self.swift.set_position(z=-1, relative=True, speed=1000)
            self.swift.flush_cmd(wait_stop=True)
            
    def setAngle(self, servo: Servo, angle: float, speed: Optional[int] = None, wait: bool = True) -> None:
        if not self.isAttached(servo):
            raise RobotArmException("Servo(s) not attached, cannot set angle")

        if speed is None:
            speed = self.speed
        self.swift.set_servo_angle(servo_id=servo.value, angle=angle)
        if wait is True:
            self.swift.flush_cmd(wait_stop=True)

    def resetPosition(self, speed: Optional[int] = None, lowerDown: bool = False, safe: bool = True) -> None:
        self.move(to=(200.0, 0.0, 150.0), speed=speed, safe=safe, isPolar=True)
        if lowerDown is True:
            self.setAngle(servo=Servo.Right, angle=66.82, wait=True)

    def setPump(self, on: bool = True) -> None:
        self.swift.set_pump(on=on)

    def start(self) -> None:
        if not self.isConnected:
            self.connect()

        self.isRunning = True
        self.thread.start()

    def stop(self) -> None:
        if self.isRunning:
            self.isRunning = False
            if self.thread is not None:
                self.thread.join()
            self.disconnect()

    def _loop(self) -> None:
        while self.isRunning:
            pass


def savePoints() -> None:
    import json
    from pathlib import Path

    robot = None
    try:
        robot = RobotArm(speed=500000)
        robot.connect()

        robot.detach(safe=True)
        isRunning = True
        saves = []
        while isRunning:
            print("[0] Exit\n[1] Save\n[2] Write save")
            try:
                command = int(input("Command: "))
                if command == 0:
                    isRunning = False
                elif command == 1:
                    robot.attach()
                    saves.append({
                        "position": robot.position,
                        "polar": robot.polar,
                        "angle": robot.angle
                    })
                    robot.detach(safe=False)
                elif command == 2:
                    path = Path(input("Save path: ")).with_suffix(".txt")
                    with path.open(mode="w") as file:
                        file.write(json.dumps(saves, indent=4))
            except ValueError:
                continue
    except RobotArmException as error:
        print(error)
    finally:
        if robot is not None:
            robot.attach()
            robot.disconnect()


if __name__ == "__main__":
    savePoints()
