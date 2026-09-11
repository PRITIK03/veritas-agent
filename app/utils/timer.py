import time
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.perf_counter()
    result = {"latency_ms": None}
    yield result
    result["latency_ms"] = int((time.perf_counter() - start) * 1000)