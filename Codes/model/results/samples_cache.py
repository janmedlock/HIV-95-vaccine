'''
Cache results from simulations with parameter samples.
'''

import collections
import os.path
import time
import warnings
import weakref

import tables

from . import common
from . import samples


class ResultsCacheCountryTarget:
    '''
    Store results in an object like `obj.attr`.
    '''
    def __init__(self, parent, target):
        self._parent = weakref.ref(parent)
        self._target = target

    def _is_current(self, attr):
        if attr not in self.__dict__:
            return False
        else:
            return self._parent()._is_current(self._target, attr)

    def __getattr__(self, attr):
        if not self._is_current(attr):
            value = self._parent()._load(self._target, attr)
            self.__setattr__(attr, value)
        else:
            value = super().__getattr__(attr)
        return value


class ResultsCacheCountry(collections.OrderedDict):
    '''
    Store results in an object like `obj[target].attr`.

    Make sure the `target` key is a string.
    '''
    def __init__(self, parent, country):
        super().__init__()
        self._parent = weakref.ref(parent)
        self._country = country

    def __getitem__(self, target):
        target = str(target)
        try:
            return super().__getitem__(target)
        except KeyError:
            return self.__missing__(target)

    def __missing__(self, target):
        target = str(target)
        if self._exists(target):
            self[target] = value = ResultsCacheCountryTarget(self,
                                                             target)
            return value
        else:
            raise FileNotFoundError(
                "No results for country '{}', target '{}' found!".format(
                    self._country, target))

    def __setitem__(self, target, value):
        target = str(target)
        return super().__setitem__(target, value)

    def __delitem__(self, target):
        target = str(target)
        return super().__delitem__(target)

    def _is_current(self, target, attr):
        if target not in self:
            return False
        else:
            return self._parent()._is_current(self._country, target, attr)

    def _load(self, target, attr):
        return self._parent()._load(self._country, target, attr)

    def _exists(self, target):
        return self._parent()._exists(self._country, target)


class ResultsCache(collections.OrderedDict):
    '''
    Disk cache for :class:`model.results.samples.Results` for speed.
    Store results in an object like `obj[country][target].attr`.
    '''
    def __init__(self):
        super().__init__()
        filename = os.path.join(common.resultsdir, '_cache.h5')
        self._h5file = tables.open_file(filename, 'a')
        for country_group in self._h5file.root:
            country = country_group._v_name
            for target_group in country_group:
                target = target_group._v_name
                for item in target_group:
                    setattr(self[country][target], item.name, item)

    def __getitem__(self, country):
        try:
            return super().__getitem__(country)
        except KeyError:
            return self.__missing__(country)

    def __missing__(self, country):
        if self._exists(country):
            self[country] = value = ResultsCacheCountry(self, country)
            return value
        else:
            raise FileNotFoundError(
                "No results for country '{}' found!".format(country))

    def close(self):
        self._h5file.close()

    def _is_current(self, country, target, attr):
        if target not in self:
            return False
        else:
            cache_entry = getattr(self[country][target], attr)
            data_file = samples.Results.get_path(country, target)
            mtime_cache = cache_entry.attrs.mtime
            mtime_data = os.path.getmtime(data_file)
            return (mtime_data <= mtime_cache)

    def _load(self, country, target, attr):
        with samples.Results(country, target) as results:
                value = getattr(results, attr)
        h5path = '/{}/{}'.format(country, target)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                                    category = tables.NaturalNameWarning)
            array = self._h5file.create_array(h5path, attr, value,
                                              createparents = True)
        array.attrs.mtime = time.time()
        return array

    def _exists(self, country, target = None):
        data_file = samples.Results.get_path(country, target)
        return os.path.exists(data_file)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()
