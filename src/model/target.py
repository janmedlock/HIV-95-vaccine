'''
Get the current target values for diagnosis, treatment, viral suppression,
and vaccination from the overall target goals.
'''

import numpy

from . import control_rates
from . import proportions
from . import simulation


class OneTargetZero:
    '''
    Fixed at 0.
    '''
    def __call__(self, initial_proportion, t):
        return numpy.zeros_like(t, dtype = float)


class OneTargetStatusQuo:
    '''
    Fixed at the `initial_proportion`.
    '''
    def __call__(self, initial_proportion, t):
        return initial_proportion * numpy.ones_like(t, dtype = float)


class OneTargetLinear:
    '''
    Linearly go from the `initial_proportion` to
    `max(target_value, initial_proportion)` between `time_to_start` and
    `time_to_target`.  Stay fixed at initial proportion before
    `time_to_start` and fixed at `target_value` after `time_to_target`.
    '''
    def __init__(self, target_value, time_to_start, time_to_target):
        self.target_value = target_value
        self.time_to_start = time_to_start
        self.time_to_target = time_to_target

    def __call__(self, initial_proportion, t):
        target_value_ = max(self.target_value, initial_proportion)
        amount_implemented = numpy.where(
            t < self.time_to_start, 0,
            numpy.where(
                t < self.time_to_target,
                (t - self.time_to_start)
                / (self.time_to_target - self.time_to_start),
                1))
        return (initial_proportion
                + (target_value_ - initial_proportion) * amount_implemented)


class OneTarget90(OneTargetLinear):
    '''
    Linearly go from the `initial_proportion` to the
    `target_value = max(90%, initial_proportion)` between 2015 and
    2020.  Stay fixed at `initial_proportion` before
    2015 and fixed at the `target_value` after 2020.
    '''
    target_value = 0.9
    time_to_start = 2015
    time_to_target = 2020

    def __init__(self):
        pass


class OneTarget95:
    '''
    Linearly go from the `initial_proportion` to
    `target_value_0 = max(90%, initial_proportion)` between 2015 and
    2020, then linearly go to
    `target_value_1 = max(95%, initial_proportion)` between 2020 and 2030.
    Stay fixed at `initial_proportion` before 2015 and fixed at
    `target_value_1` after 2030.
    '''
    target_value_0 = 0.9
    target_value_1 = 0.95
    time_0 = 2015
    time_1 = 2020
    time_2 = 2030

    def __call__(self, initial_proportion, t):
        target_value_0_ = max(self.target_value_0, initial_proportion)
        target_value_1_ = max(self.target_value_1, initial_proportion)
        amount_implemented_0 = numpy.where(
            t < self.time_0, 0,
            numpy.where(
                t < self.time_1,
                (t - self.time_0) / (self.time_1 - self.time_0),
                1))
        amount_implemented_1 = numpy.where(
            t < self.time_1, 0,
            numpy.where(
                t < self.time_2,
                (t - self.time_1) / (self.time_2 - self.time_1),
                1))
        return (initial_proportion
                + (target_value_0_ - initial_proportion) * amount_implemented_0
                + (target_value_1_ - target_value_0_) * amount_implemented_1)


class Target:
    '''
    Base type for target for diagnosis, treatment, viral suppression,
    and vaccination.
    '''

    diagnosed = None
    treated = None
    suppressed = None
    vaccinated = None

    vaccine_efficacy = 0

    def __call__(self, t, parameters):
        '''
        Get numerical values for the target at different points in time.
        '''
        t = numpy.asarray(t)
        initial_proportions = proportions.get(parameters.initial_conditions)
        names = initial_proportions.dtype.names
        arrays = []
        for n in names:
            targ = getattr(self, n)
            ip = getattr(initial_proportions, n)
            arrays.append(targ(ip, t))
        return numpy.rec.fromarrays(arrays, names = names)

    @classmethod
    def __str__(cls):
        return cls.__name__

    def __repr__(self):
        return '{}.{}()'.format(self.__class__.__module__,
                                self.__class__.__name__)


class Zero(Target):
    '''
    All zero.
    '''
    diagnosed = OneTargetZero()
    treated = OneTargetZero()
    suppressed = OneTargetZero()
    vaccinated = OneTargetZero()

    @staticmethod
    def __str__():
        return 'All Zeroes'


