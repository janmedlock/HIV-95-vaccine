'''
Get the current target values for diagnosis, treatment, viral suppression,
and vaccination from the overall target goals.
'''

import numpy

from . import container
from . import control_rates
from . import proportions


class TargetZero:
    '''
    Fixed at 0.
    '''
    def __call__(self, initial_proportion, t):
        return numpy.zeros_like(t, dtype = float)


class TargetStatusQuo:
    '''
    Fixed at the initial proportion.
    '''
    def __call__(self, initial_proportion, t):
        return initial_proportion * numpy.ones_like(t, dtype = float)


class TargetLinear:
    '''
    Linearly go from the initial proportion to
    max(target_value, initial_proportion) between time_to_start and
    time_to_target.  Stay fixed at initial proportion before
    time_to_start and fixed at target_value after time_to_target.
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

class Target90(TargetLinear):
    '''
    Linearly go from the initial proportion to the target value =
    max(90%, initial_proportion) between 2015 and
    2020.  Stay fixed at initial proportion before
    2015 and fixed at the target value after 2020.
    '''
    target_value = 0.9
    time_to_start = 2015
    time_to_target = 2020

    def __init__(self):
        pass


class Target95:
    '''
    Linearly go from the initial proportion to
    target_value_0 = max(90%, initial_proportion) between 2015 and
    2020, then linearly go to
    target_value_1 = max(95%, initial_proportion) between 2020 and 2030.
    Stay fixed at initial proportion before 2015 and fixed at
    target_value_1 after 2030.
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


class Targets(container.Container):
    '''
    Base type for targets for diagnosis, treatment, viral suppression,
    and vaccination.
    '''
    _keys = ('diagnosed', 'treated', 'suppressed', 'vaccinated')

    vaccine_efficacy = 0

    def __call__(self, parameters, t):
        return _TargetValues(self, parameters, t)

    @classmethod
    def __str__(cls):
        return cls.__name__

    def __repr__(self):
        return '{}.{}()'.format(self.__class__.__module__,
                                self.__class__.__name__)


class _TargetValues(container.Container):
    '''
    Hold numerical values for the targets at different points in time.
    '''
    _keys = Targets._keys

    def __init__(self, targets, parameters, t):
        self.t = numpy.asarray(t)
        self.parameters = parameters
        initial_proportions = proportions.Proportions(
            self.parameters.initial_conditions)
        for k in self.keys():
            target = getattr(targets, k)
            ip = getattr(initial_proportions, k)
            setattr(self, k, target(ip, self.t))

    def control_rates(self, state):
        '''
        Get the control rates given the current state.
        '''
        return control_rates.ControlRates(self.t, state, self, self.parameters)


class Zero(Targets):
    '''
    All zero.
    '''
    diagnosed = TargetZero()
    treated = TargetZero()
    suppressed = TargetZero()
    vaccinated = TargetZero()

    @staticmethod
    def __str__():
        return 'All Zeroes'


class StatusQuo(Targets):
    '''
    Fixed at the initial proportion with no vaccination.
    '''
    diagnosed = TargetStatusQuo()
    treated = TargetStatusQuo()
    suppressed = TargetStatusQuo()
    vaccinated = TargetZero()

    @staticmethod
    def __str__():
        return 'Status Quo'


class UNAIDS90(Targets):
    '''
    90-90-90 targets with no vaccination.
    '''
    diagnosed = Target90()
    treated = Target90()
    suppressed = Target90()
    vaccinated = TargetZero()

    @staticmethod
    def __str__():
        return '90–90–90'


class UNAIDS95(Targets):
    '''
    95-95-95 targets with no vaccination.
    '''
    diagnosed = Target95()
    treated = Target95()
    suppressed = Target95()
    vaccinated = TargetZero()

    @staticmethod
    def __str__():
        return '95–95–95'


class Vaccine(Targets):
    '''
    Vaccine plus the treatment targets in `treatment_targets`.
    '''
    def __init__(self,
                 efficacy = 0.5,
                 coverage = 0.7,
                 time_to_start = 2020,
                 time_to_fifty_percent = 2,
                 treatment_targets = UNAIDS95):
        self._efficacy = efficacy
        self._coverage = coverage
        self._time_to_start = time_to_start
        self._time_to_fifty_percent = time_to_fifty_percent
        self._treatment_targets = treatment_targets

        self.diagnosed = self._treatment_targets.diagnosed
        self.treated = self._treatment_targets.treated
        self.suppressed = self._treatment_targets.suppressed

        # Set vaccine efficacy
        self.vaccine_efficacy = self._efficacy

        time_to_target = (self._coverage / 0.5 * self._time_to_fifty_percent
                          + self._time_to_start)
        self.vaccinated = TargetLinear(self._coverage,
                                       self._time_to_start,
                                       time_to_target)
        self.vaccinated.time_to_fifty_percent = self._time_to_fifty_percent

    def __repr__(self):
        if isinstance(self._treatment_targets, Targets):
            treatment_str = repr(self._treatment_targets)
        elif issubclass(self._treatment_targets, Targets):
            treatment_str = '{}.{}'.format(self._treatment_targets.__module__,
                                           self._treatment_targets.__name__)
        else:
            raise ValueError

        params = [
            'efficacy={}'.format(self._efficacy),
            'coverage={}'.format(self._coverage),
            'time_to_start={}'.format(self._time_to_start),
            'time_to_fifty_percent={}'.format(self._time_to_fifty_percent),
            'treatment_targets={}'.format(treatment_str)]

        return '{}.{}({})'.format(self.__class__.__module__,
                                  self.__class__.__name__,
                                  ', '.join(params))

    def __str__(self):
        if isinstance(self._treatment_targets, Targets):
            treatment_str = str(self._treatment_targets)
        elif issubclass(self._treatment_targets, Targets):
            treatment_str = self._treatment_targets.__str__()
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
_baseline = [StatusQuo(),
             UNAIDS90(),
             UNAIDS95()]
all_ = []
for target in _baseline:
    all_.extend([target,
                 Vaccine(treatment_targets = target)])


vaccine_sensitivity_all = [Vaccine(),
                           Vaccine(efficacy = 0.3),
                           Vaccine(efficacy = 0.7),
                           Vaccine(coverage = 0.5),
                           Vaccine(coverage = 0.9),
                           Vaccine(time_to_start = 2025),
                           Vaccine(time_to_fifty_percent = 5)]
