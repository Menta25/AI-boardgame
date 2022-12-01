import logging
from enum import IntFlag
from time import sleep
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from threading import Thread
from functools import partial
from queue import Queue, Empty, Full
from uarm.wrapper import SwiftAPI
from uarm.tools.list_ports import get_ports
from uarm.swift.protocol import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND


class Servo(IntFlag):
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
    thread: Thread
    isRunning: bool
    speed: int

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
    def info(self) -> Dict[str, str]:
        info = self.swift.get_device_info()
        return info if isinstance(info, dict) else {}

    @property
    def isAllAttached(self) -> bool:
        return self.swift.get_servo_attach(wait=True)

    @property
    def isPumpActive(self) -> bool:
        return self.swift.get_pump_status() in [1,2]

    @property
    def isGrabbing(self) -> bool:
        return self.swift.get_pump_status() == 2

    def isAttached(self, servo: Servo) -> bool:
        return self.swift.get_servo_attach(servo.value, wait=True)

    def connect(self) -> None:
        try:
            self.swift.connect()
            self.swift.waiting_ready(timeout=3)
            logging.debug(f"Device info:\n{self.info}")
        except Exception:
            raise RobotArmException("Cannot connect to uArm Swift")
        else:
            self.swift.set_mode(mode=0)
            self.resetPosition(speed=500000)

    def disconnect(self) -> bool:
        if self.isConnected:
            self.detach(safe=True)
            self.swift.disconnect()
        
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

    def resetPosition(self, speed: Optional[int] = None, lowerDown: bool = False) -> None:
        self.move(position=(200.0, 0.0, 150.0), speed=speed, wait=True, isPolar=True)
        if lowerDown is True:
            self.setAngle(servo=Servo.Right, angle=66.82, wait=True)

    def move(self, position: Tuple[float, float, float], speed: Optional[int] = None, wait: bool = True, isPolar: bool = False) -> None:
        if not self.isAllAttached:
            raise RobotArmException("Servo(s) not attached, cannot move")

        if speed is None:
            speed = self.speed

        if not isPolar:
            x, y, z = position
            movePartial = partial(self.swift.set_position, x=x, y=y, z=z)
        else:
            stretch, rotation, height = position
            movePartial = partial(self.swift.set_polar, stretch=stretch, rotation=rotation, height=height)
        movePartial(speed=speed)
        if wait is True:
            self.swift.flush_cmd(wait_stop=True)

    def setAngle(self, servo: Servo, angle: float, speed: Optional[int] = None, wait: bool = True) -> None:
        if not self.isAttached(servo):
            raise RobotArmException("Servo(s) not attached, cannot set angle")

        if speed is None:
            speed = self.speed
        self.swift.set_servo_angle(servo_id=servo.value, angle=angle)
        if wait is True:
            self.swift.flush_cmd(wait_stop=True)

    def detach(self, safe: bool = True) -> None:
        if self.isAllAttached:
            if safe is True:
                self.resetPosition(lowerDown=True)
            self.swift.set_servo_detach()

    def attach(self) -> None:
        if not self.isAllAttached:
            self.swift.set_servo_attach()


if __name__ == "__main__":
    robot = RobotArm()
    robot.start()
