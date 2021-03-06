'''
Dump and load simulation results.
'''

import os

import joblib

from . import output_dir
from . import multicountry
from . import ODEs
from . import parameters
from . import regions
from . import simulation


def get_path(place, target, parameters_type = 'sample'):
    if parameters_type == 'sample' :
        suffix = ''
    else:
        suffix = '-' + parameters_type
    filename = '{}{}.pkl'.format(str(target), suffix)
    return os.path.join(output_dir.output_dir, place, filename)


def dump(obj, parameters_type = None, compress = False):
    if isinstance(obj, multicountry.MultiCountry):
        # Guess.
        if parameters_type is None:
            parameters_type = 'sample'
        path = get_path(obj.region, obj.target, parameters_type)
    else:
        if parameters_type is None:
            # Try to guess.
            if isinstance(obj.parameters, parameters.Samples):
                parameters_type = 'sample'
            elif isinstance(obj.parameters, parameters.Mode):
                parameters_type = 'mode'
        path = get_path(obj.parameters.country, obj.target,
                        parameters_type = parameters_type)
    if not os.path.exists(os.path.dirname(path)):
        os.mkdir(os.path.dirname(path))
    return joblib.dump(obj.state, path, compress = compress, protocol = -1)


def load(place, target, parameters_type = 'sample'):
    path = get_path(place,
                    target,
                    parameters_type = parameters_type)
    state = joblib.load(path, mmap_mode = 'r')
    if place == 'Global':
        return multicountry.Global._from_state(target,
                                               state)
    elif place in regions.regions:
        return multicountry.MultiCountry._from_state(place,
                                                     target,
                                                     state)
    else:
        return simulation._from_state(place,
                                      target,
                                      state,
                                      parameters_type)


def exists(place, target, parameters_type = 'sample'):
    path = get_path(place, target,
                    parameters_type = parameters_type)
    return os.path.exists(path)
