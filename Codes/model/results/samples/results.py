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
from ... import regions


_regions = ['Global'] + regions.all_


def _is_region(x):
    return (x in _regions)


def _is_country(x):
    return (not _is_region(x))


def get_path(country_or_region, target):
    if isinstance(target, type):
        # It's a class.
        target = target()
    if target is not None:
        path = os.path.join(common.resultsdir,
                            country_or_region,
                            '{}.pkl'.format(str(target)))
    else:
        path = os.path.join(common.resultsdir,
                            country_or_region)
    return path


def exists(country_or_region, target):
    resultsfile = get_path(country_or_region, target)
    return os.path.exists(resultsfile)


class Results:
    '''
    Class to load the data on demand.
    '''
    def __init__(self, country_or_region, target):
        self._country_or_region = country_or_region
        # Convert to string in case its an instance.
        self._target = str(target)

        if (not self.exists) and _is_country(self._country_or_region):
            raise FileNotFoundError("'{}', '{}' not found!".format(
                self._country_or_region, self._target))
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        pass

    def _load_data(self):
        if _is_region(self._country_or_region) and (not self.exists):
            print('Building {}, {}...'.format(self._country_or_region,
                                              self._target))
            self._build_regional()
        else:
            print('Loading data for {}, {}...'.format(self._country_or_region,
                                                      self._target))
            self._data = picklefile.load(self.path)

    def _build_regional(self):
        # OrderedDict so that the countries' Results._load_data() are called
        # in order later by multicountry.MultiCountry()
        data = collections.OrderedDict()
        if self._country_or_region == 'Global':
            for country in sorted(datasheet.get_country_list()):
                data[country] = load(country, self._target)
            self._data = multicountry.Global(data)
        else:
            for country in sorted(regions.regions[self._country_or_region]):
                data[country] = load(country, self._target)
            self._data = multicountry.MultiCountry(data)

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

    @property
    def path(self):
        return get_path(self._country_or_region, self._target)

    @property
    def exists(self):
        return exists(self._country_or_region, self._target)


def load(country_or_region, target):
    return Results(country_or_region, target)


def dump(country_or_region, target, results):
    resultsfile = get_path(country_or_region, target)
    resultsdir = os.path.dirname(resultsfile)
    if not os.path.exists(resultsdir):
        os.mkdir(resultsdir)
    picklefile.dump(results, resultsfile)
