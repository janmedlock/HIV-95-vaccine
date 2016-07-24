'''
Store and retrieve results from simulations with parameter modes.
'''

import collections
import os.path
import warnings

import tables

from . import common
from .. import global_


modesfile = os.path.join(common.resultsdir, 'modes.h5')
vaccine_sensitivity_file = os.path.join(common.resultsdir,
                                        'vaccine_sensitivity.h5')


class _DefaultOrderedDict(collections.OrderedDict):
    def __init__(self, default_factory):
        super().__init__()
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        self[key] = value = self.default_factory()
        return value


class ModesResults(_DefaultOrderedDict):
    class ModesCountry(_DefaultOrderedDict):
        class ModesSim:
            pass

        def __init__(self):
            super().__init__(self.ModesSim)

    def __init__(self, filename = None, mode = 'r'):
        super().__init__(self.ModesCountry)

        if filename is None:
            self._h5file = None
        else:
            self._h5file = tables.open_file(filename, mode)
            for country_group in self._h5file.root:
                country = country_group._v_name
                for target_group in country_group:
                    target = target_group._v_name
                    for item in target_group:
                        setattr(self[country][target], item.name, item)

    def close(self):
        if self._h5file is not None:
            try:
                self._h5file.close()
            except AttributeError:
                pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    attrs_to_dump = list(global_.Global._keys) + ['t']
    for _attr in dir(global_.Global):
        obj = getattr(global_.Global, _attr)
        if isinstance(obj, property):
            attrs_to_dump.append(_attr)

    def dump(self):
        root = self._h5file.root
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                                    category = tables.NaturalNameWarning)
            for (country, country_dict) in self.items():
                if country not in root:
                    country_group = self._h5file.create_group(root, country)
                for (target, sim) in country_dict.items():
                    if target  not in country_group:
                        target_group = self._h5file.create_group(country_group,
                                                                 target)
                    for attr in self.attrs_to_dump:
                        if attr not in target_group:
                            self._h5file.create_array(target_group,
                                                      attr,
                                                      getattr(sim, attr))
        self._h5file.flush()


def load_modes():
    return ModesResults(modesfile)


def load_vaccine_sensitivity():
    return ModesResults(vaccine_sensitivity_file)
