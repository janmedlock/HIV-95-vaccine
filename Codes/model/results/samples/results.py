'''
Store and retrieve results from simulations with parameter samples.

.. todo:: Use HDF instead of pickle.  HDF can do random access instead
          of reading the whole file, so all the complicated caching
          I'm doing could hopefully be removed.
'''

import collections
import os

from .. import common
from ... import datasheet
from ... import multicountry
from ... import picklefile


class Results:
    '''
    Class to load the data on demand.
    '''
    def __init__(self, country, target):
        if (not self.exists(country, target)) and (not country == 'Global'):
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
        if ((self._country == 'Global')
            and (not self.exists(self._country, self._target))):
            print('Building Global, {}...'.format(self._target))
            self._build_global()
        else:
            print('Loading data for {}, {}...'.format(self._country,
                                                      self._target))
            path = self.get_path(self._country, self._target)
            self._data = picklefile.load(path)

    def _build_global(self):
        # OrderedDict so that the countries' Results._load_data() are called
        # in order later by multicountry.Global()
        data = collections.OrderedDict()
        for country in sorted(datasheet.get_country_list()):
            data[country] = Results(country, self._target)
        self._data = multicountry.Global(data)
        
    def __getattr__(self, key):
        # Don't use ._data for special attrs.
        if key.startswith('__') and key.endswith('__'):
            raise AttributeError
        else:
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
