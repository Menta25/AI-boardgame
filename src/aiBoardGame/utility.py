import logging
from time import sleep
from math import log10
from typing import List, Dict, Any, Tuple, Type, Callable, Optional

def retry(times: int, exceptions: Tuple[Type[Exception],...], callback: Optional[Callable[[Callable[..., Any], str], Any]] = None):
    def decorator(function: Callable):
        def newFunction(*args: List[Any], **kwargs: Dict[str, Any]):
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
                callback(newFunction, function.__name__)
            else:
                raise exception
        return newFunction
    return decorator


def rerunAfterCorrection(function: Callable[..., Any], functionName: str) -> Any:
    input(f"Press any key if the correction was made for {functionName}")
    return function()
    