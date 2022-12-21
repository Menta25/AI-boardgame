"""Robot arm control"""

import logging
from math import radians, degrees
from time import sleep
from enum import IntEnum, unique
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, ClassVar, Callable
import numpy as np
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports
from uarm.swift.protocol import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND


@unique
class Servo(IntEnum):
    """Enum class for indentifying robot servos"""
    BOTTOM = SERVO_BOTTOM
    LEFT = SERVO_LEFT
    RIGHT = SERVO_RIGHT
    HAND = SERVO_HAND


@dataclass(frozen=True)
class RobotArmException(Exception):
    """Exception for robot arm errors"""
    message: str

    def __str__(self) -> str:
        return self.message


class RobotArm:
    """Wrapper class for the Swift API and the robot arm for better control"""
    swift: SwiftAPI
    """Swift API instance"""
    speed: int
    """Robot arm move speed"""

    freeMoveHeightLimit: ClassVar[float] = 35.0
    """Minimum height for free movement"""
    resetPosition: ClassVar[Tuple[float, float, float]] = (200.0, 0.0, freeMoveHeightLimit)
    """Robot arm's reset position"""

    def __init__(self, speed: int = 1000, hardwareID: Optional[str] = None) -> None:
        """Constructs a RobotArm object

        :param speed: Robot arm move speed, defaults to 1000
        :type speed: int, optional
        :param hardwareID: Hardware ID, defaults to USB VID:PID=2341:0042
        :type hardwareID: Optional[str], optional
        :raises RobotArmException: No hardware found with given ID
        """
        if hardwareID is None:
            hardwareID = "USB VID:PID=2341:0042"

        filters = {"hwid": hardwareID}
        if len(get_ports(filters=filters)) == 0:
            raise RobotArmException(f"Cannot initialize robot arm with hardware ID: {hardwareID}")

        self.swift = SwiftAPI(filters=filters, do_not_open=True)
        self.speed = speed

    @property
    def isConnected(self) -> bool:
        """Check if robot arm is currently connected"""
        return bool(self.swift.connected)

    @property
    def info(self) -> Optional[Dict[str, str]]:
        """Device info"""
        info = self.swift.get_device_info()
        return info if isinstance(info, dict) else None

    @property
    def position(self) -> Optional[List[float]]:
        """Current cartesian position"""
        return self._getBase(self.swift.get_position)

    @property
    def polar(self) -> Optional[List[float]]:
        """Current polar position"""
        return self._getBase(self.swift.get_polar)

    @property
    def angle(self) -> Optional[List[float]]:
        """Current servo angles"""
        return self._getBase(self.swift.get_servo_angle)

    @property
    def isAllAttached(self) -> bool:
        """Check if servos are attached"""
        return self.swift.get_servo_attach(wait=True) is True

    @property
    def isPumpActive(self) -> bool:
        """Check if pump is active"""
        return self.swift.get_pump_status(wait=True) in [1,2]

    @property
    def isTouching(self) -> bool:
        """Check if limit switch is active"""
        return self.swift.get_limit_switch(wait=True) is True

    def _getBase(self, getFunc: Callable) -> Optional[List[float]]:
        if self.isAllAttached:
            info = getFunc(wait=True)
            return info if isinstance(info, list) else None
        else:
            return None

    def connect(self) -> None:
        """Try to connect robot arm

        :raises RobotArmException: Cannot connect uArm Swift
        """
        try:
            self.swift.connect()
            self.swift.waiting_ready(timeout=3)
            logging.debug(f"Device info:\n{self.info}")
        except Exception as exception:
            raise RobotArmException("Cannot connect to uArm Swift") from exception
        else:
            self.swift.set_mode(mode=0)
            polar = self.polar
            safe = polar[-1] < self.freeMoveHeightLimit if polar is not None else True
            self.reset(safe=safe)

    def disconnect(self) -> None:
        """Disconnects robot arm if it is connected"""
        if self.isConnected:
            self.detach(safe=True)
            self.swift.disconnect()

    def isAttached(self, servo: Servo) -> bool:
        """Check if specific servo is attached
        """
        return self.swift.get_servo_attach(servo.value, wait=True) is True

    def detach(self, safe: bool = True) -> None:
        """Detach robot arm servos

        :param safe: Move above height limit and lower after resetting, defaults to True
        :type safe: bool, optional
        """
        if self.isAllAttached:
            if safe is True:
                self.reset(safe=True)
                self.lowerDown(speed=2000)
            self.swift.set_servo_detach()

    def attach(self) -> None:
        """Attach robot arm servos
        """
        if not self.isAllAttached:
            self.swift.set_servo_attach()

    def lowerDown(self, speed: Optional[int] = 1000) -> None:
        """Lower robot arm until limit switch activates

        :param speed: Lower speed, defaults to 1000
        :type speed: Optional[int], optional
        :raises RobotArmException: Servos are not attached
        """
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot lower arm")

        if speed is None:
            speed = self.speed
        while not self.isTouching:
            self.swift.set_polar(height=-1, relative=True, speed=speed)
            self.swift.flush_cmd(wait_stop=True)

    def moveVertical(self, height: Optional[float] = None, speed: Optional[int] = None) -> None:
        """Move robot arm vertical

        :param height: Height to move, defaults to move height limit
        :type height: Optional[float], optional
        :param speed: Vertical move speed, defaults to robot's base speed
        :type speed: Optional[int], optional
        :raises RobotArmException: Servos are not attached
        """
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
        """Move robot arm horizontal

        :param stretch: Polar position's rho distance
        :type stretch: float
        :param rotation: Polar position's phi angle in degrees
        :type rotation: float
        :param speed: Horizontal move speed, defaults to robot's base speed
        :type speed: Optional[int], optional
        :raises RobotArmException: Servos are not attached
        """
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot raise arm")

        if speed is None:
            speed = self.speed

        _, _, height = self.polar
        self.swift.set_polar(stretch=stretch, rotation=rotation, height=height, speed=speed)
        self.swift.flush_cmd(wait_stop=True)

    def move(self, position: Tuple[float, float, Optional[float]], speed: Optional[int] = None, safe: bool = True, isCartesian: bool = False) -> None:
        """Moves robot arm. Bundles :meth:`~moveHorizontal` and :meth:`~moveVertical` for safe operation above a board.
        Safely lowers robot arm at the end of the move if position only consists of 2 value

        :param position: Position to move to
        :type position: Tuple[float, float, Optional[float]]
        :param speed: Move speed, defaults to robot's base speed
        :type speed: Optional[int], optional
        :param safe: Move above height limit, defaults to True
        :type safe: bool, optional
        :param isCartesian: Position is not in polar, defaults to False
        :type isCartesian: bool, optional
        :raises RobotArmException: Servos are not attached
        """
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot move")

        pos0, pos1, pos2 = position
        isRelative = pos2 is None
        if isCartesian:
            pos0, pos1 = self.cartesianToPolar(np.asarray([pos0, pos1]))
        if isRelative:
            pos2 = self.freeMoveHeightLimit

        polar = self.polar
        if safe is True and (polar is None or polar[-1] < self.freeMoveHeightLimit):
            self.moveVertical(height=self.freeMoveHeightLimit, speed=speed)

        self.moveHorizontal(stretch=pos0, rotation=pos1, speed=speed)
        self.moveVertical(height=pos2, speed=speed)

    def setAngle(self, servo: Servo, angle: float, speed: Optional[int] = None) -> None:
        """Set given servo's angle

        :param servo: Servo ID
        :type servo: Servo
        :param angle: Angle to set given servo
        :type angle: float
        :param speed: Move speed, defaults to robot's base speed
        :type speed: Optional[int], optional
        :raises RobotArmException: Servos are not attached
        """
        if not self.isAttached(servo):
            raise RobotArmException("Servo(s) not attached, cannot set angle")

        if speed is None:
            speed = self.speed
        self.swift.set_servo_angle(servo_id=servo.value, angle=angle)
        self.swift.flush_cmd(wait_stop=True)

    def reset(self, speed: Optional[int] = None, safe: bool = True) -> None:
        """Reset robot arm's position to \"origin\"

        :param speed: Move speed, defaults to robot's base speed
        :type speed: Optional[int], optional
        :param safe: Move above height limit, defaults to True
        :type safe: bool, optional
        """
        self.move(position=self.resetPosition, speed=speed, safe=safe)

    def setPump(self, on: bool = True) -> None:
        """Sets pump status

        :param on: Activate or deactivate, defaults to True
        :type on: bool, optional
        """
        self.swift.set_pump(on=on)
        sleep(0.25)

    @staticmethod
    def cartesianToPolar(cartesian: np.ndarray) -> np.ndarray:
        """Helper method for cartesian to polar conversion

        :param cartesian: Cartesian position
        :type cartesian: np.ndarray
        :return: Polar position
        :rtype: np.ndarray
        """
        x, y = cartesian
        rho = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y, x)
        phi = degrees(phi)+90.0
        return np.array([rho, phi])

    @staticmethod
    def polarToCartesian(polar: np.ndarray) -> np.ndarray:
        """Helper method for polar to cartesian conversion

        :param polar: Polar position
        :type polar: np.ndarray
        :return: Cartesian position
        :rtype: np.ndarray
        """
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
