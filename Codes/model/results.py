'''
Store and retrieve simulation results.
'''

import atexit
import collections
import functools
import os
import pickle
import time

from . import global_


resultsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '../results')


def exists(country, target):
    resultsfile = Results.get_path(country, target)
    return os.path.exists(resultsfile)
    

def dump(country, target, results):
    resultsfile = Results.get_path(country, target)
    if not os.path.exists(os.path.join(resultsdir, country)):
        os.mkdir(os.path.join(resultsdir, country))
    with open(resultsfile, 'wb') as fd:
        pickle.dump(results, fd)


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
        print('Loading data for {} {}...'.format(self._country, self._target))
        if self._country == 'Global':
            self._build_global()
        else:
            path = self.get_path(self._country, self._target)
            with open(path, 'rb') as fd:
                self._data = pickle.load(fd)

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
    class ShelfItem:
        def __init__(self, value):
            self.value = value
            self.set_mtime()

        def set_mtime(self):
            self.mtime = time.time()

    def __init__(self):
        self._shelfpath = os.path.join(resultsdir, '_cache.pkl')
        # Delay opening shelf.
        # self._open_shelf()
        self._results = collections.defaultdict(dict)

    def _open_shelf(self):
        assert not hasattr(self, '_shelf')
        try:
            self._shelf = pickle.load(open(self._shelfpath, 'rb'))
        except FileNotFoundError:
            # The shelf is a three-deep dict:
            # _shelf[country][target][key]
            self._shelf = collections.defaultdict(
                functools.partial(collections.defaultdict, dict))
        self._shelf_updated = False
        atexit.register(self._write_shelf)

    def _open_shelf_if_needed(self):
        if not hasattr(self, '_shelf'):
            self._open_shelf()

    def _write_shelf(self):
        if self._shelf_updated:
            pickle.dump(self._shelf, open(self._shelfpath, 'wb'))

    def _is_current(self, key):
        country, target, attr = key
        if (attr not in self._shelf[country][target]):
            return False
        else:
            mtime_shelf = self._shelf[country][target][attr].mtime
            resultsfile = Results.get_path(country, target)
            mtime_data = os.path.getmtime(resultsfile)
            return (mtime_data <= mtime_shelf)

    def __getitem__(self, key):
        country, target, attr = key
        self._open_shelf_if_needed()
        if not self._is_current(key):
            if target not in self._results[country]:
                self._results[country][target] = Results(country, target)
            self.__setitem__(key, getattr(self._results[country][target],
                                          attr))
        return self._shelf[country][target][attr].value

    def __setitem__(self, key, value):
        country, target, attr = key
        self._open_shelf_if_needed()
        self._shelf[country][target][attr] = self.ShelfItem(value)
        self._shelf_updated = True

    def __delitem__(self, key):
        country, target, attr = key
        self._open_shelf_if_needed()
        del self._shelf[country][target][attr]
        if len(self._shelf[country][target]) == 0:
            del self._shelf[country][target]
            if len(self._shelf[country]) == 0:
                del self._shelf[country]
        self._shelf_updated = True

    def __len__(self):
        self._open_shelf_if_needed()
        return len(self._shelf)

    def __iter__(self):
        self._open_shelf_if_needed()
        return iter(self._shelf)


results_data = ResultsShelf()
