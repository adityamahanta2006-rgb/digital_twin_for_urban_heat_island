'''
 * @author QiongjieX
 * @email qiongjie.xu@polimi.it
 * @create date 2024-07-10 12:09:55
 * @modify date 2024-07-10 12:09:55
 * @desc timing decorator
'''
from functools import wraps
from time import time

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(f"func: {f.__name__} args: [{args}, {kw}] took: {te-ts:.2f} secs / {(te-ts)/60:.2f} mins")
        return result
    return wrap

def only_timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(f"func: {f.__name__} took: {te-ts:.2f} secs / {(te-ts)/60:.2f} mins")
        return result
    return wrap