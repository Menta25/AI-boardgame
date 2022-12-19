# pylint: disable=no-name-in-module

import logging
from abc import ABC
from threading import Event
from time import sleep
from math import log10
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Type, Callable, Optional
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject


class FinalMeta(type(ABC), type(QObject)):
    pass


@dataclass
class Utils(QObject):
    event: Event = field(default=Event(), init=False)
    waitForCorrection: pyqtSignal = field(default=pyqtSignal(str), init=False)
    statusUpdate: pyqtSignal = field(default=pyqtSignal(str), init=False)

    @pyqtSlot()
    def clearEvent(self) -> None:
        self.event.clear()


utils = Utils()


def retry(times: int, exceptions: Tuple[Type[Exception],...], callback: Optional[Callable[[Callable[..., Any], str], Any]] = None) -> Callable:
    def decorator(function: Callable) -> Callable:
        def newFunction(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            attempt = 0
            lastException = None
            while attempt < times:
                try:
                    return function(*args, **kwargs)
                except exceptions as exception:
                    lastException = exception
                    attempt += 1
                    logging.error("Exception thrown when attempting to run {functionName}, attempt {attempt} of {times}", functionName=function.__name__, attempt=attempt, times=times)
                    logging.error(str(exception))
                    sleep(attempt*log10(attempt))
            if callback is not None:
                return callback(function.__name__, newFunction, args, kwargs)
            else:
                raise lastException
        return newFunction
    return decorator


def rerunAfterCorrection(functionName: str, function: Callable[..., Any], args: List[Any], kwargs: Dict[str, Any]) -> Any:
    utils.waitForCorrection.emit(f"Press any key if the correction was made for {functionName}")
    utils.event.set()
    return function(*args, **kwargs)
    