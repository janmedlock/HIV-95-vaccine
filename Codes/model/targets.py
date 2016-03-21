'''
Get the current target values for diagnosis, treatment, and viral suppression
from the overall target goals.
'''

import functools

import numpy

from . import container
from . import control_rates
from . import proportions


class Target:
    '''
    Simple container for a single target.
    '''
    def __init__(self, target, time_to_start = 0,
                 time_to_full_implementation = 5):
        self.target = target
        self.time_to_start = time_to_start
        self.time_to_full_implementation = time_to_full_implementation

    def __repr__(self):
        retval = '<target = {:g}'.format(self.target)
        if self.target > 0:
            retval += (', time_to_start = {:g}'.format(self.time_to_start)
                       + ', time_to_full_implementation = {:g}'.format(
                           self.time_to_full_implementation))
        retval += '>'
        return retval


class Targets(container.Container):
    '''n
    Target values over time.

    From the initial proportions read from
    :attr:`model.datasheet.Parameters.initial_conditions`,
    the target values go linearly from the initial proportions to `targets`
    in `time_to_full_implementation` years, then stay constant at
    `targets` after that.

    `targets` can be a 3-tuple of levels for diagnosis, treatment,
    and viral suppression, or it can be one of the following
    strings:

    * ``'909090'``: 90–90–90 with no vaccine.
      Set levels to 90% in 5 years.  If a current level
      is above 90%, keep it there instead.
    * ``'baseline'``: Keep the current levels constant going forward.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed', 'vaccinated')

    def __init__(self, targets,
                 vaccine_target = Target(0, 0, 0),
                 times_to_start = 0,
                 times_to_full_implementation = 5):
        self.targets = targets
        self.vaccine_target = vaccine_target

        # Append vaccine to times_to_start.
        if numpy.isscalar(times_to_start):
            times_to_start *= numpy.ones(len(self._keys) - 1)
        else:
            times_to_start = numpy.asarray(times_to_start)
        times_to_start = numpy.hstack((times_to_start,
                                       vaccine_target.time_to_start))

        # Append vaccine to times_to_full_implementation.
        if numpy.isscalar(times_to_full_implementation):
            times_to_full_implementation *= numpy.ones(len(self._keys) - 1)
        else:
            times_to_full_implementation = numpy.asarray(
                times_to_full_implementation)
        times_to_full_implementation = numpy.hstack((
            times_to_full_implementation,
            vaccine_target.time_to_full_implementation))

        # Use names.
        self.times_to_start = numpy.rec.fromarrays(
            times_to_start,
            names = ','.join(self._keys))
        self.times_to_full_implementation = numpy.rec.fromarrays(
            times_to_full_implementation,
            names = ','.join(self._keys))

    def __call__(self, parameters, t):
        return TargetValues(self.targets, self.vaccine_target,
                            self.times_to_start,
                            self.times_to_full_implementation,
                            parameters, t)


class TargetValues(container.Container):
    '''
    Target values over time.
    '''
    _keys = Targets._keys

    def __init__(self, targets, vaccine_target,
                 times_to_start, times_to_full_implementation,
                 parameters, t):
        self.parameters = parameters
        self.t = t
        
        initial_proportions = proportions.Proportions(
            self.parameters.initial_conditions)

        # Convert special strings to numerical values.
        if isinstance(targets, str):
            if targets == '909090':
                # Max of 90% and current the current level.
                targets = [numpy.clip(v, 0.9, None)
                           for v in initial_proportions.values()]
                targets = targets[: len(self._keys) - 1]
            elif targets == 'baseline':
                # Fixed at initial values.
                targets = list(initial_proportions.values())
                targets = targets[: len(self._keys) - 1]
            else:
                raise ValueError("Unknown targets '{}'!".format(targets))

        targets = numpy.hstack((targets, vaccine_target.target))
        # Use names for entries.
        targets = numpy.rec.fromarrays(targets,
                                       names = ','.join(self._keys))

        for k in self.keys():
            initial_proportion = getattr(initial_proportions, k)
            target = getattr(targets, k)
            time_to_start = getattr(times_to_start, k)
            time_to_full_implementation = getattr(times_to_full_implementation,
                                                  k)
            amount_implemented = numpy.where(
                t < time_to_start, 0,
                numpy.where(t - time_to_start < time_to_full_implementation,
                            (t - time_to_start) / time_to_full_implementation,
                            1))

            v = (initial_proportion
                 + (target - initial_proportion) * amount_implemented)
            setattr(self, k, v)

    def control_rates(self, state):
        return control_rates.ControlRates(self.t, state, self, self.parameters) 
