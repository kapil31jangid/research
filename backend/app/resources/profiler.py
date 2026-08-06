"""Small local profiler used to measure in-process inference latency."""

from collections.abc import Callable
from time import perf_counter


def profile_call[**Parameters, Result](
    function: Callable[Parameters, Result], *args: Parameters.args, **kwargs: Parameters.kwargs
) -> tuple[Result, float]:
    """Return a function result with elapsed milliseconds."""
    started = perf_counter()
    result = function(*args, **kwargs)
    return result, (perf_counter() - started) * 1000