class StatusQuo(Target):
    '''
    Fixed at the initial proportion with no vaccination.
    '''
    diagnosed = OneTargetStatusQuo()
    treated = OneTargetStatusQuo()
    suppressed = OneTargetStatusQuo()
    vaccinated = OneTargetZero()

    @staticmethod
    def __str__():
        return 'Status Quo'


class UNAIDS90(Target):
    '''
    90--90--90 target with no vaccination.
    '''
    diagnosed = OneTarget90()
    treated = OneTarget90()
    suppressed = OneTarget90()
    vaccinated = OneTargetZero()

    @staticmethod
    def __str__():
        return '90–90–90'


class UNAIDS95(Target):
    '''
    95--95--95 target with no vaccination.
    '''
    diagnosed = OneTarget95()
    treated = OneTarget95()
    suppressed = OneTarget95()
    vaccinated = OneTargetZero()

    @staticmethod
    def __str__():
        return '95–95–95'


class Vaccine(Target):
    '''
    Vaccine plus the `treatment_target`.
    '''
    def __init__(self,
                 treatment_target = UNAIDS95,
                 efficacy = 0.5,
                 coverage = 0.7,
                 time_to_start = 2020,
                 time_to_fifty_percent = 2):
        self._efficacy = efficacy
        self._coverage = coverage
        self._time_to_start = time_to_start
        self._time_to_fifty_percent = time_to_fifty_percent
        self._treatment_target = treatment_target

        self.diagnosed = self._treatment_target.diagnosed
        self.treated = self._treatment_target.treated
        self.suppressed = self._treatment_target.suppressed

        # Set vaccine efficacy
        self.vaccine_efficacy = self._efficacy

        time_to_target = (self._coverage / 0.5 * self._time_to_fifty_percent
                          + self._time_to_start)
        self.vaccinated = OneTargetLinear(self._coverage,
                                          self._time_to_start,
                                          time_to_target)
        self.vaccinated.time_to_fifty_percent = self._time_to_fifty_percent

    def __repr__(self):
        if isinstance(self._treatment_target, Target):
            treatment_str = repr(self._treatment_target)
        elif issubclass(self._treatment_target, Target):
            treatment_str = '{}.{}'.format(self._treatment_target.__module__,
                                           self._treatment_target.__name__)
        else:
            raise ValueError

        params = [
            'efficacy={}'.format(self._efficacy),
            'coverage={}'.format(self._coverage),
            'time_to_start={}'.format(self._time_to_start),
            'time_to_fifty_percent={}'.format(self._time_to_fifty_percent),
            'treatment_target={}'.format(treatment_str)]

        return '{}.{}({})'.format(self.__class__.__module__,
                                  self.__class__.__name__,
                                  ', '.join(params))

    def __str__(self):
        if isinstance(self._treatment_target, Target):
            treatment_str = str(self._treatment_target)
        elif issubclass(self._treatment_target, Target):
            treatment_str = self._treatment_target.__str__()
        else:
            raise ValueError
            
        params = [
            'efficacy={:g}%'.format(100 * self._efficacy),
            'coverage={:g}%'.format(100 * self._coverage),
            'time_to_start={}'.format(self._time_to_start),
            'time_to_fifty_percent={}y'.format(self._time_to_fifty_percent)]

        return '{} + {}({})'.format(treatment_str,
                                    super().__str__(),
                                    ', '.join(params))


# Build each of these and each of these + vaccine.
all_baselines = [StatusQuo(),
             UNAIDS90(),
             UNAIDS95()]
all_ = []
for target in all_baselines:
    all_.extend([target,
                 Vaccine(treatment_target = target)])


vaccine_scenarios_baselines = [
    StatusQuo(),
    # UNAIDS90(),
    # UNAIDS95(),
]
vaccine_scenarios = []
for target in vaccine_scenarios_baselines:
    vaccine_scenarios.extend([
        target,
        Vaccine(treatment_target = target),
        Vaccine(treatment_target = target, efficacy = 0.3),
        Vaccine(treatment_target = target, efficacy = 0.7),
        Vaccine(treatment_target = target, coverage = 0.5),
        Vaccine(treatment_target = target, coverage = 0.9),
        Vaccine(treatment_target = target, time_to_start = 2025),
        Vaccine(treatment_target = target, time_to_fifty_percent = 5)])
