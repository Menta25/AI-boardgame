import logging
from time import sleep
from math import log10
from typing import List, Dict, Any, Tuple, Type, Callable, Optional


def retry(times: int, exceptions: Tuple[Type[Exception],...], callback: Optional[Callable[[Callable[..., Any], str], Any]] = None) -> Callable:
    def decorator(function: Callable) -> Callable:
        def newFunction(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
            attempt = 0
            while attempt < times:
                try:
                    return function(*args, **kwargs)
                except exceptions as exception:
                    attempt += 1
                    logging.error(f"Exception thrown when attempting to run {function.__name__}, attempt {attempt} of {times}")
                    logging.error(str(exception))
                    sleep(attempt*log10(attempt))
            if callback is not None:
                callback(function.__name__, newFunction, args, kwargs)
            else:
                raise exception
        return newFunction
    return decorator


def rerunAfterCorrection(functionName: str, function: Callable[..., Any], *args: List[Any], **kwargs: Dict[str, Any]) -> Any:
    input(f"Press any key if the correction was made for {functionName}")
    return function(*args, **kwargs)
    