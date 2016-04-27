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


def dump(country, results):
    resultsfile = os.path.join(resultsdir,
                               '{}.pkl'.format(country))
    with open(resultsfile, 'wb') as fd:
        pickle.dump(results, fd)


class Results:
    '''
    Class to load the data on demand, with getfield cached for speed.
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
            self._data = self._build_global()
        else:
            path = os.path.join(resultsdir,
                                '{}.pkl'.format(self._country))
            with open(path, 'rb') as fd:
                self._data = pickle.load(fd)

    def _build_global(self):
        data = {}
        for f in os.listdir(resultsdir):
            if f.endswith('.pkl'):
                country = f.replace('.pkl', '')
                data[country] = Results(country)
        
    def __getattr__(self, key):
        if self._data is None:
            self._load_data()
        return getattr(self._data, key)

    def getfield(self, field):
        return _getfield_cached(self._country, field, self)

    def flush(self):
        del self._data
        self._data = None


cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '_joblib')
mem = joblib.Memory(cachedir = cachedir)
@mem.cache(ignore = ['results'])
def _getfield_cached(country, field, results):
    t = results.t
    retval = {}
    for (obj, k) in ((results.baseline, 'Status Quo'),
                     (results, '90–90–90')):
        if field == 'incidence':
            ni = numpy.vstack(obj.new_infections)
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        elif field == 'incidence_per_capita':
            ni = numpy.vstack(obj.new_infections)
            n = numpy.vstack(obj.alive)
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
        elif field.endswith('_per_capita'):
            field_ = field.replace('_per_capita', '')
            x = numpy.vstack(getattr(obj, field_))
            n = numpy.vstack(obj.alive)
            retval[k] = x / n
        else:
            retval[k] = getattr(obj, field)
    if field.startswith('incidence'):
        t = t[1 : ]
    return (t, retval)


def _clear_cache():
    mem.clear()
