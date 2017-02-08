'''
Dump and load simulation results.
'''

import os

import joblib

from . import ODEs
from . import parameters
from . import simulation


resultsdir = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                           '../sim_data'))


def get_path(country, target, parameters_type = 'sample'):
    if parameters_type == 'sample' :
        suffix = ''
    else:
        suffix = '-' + parameters_type
    filename = '{}{}.pkl.z'.format(str(target), suffix)
    return os.path.join(resultsdir, country, filename)


def dump(obj, parameters_type = None):
    if parameters_type is None:
        # Try to guess.
        if isinstance(obj.parameters, parameters.Samples):
            parameters_type = 'sample'
        elif isinstance(obj.parameters, parameters.Mode):
            parameters_type = 'mode'

    path = get_path(obj.parameters.country, obj.target,
                    parameters_type = parameters_type)
    if not os.path.exists(os.path.dirname(path)):
        os.mkdirs(os.path.dirname(path))
    return joblib.dump(obj.state, path, compress = 3)


def load(country, target, parameters_type = 'sample'):
    path = get_path(country, target,
                    parameters_type = parameters_type)
    state = joblib.load(path, mmap_mode = 'r')
    return simulation._from_state(country, target, state, parameters_type)


def exists(country, target, parameters_type = 'sample'):
    path = get_path(obj.parameters.country, obj.target,
                    parameters_type = parameters_type)
    return os.path.exists(path)
