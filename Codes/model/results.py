'''
Store and retrieve simulation results.
'''

import atexit
import collections
import functools
import itertools
import os
import time

from . import global_
from . import picklefile


resultsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '../results')


def exists(country, target):
    resultsfile = Results.get_path(country, target)
    return os.path.exists(resultsfile)
    

def dump(country, target, results):
    resultsfile = Results.get_path(country, target)
    if not os.path.exists(os.path.join(resultsdir, country)):
        os.mkdir(os.path.join(resultsdir, country))
    picklefile.dump(results, resultsfile)


class Results:
    '''
    Class to load the data on demand.
    '''
    def __init__(self, country, target):
        self._country = country
        self._target = target
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        pass

    def _load_data(self):
        # print('Loading data for {} {}...'.format(self._country,
        #                                          self._target))
        if self._country == 'Global':
            self._build_global()
        else:
            path = self.get_path(self._country, self._target)
            self._data = picklefile.load(path)

    def _build_global(self):
        data = {}
        for country in sorted(os.listdir(resultsdir)):
            if os.path.isdir(os.path.join(resultsdir, country)):
                if exists(country, self._target):
                    data[country] = Results(country, self._target)
        self._data = global_.Global(data)
        
    def __getattr__(self, key):
        if self._data is None:
            self._load_data()
        return getattr(self._data, key)

    def flush(self):
        del self._data
        self._data = None

    @staticmethod
    def get_path(country, target):
        if isinstance(target, type):
            # It's a class.
            target = target()
        path = os.path.join(resultsdir, country, '{!s}.pkl'.format(target))
        return path


class ResultsShelf(collections.abc.MutableMapping):
    '''
    Disk cache for Results for speed.
    '''
    def __init__(self, debug = False):
        self.debug = debug
        self._shelfpath = os.path.join(resultsdir, '_cache.pkl')
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

    def _is_current(self, key):
        country, target, attr = key
        if (attr not in self._shelf[country][str(target)]):
            if self.debug:
                print("key = '{}' not in shelf.".format(key))
            return False
        else:
            mtime_shelf = self._shelf[country][str(target)][attr].mtime
            resultsfile = Results.get_path(country, target)
            mtime_data = os.path.getmtime(resultsfile)
            if self.debug:
                if (mtime_data <= mtime_shelf):
                    print("key = '{}' shelf up to date.".format(key))
                else:
                    print("key = '{}' shelf expired.".format(key))
            return (mtime_data <= mtime_shelf)

    def __getitem__(self, key):
        country, target, attr = key
        self._open_shelf_if_needed()
        if not self._is_current(key):
            if self.debug:
                print("Loading '{}' from Results({}, {}).".format(attr,
                                                                  country,
                                                                  target))
            with Results(country, target) as results:
                val = getattr(results, attr)
            self.__setitem__(key, val)
        return self._shelf[country][str(target)][attr].value

    def __setitem__(self, key, value):
        if self.debug:
            print("In __setitem__ for key = '{}'.".format(key))
        country, target, attr = key
        self._open_shelf_if_needed()
        self._shelf[country][str(target)][attr] = self.ShelfItem(value)
        self._shelf_updated = True

    def __delitem__(self, key):
        if self.debug:
            print("In __delitem__ for key = '{}'.".format(key))
        country, target, attr = key
        self._open_shelf_if_needed()
        del self._shelf[country][str(target)][attr]
        if len(self._shelf[country][str(target)]) == 0:
            del self._shelf[country][str(target)]
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
