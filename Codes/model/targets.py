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

    From the initial proportions read from
    :attr:`model.datasheet.Parameters.initial_conditions`,
    the target values go linearly from the initial proportions to `targets`
    in `time_to_full_implementation` years, then stay constant at
    `targets` after that.

    `targets` can be a 4-tuple of levels for diagnosis, treatment,
    viral suppression, and vaccination, or it can be one of the following
    strings:

    * ``'909090'``: 90–90–90 with no vaccine.
      Set (non-vaccination) levels to 90% in 5 years.  If a current level
      is above 90%, keep it there instead.
    * ``'909090+50-5'``: 90-90-90 with vaccination starting at 5 years
      and increasing to 50% at 10 years.
    * ``'909090+50-10'``: 90-90-90 with vaccination starting at 10 years
      and increasing to 50% at 15 years.
    * ``'baseline'``: Keep the current levels constant going forward.
    * ``'baseline+50-5'``: baseline with vaccination starting at 5 years
      and increasing to 50% at 10 years.
    * ``'baseline+50-10'``: baseline with vaccination starting at 10 years
      and increasing to 50% at 15 years.
    * ``'nothing'``: Set all levels to 0.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed', 'vaccinated')

    def __init__(self, t, targets, parameters,
                 times_to_start = 0,
                 times_to_full_implementation = 5):
        initial_proportions = proportions.Proportions(
            parameters.initial_conditions)

        if numpy.isscalar(times_to_start):
            times_to_start *= numpy.ones(len(self._keys))
        else:
            times_to_start = numpy.asarray(times_to_start)

        if numpy.isscalar(times_to_full_implementation):
            times_to_full_implementation *= numpy.ones(len(self._keys))
        else:
            times_to_full_implementation = numpy.asarray(
                times_to_full_implementation)

        # Convert special strings to numerical values.
        if isinstance(targets, str):
            if targets.startswith('909090'):
                targets_ = targets
                # Max of 90% and current the current level.
                targets = [numpy.clip(v, 0.9, None)
                           for v in initial_proportions.values()]
                if targets_ == '909090':
                    # vaccination is 0.
                    targets[-1] = 0
                elif targets_ == '909090+50-5':
                    # vaccination is 50%.
                    targets[-1] = 0.5
                    # 5 years
                    times_to_start[-1] = 5
                elif targets_ == '909090+50-10':
                    # vaccination is 50%.
                    targets[-1] = 0.5
                    # 10 years
                    times_to_start[-1] = 10
            elif targets.startswith('baseline'):
                targets_ = targets
                # Fixed at initial values.
                targets = initial_proportions.values()
                if targets_ == 'baseline':
                    # vaccination is 0.
                    targets[-1] = 0
                elif targets_ == 'baseline+50-5':
                    # vaccination is 50%.
                    targets[-1] = 0.5
                    # 5 years
                    times_to_start[-1] = 5
                elif targets_ == 'baseline+50-10':
                    # vaccination is 50%.
                    targets[-1] = 0.5
                    # 10 years
                    times_to_start[-1] = 10
            elif targets == 'nothing':
                targets = numpy.zeros(len(self._keys))

        # Use names for entries.
        targets = numpy.rec.fromarrays(targets,
                                       names = ','.join(self._keys))
        times_to_start = numpy.rec.fromarrays(times_to_start,
                                              names = ','.join(self._keys))
        times_to_full_implementation = numpy.rec.fromarrays(
            times_to_full_implementation,
            names = ','.join(self._keys))

        for k in self._keys:
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
