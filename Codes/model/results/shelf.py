'''
Cache results from simulations with parameter samples.

.. todo:: Use HDF instead of pickle.
'''

import atexit
import collections
import functools
import itertools
import os.path
import time

from . import common
from . import samples
from .. import picklefile


class ResultsShelf(collections.abc.MutableMapping):
    '''
    Disk cache for :class:`samples.Results` for speed.
    '''
    def __init__(self, debug = False):
        self.debug = debug
        self._shelfpath = os.path.join(common.resultsdir, '_cache.pkl')
        # Delay opening shelf.
        # self._open_shelf()

    def _open_shelf(self):
        if self.debug:
            print('Opening shelf.')
        assert not hasattr(self, '_shelf')
        try:
            self._shelf = picklefile.load(self._shelfpath)
        except FileNotFoundError:
            # The shelf is a three-deep dict:
            # _shelf[country][target][key]
            self._shelf = collections.defaultdict(
                functools.partial(collections.defaultdict, dict))
        if self.debug:
            print('Opened shelf.')
        self._shelf_updated = False
        atexit.register(self._write_shelf)

    def _open_shelf_if_needed(self):
        if not hasattr(self, '_shelf'):
            self._open_shelf()

    def _write_shelf(self):
        if self.debug:
            print('In _write_shelf, _shelf_updated = {}.'.format(
                self._shelf_updated))
        if self._shelf_updated:
            picklefile.dump(self._shelf, self._shelfpath)
            self._shelf_updated = False

    class ShelfItem:
        def __init__(self, value):
            self.value = value
            self.set_mtime()

        def set_mtime(self):
            self.mtime = time.time()

    @staticmethod
    def _parse_key(key):
        country, target, attr = key
        return country, str(target), attr

    def _is_current(self, key):
        country, target, attr = self._parse_key(key)
        if (attr not in self._shelf[country][target]):
            if self.debug:
                print("key = '{}' not in shelf.".format(key))
            return False
        else:
            mtime_shelf = self._shelf[country][target][attr].mtime
            resultsfile = samples.Results.get_path(country, target)
            mtime_data = os.path.getmtime(resultsfile)
            if self.debug:
                if (mtime_data <= mtime_shelf):
                    print("key = '{}' shelf up to date.".format(key))
                else:
                    print("key = '{}' shelf expired.".format(key))
            return (mtime_data <= mtime_shelf)

    def __getitem__(self, key):
        country, target, attr = self._parse_key(key)
        self._open_shelf_if_needed()
        if not self._is_current(key):
            if self.debug:
                print("Loading '{}' from Results({}, {}).".format(attr,
                                                                  country,
                                                                  target))
            with samples.Results(country, target) as results:
                val = getattr(results, attr)
            self.__setitem__(key, val)
        return self._shelf[country][target][attr].value

    def __setitem__(self, key, value):
        if self.debug:
            print("In __setitem__ for key = '{}'.".format(key))
        country, target, attr = self._parse_key(key)
        self._open_shelf_if_needed()
        self._shelf[country][target][attr] = self.ShelfItem(value)
        self._shelf_updated = True

    def __delitem__(self, key):
        if self.debug:
            print("In __delitem__ for key = '{}'.".format(key))
        country, target, attr = self._parse_key(key)
        self._open_shelf_if_needed()
        del self._shelf[country][target][attr]
        if len(self._shelf[country][target]) == 0:
            del self._shelf[country][target]
            if len(self._shelf[country]) == 0:
                del self._shelf[country]
        self._shelf_updated = True

    def __len__(self):
        self._open_shelf_if_needed()
        # Sum over the 3 dict levels.
        return sum(sum(len(v1) for v1 in v0.values())
                   for v0 in self._shelf.values())

    def __iter__(self):
        self._open_shelf_if_needed()
        # First key level: country
        keys0 = self._shelf.keys()
        # First 2 key levels: country, target.
        keys1 = itertools.chain.from_iterable(
            (((country, target)
              for target in self._shelf[country].keys())
             for country in keys0))
        # 3 key levels: country, target, attr.
        keys2 = itertools.chain.from_iterable(
            (((country, target, attr)
              for attr in self._shelf[country][target].keys())
             for (country, target) in keys1))
        return keys2


data = ResultsShelf()
