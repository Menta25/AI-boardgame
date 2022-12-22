"""Utility class, decorator and function for gameplay"""

# pylint: disable=no-name-in-module,unnecessary-pass

import logging
from abc import ABCMeta
from threading import Event
from time import sleep
from math import log10
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Type, Callable, Optional
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject


class FinalMeta(ABCMeta, type(QObject)):
    """Metaclass to combine Abstract Base Class and QObject"""
    pass


@dataclass
class Utils(QObject):
    """Utility class for game thread control and general signal"""
    waitEvent: Event = field(default=Event(), init=False)
    """Thread event raised when game has to wait"""
    waitForCorrection: pyqtSignal = field(default=pyqtSignal(str), init=False)
    """Signal emitted when game needs to corrected"""
    statusUpdate: pyqtSignal = field(default=pyqtSignal(str), init=False)
    """Signal emitted when game status is updated"""

    def __post_init__(self) -> None:
        super().__init__()

    @pyqtSlot()
    def continueRun(self) -> None:
        """Continue game thread operation
        """
        self.waitEvent.set()

    def pauseRun(self) -> None:
        """Pause game thread operation
        """
        self.waitEvent.clear()
        self.waitEvent.wait()


utils = Utils()


def retry(times: int, exceptions: Tuple[Type[Exception],...], callback: Optional[Callable[[Callable[..., Any], str], Any]] = None) -> Callable:
    """Retry decorated function several times

    :param times: Times to retry wrapped function
    :type times: int
    :param exceptions: Only retry if given exceptions are raised
    :type exceptions: Tuple[Type[Exception],...]
    :param callback: Run callback function if all retry failed, if None reraise last exception, defaults to None
    :type callback: Optional[Callable[[Callable[..., Any], str], Any]], optional
    :return: Decorated function
    :rtype: Callable
    """
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
                    logging.error(f"Exception thrown when attempting to run {function.__name__}, attempt {attempt} of {times}")
                    logging.error(str(exception))
                    utils.statusUpdate.emit(str(exception))
                    sleep(attempt*log10(attempt))
            if callback is not None:
                return callback(function.__name__, newFunction, args, kwargs)
            else:
                raise lastException
        return newFunction
    return decorator


def rerunAfterCorrection(functionName: str, function: Callable[..., Any], args: List[Any], kwargs: Dict[str, Any]) -> Any:
    """Rerun function with arguments

    :param functionName: Name of function
    :type functionName: str
    :param function: Function to rerun
    :type function: Callable[..., Any]
    :param args: Positional arguments for function
    :type args: List[Any]
    :param kwargs: Keyword arguments for function
    :type kwargs: Dict[str, Any]
    :return: Function return value
    :rtype: Any
    """
    utils.waitForCorrection.emit(f"Press any key if the correction was made for {functionName}")
    utils.pauseRun()
    return function(*args, **kwargs)
    