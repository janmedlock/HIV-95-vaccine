'''
Cache results to disk.
'''

import inspect
import os
import shelve


class shelved:
    def __init__(self, func):
        self._func = func

        # Put the cache file in the same directory as the caller.
        funcdir = os.path.dirname(inspect.getfile(self._func))
        cachedir = os.path.join(funcdir, '_shelve')
        if not os.path.exists(cachedir):
            os.mkdir(cachedir)

        # Name the cache file func.__name__
        cachefile = os.path.join(cachedir,
                                 str(self._func.__name__))
        self.cache = shelve.open(cachefile)

    def __call__(self, *args, **kwargs):
        key = str((args, set(kwargs.items())))

        try:
            # Try to get value from the cache.
            val = self.cache[key]
        except KeyError:
            # Get the value and store it in the cache.
            val = self.cache[key] = self._func(*args, **kwargs)
        return val

    def __del__(self):
        self.cache.close()
