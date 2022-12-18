import logging
import numpy as np
from math import radians, degrees
from time import sleep
from enum import IntEnum, unique
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, ClassVar, Callable
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports
from uarm.swift.protocol import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND


@unique
class Servo(IntEnum):
    Bottom = SERVO_BOTTOM
    Left = SERVO_LEFT
    Right = SERVO_RIGHT
    Hand = SERVO_HAND


@dataclass(frozen=True)
class RobotArmException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class RobotArm:
    swift: SwiftAPI
    speed: int

    freeMoveHeightLimit: ClassVar[float] = 35.0
    resetPosition: ClassVar[Tuple[float, float, float]] = (200.0, 0.0, freeMoveHeightLimit)

    def __init__(self, speed: int = 1000, hardwareID: Optional[str] = None) -> None:
        if hardwareID is None:
            hardwareID = "USB VID:PID=2341:0042"

        filters = {"hwid": hardwareID}
        if len(get_ports(filters=filters)) == 0:
            raise RobotArmException(f"Cannot initialize robot arm with hardware ID: {hardwareID}")

        self.swift = SwiftAPI(filters=filters, do_not_open=True)
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
            polar = self.polar
            safe = polar[-1] < self.freeMoveHeightLimit if polar is not None else True
            self.reset(safe=safe)

    def disconnect(self) -> None:
        if self.isConnected:
            self.detach(safe=True)
            self.swift.disconnect()

    def isAttached(self, servo: Servo) -> bool:
        return self.swift.get_servo_attach(servo.value, wait=True) == True

    def detach(self, safe: bool = True) -> None:
        if self.isAllAttached:
            if safe is True:
                self.reset(safe=True)
                self.lowerDown(speed=2000)
            self.swift.set_servo_detach()

    def attach(self) -> None:
        if not self.isAllAttached:
            self.swift.set_servo_attach()

    def lowerDown(self, speed: Optional[int] = 1000) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot lower arm")

        if speed is None:
            speed = self.speed
        while not self.isTouching:
            self.swift.set_polar(height=-1, relative=True, speed=speed)
            self.swift.flush_cmd(wait_stop=True)

    def moveVertical(self, height: Optional[float] = None, speed: Optional[int] = None) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot raise arm")

        if speed is None:
            speed = self.speed
        if height is None:
            height = self.freeMoveHeightLimit

        stretch, rotation, _ = self.polar
        self.swift.set_polar(stretch=stretch, rotation=rotation, height=height, speed=speed)
        self.swift.flush_cmd(wait_stop=True)

    def moveHorizontal(self, stretch: float, rotation: float, speed: Optional[int] = None) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot raise arm")

        if speed is None:
            speed = self.speed

        _, _, height = self.polar
        self.swift.set_polar(stretch=stretch, rotation=rotation, height=height, speed=speed)
        self.swift.flush_cmd(wait_stop=True)

    def move(self, to: Tuple[float, float, Optional[float]], speed: Optional[int] = None, safe: bool = True, isCartesian: bool = False) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot move")

        to0, to1, to2 = to
        isRelative = to2 == None
        if isCartesian:
            to0, to1 = self.cartesianToPolar(np.asarray([to0, to1]))
        if isRelative:
            to2 = self.freeMoveHeightLimit

        polar = self.polar
        if safe is True and (polar is None or polar[-1] < self.freeMoveHeightLimit):
            self.moveVertical(height=self.freeMoveHeightLimit, speed=speed)

        self.moveHorizontal(stretch=to0, rotation=to1, speed=speed)
        self.moveVertical(height=to2, speed=speed)
            
    def setAngle(self, servo: Servo, angle: float, speed: Optional[int] = None) -> None:
        if not self.isAttached(servo):
            raise RobotArmException("Servo(s) not attached, cannot set angle")

        if speed is None:
            speed = self.speed
        self.swift.set_servo_angle(servo_id=servo.value, angle=angle)
        self.swift.flush_cmd(wait_stop=True)

    def reset(self, speed: Optional[int] = None, safe: bool = True) -> None:
        self.move(to=self.resetPosition, speed=speed, safe=safe)

    def setPump(self, on: bool = True) -> None:
        self.swift.set_pump(on=on)
        sleep(0.25)

    @staticmethod
    def cartesianToPolar(cartesian: np.ndarray) -> np.ndarray:
        x, y = cartesian
        rho = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y, x)
        phi = degrees(phi)+90.0
        return np.array([rho, phi])

    @staticmethod
    def polarToCartesian(polar: np.ndarray) -> np.ndarray:
        rho, phi = polar
        phi = radians(phi-90.0)
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        return np.array([x, y])


if __name__ == "__main__":
    arm = RobotArm(speed=100_000)
    arm.connect()
    arm.detach()
    input("ready")
    arm.attach()
    arm.reset()
    arm.disconnect()
