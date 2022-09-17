from functools import wraps
from time import time
def timer(func):
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            print(f"Total execution time of {str(func)}: {end_ if end_ > 0 else 0} ms\n")
    return _time_it
