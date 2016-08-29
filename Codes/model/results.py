'''
Dump and load simulation results.
'''

import os

import numpy

from . import simulation


resultsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '../results')


def get_path(country, targets, suffix = None):
    if suffix is None:
        suffix = ''
    filename = '{}{}.npy'.format(str(targets), suffix)
    return os.path.join(resultsdir, country, filename)


def dump(obj, suffix = None):
    path = get_path(obj.parameters.country, obj.targets, suffix = suffix)
    if not os.path.exists(os.path.dirname(path)):
        os.mkdirs(os.path.dirname(path))
    return numpy.save(path, obj.state)


def load(country, targets, suffix = None):
    path = get_path(country, targets, suffix = suffix)
    state = numpy.load(path)
    if state.ndim == 2:
        return simulation.Simulation._from_state(country, targets, state)
    elif numpy.ndim == 3:
        return multisim.Multisim._from_state(country, targets, state)
    else:
        raise ValueError('Unknown state.ndim == {}!'.format(state.ndim))
