'''
Get the current target values for diagnosis, treatment, and viral suppression
from the overall target goals.
'''

import functools

import numpy

from . import proportions


def get_target_values(t, targs, parameters,
                      time_to_full_implementation = 5):
    '''
    From the initial proportions read from
    :attr:`model.datasheet.Parameters.initial_conditions`,
    the target values go linearly from the initial proportions to `targs`
    in `time_to_full_implementation` years, then stay constant at
    `targs` after that.
    '''
    initial_proportions = proportions.get_proportions(
        parameters.initial_conditions)

    # Convert special strings to numerical values.
    if isinstance(targs, str):
        if targs == '909090':
            # Max of 90% and current the current level.
            targs = initial_proportions.clip(0.9, None)
        elif targs == 'base':
            # Fixed at initial values.
            targs = initial_proportions
        elif targs == 'nothing':
            targs = numpy.zeros(3)

    return (initial_proportions
            + ((targs - initial_proportions)
               * (numpy.atleast_1d(t).clip(0, time_to_full_implementation)
                  / time_to_full_implementation)[:, numpy.newaxis])).squeeze()
