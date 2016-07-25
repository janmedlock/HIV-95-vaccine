'''
Store and retrieve results from simulations with parameter modes.
'''

import collections
import os.path
import warnings

import tables

from . import common
from .. import container
from .. import global_


class ModesResultsCountryTarget:
    '''
    Store results in an object like `obj.attr`.
    '''


class ModesResultsCountry(container.DefaultOrderedDict):
    '''
    Store results in an object like `obj[target].attr`.
    '''
    def __init__(self):
        super().__init__(ModesResultsCountryTarget)


class ModesResults(container.DefaultOrderedDict):
    '''
    Store results in an object like `obj[country][target].attr`.
    Back that object with a mod:`tables` HDF5 store.
    '''
    # attrs_to_dump are the global_.Global().keys(),
    # plus 't',
    # plus any @properties of global_.Global()
    # (e.g. prevalence, incidence, etc).
    attrs_to_dump = list(global_.Global._keys) + ['t']
    for _attr in dir(global_.Global):
        obj = getattr(global_.Global, _attr)
        if isinstance(obj, property):
            attrs_to_dump.append(_attr)

    def __init__(self, filename = None, mode = 'r'):
        super().__init__(ModesResultsCountry)
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
            self._h5file.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

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
    return ModesResults(os.path.join(common.resultsdir,
                                     'modes.h5'))


def load_vaccine_sensitivity():
    return ModesResults(os.path.join(common.resultsdir,
                                     'vaccine_sensitivity.h5'))
