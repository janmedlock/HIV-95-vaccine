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


def exists(country):
    resultsfile = Results.get_path(country)
    return os.path.exists(resultsfile)
    

def dump(country, results):
    resultsfile = Results.get_path(country)
    with open(resultsfile, 'wb') as fd:
        pickle.dump(results, fd)


class Results:
    '''
    Class to load the data on demand, with getfield cached for speed.

    .. todo:: Fix `_getfield_cached` use of `.baseline`.
    '''
    def __init__(self, country):
        self._country = country
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        pass

    def _load_data(self):
        print('Loading data for {}...'.format(self._country))
        if self._country == 'Global':
            self._build_global()
        else:
            path = self.get_path(self._country)
            with open(path, 'rb') as fd:
                self._data = pickle.load(fd)

    def _build_global(self):
        data = {}
        for f in sorted(os.listdir(resultsdir)):
            if f.endswith('.pkl'):
                country = f.replace('.pkl', '')
                data[country] = Results(country)
        self._data = global_.Global(data)
        
    def __getattr__(self, key):
        if self._data is None:
            self._load_data()
        return getattr(self._data, key)

    def getfield(self, field, force_call = False):
        if force_call:
            # Don't use the value in the cache.
            return _getfield_cached.call(self._country, field, self)
        else:
            return _getfield_cached(self._country, field, self)

    def flush(self):
        del self._data
        self._data = None

    @staticmethod
    def get_path(country):
        path = os.path.join(resultsdir, '{}.pkl'.format(country))
        return path


_cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '_joblib')
_mem = joblib.Memory(cachedir = _cachedir)
@_mem.cache(ignore = ['results'])
def _getfield_cached(country, field, results):
    t = results.t
    retval = {}
    for (obj, k) in ((results.baseline, 'Status Quo'),
                     (results, '90–90–90')):
        if field == 'incidence':
            ni = numpy.asarray(obj.new_infections)
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        elif field == 'incidence_per_capita':
            ni = numpy.asarray(obj.new_infections)
            n = numpy.asarray(obj.alive)
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
        elif field.endswith('_per_capita'):
            field_ = field.replace('_per_capita', '')
            x = numpy.asarray(getattr(obj, field_))
            n = numpy.asarray(obj.alive)
            retval[k] = x / n
        else:
            retval[k] = getattr(obj, field)
    if field.startswith('incidence'):
        t = t[1 : ]
    return (t, retval)


def _clear_cache():
    _mem.clear()
