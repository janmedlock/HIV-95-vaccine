'''
Store and retrieve simulation results.
'''

import os
import pickle

import joblib
import numpy

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
    Class to load the data on demand, with getfield cached for speed.
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

    def getfield(self, field, force_call = False):
        if force_call:
            # Don't use the value in the cache.
            return _getfield_cached.call(self._country, self._target,
                                         field, self)
        else:
            return _getfield_cached(self._country, self._target, field, self)

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


_cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '_joblib')
_mem = joblib.Memory(cachedir = _cachedir)
@_mem.cache(ignore = ['results'])
def _getfield_cached(country, target, field, results):
    return getattr(results, field)


def _clear_cache():
    _mem.clear()
