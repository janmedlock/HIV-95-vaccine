'''
Dump and load simulation results.
'''

import os

import numpy

from . import simulation


resultsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '../results')


def get_path(country, target, parameters_type = 'sample'):
    if parameters_type == 'sample' :
        suffix = ''
    else:
        suffix = parameters_type
    filename = '{}{}.npz'.format(str(target), suffix)
    return os.path.join(resultsdir, country, filename)


def dump(obj, parameters_type = 'sample'):
    path = get_path(obj.parameters.country, obj.target,
                    parameters_type = parameters_type)
    if not os.path.exists(os.path.dirname(path)):
        os.mkdirs(os.path.dirname(path))
    return numpy.savez_compressed(path, obj.state)


def load(country, target, parameters_type = 'sample'):
    path = get_path(country, target,
                    parameters_type = parameters_type)
    state = numpy.load(path)[0]
    return simulation._from_state(country, target, state, parameters_type)
