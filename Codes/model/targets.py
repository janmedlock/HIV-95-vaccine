'''
Get the current target values for diagnosis, treatment, and viral suppression
from the overall target goals.
'''

import functools

import numpy

from . import container
from . import proportions


class TargetValues(container.Container):
    '''
    Target values over time.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed')

    def __init__(self, t, targets, parameters,
                 time_to_full_implementation = 5):
        '''
        From the initial proportions read from
        :attr:`model.datasheet.Parameters.initial_conditions`,
        the target values go linearly from the initial proportions to `targets`
        in `time_to_full_implementation` years, then stay constant at
        `targets` after that.
        '''
        initial_proportions = proportions.Proportions(
            parameters.initial_conditions)

        # Convert special strings to numerical values.
        if isinstance(targets, str):
            if targets == '909090':
                # Max of 90% and current the current level.
                targets = [numpy.clip(v, 0.9, None)
                           for v in initial_proportions.values()]
            elif targets == 'base':
                # Fixed at initial values.
                targets = initial_proportions.values()
            elif targets == 'nothing':
                targets = numpy.zeros_like(self._keys)

        # Use names for entries.
        targets = numpy.rec.fromarrays(targets,
                                       names = ','.join(self._keys))

        # Go from 0% to 100% over the first time_to_full_implementation years.
        amount_implemented = (numpy.clip(t, 0, time_to_full_implementation)
                              / time_to_full_implementation)

        for k in self._keys:
            initial_proportion = getattr(initial_proportions, k)
            target = getattr(targets, k)
            v = (initial_proportion
                 + (target - initial_proportion) * amount_implemented)
            setattr(self, k, v)
