'''
Store and retrieve results from simulations with parameter samples.

.. todo:: Use HDF instead of pickle.  HDF can do random access instead
          of reading the whole file, so all the complicated caching
          I'm doing could hopefully be removed.
'''

import os

from .. import common
from ... import global_
from ... import picklefile


class Results:
    '''
    Class to load the data on demand.
    '''
    def __init__(self, country, target):
        if not self.exists(country, target):
            raise FileNotFoundError("'{}', '{}' not found!".format(country,
                                                                   target))
        self._country = country
        # Convert to string in case its an instance.
        self._target = str(target)
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
        for country in sorted(os.listdir(common.resultsdir)):
            if os.path.isdir(os.path.join(common.resultsdir, country)):
                if exists(country, self._target):
                    data[country] = Results(country, self._target)
        self._data = global_.Global(data)
        
    def __getattr__(self, key):
        if self._data is None:
            self._load_data()
        return getattr(self._data, key)

    def keys(self):
        if self._data is None:
            self._load_data()
        return self._data.keys()

    def flush(self):
        del self._data
        self._data = None

    @staticmethod
    def get_path(country, target):
        if isinstance(target, type):
            # It's a class.
            target = target()
        if target is not None:
            path = os.path.join(common.resultsdir, country,
                                '{!s}.pkl'.format(target))
        else:
            path = os.path.join(common.resultsdir, country)
        return path

    @classmethod
    def exists(cls, country, target):
        resultsfile = cls.get_path(country, target)
        return os.path.exists(resultsfile)


def exists(country, target):
    return Results.exists(country, target)


def dump(country, target, results):
    resultsfile = Results.get_path(country, target)
    if not os.path.exists(os.path.join(common.resultsdir, country)):
        os.mkdir(os.path.join(common.resultsdir, country))
    picklefile.dump(results, resultsfile)
