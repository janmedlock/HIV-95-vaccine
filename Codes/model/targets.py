'''
Get the current target values for diagnosis, treatment, viral suppression,
and vaccination from the overall target goals.
'''

import numpy

from . import container
from . import control_rates
from . import proportions


def target_zero(self, initial_proportion, t):
    '''
    Fixed at 0.
    '''
    return numpy.zeros_like(t, dtype = float)


def target_status_quo(self, initial_proportion, t):
    '''
    Fixed at the initial proportion.
    '''
    return initial_proportion * numpy.ones_like(t, dtype = float)


def target_linear(target_value, time_to_start, time_to_target):
    '''
    Linearly go from the initial proportion to
    max(target_value, initial_proportion) between time_to_start and
    time_to_target.  Stay fixed at initial proportion before
    time_to_start and fixed at target_value after time_to_target.
    '''
    def f(self, initial_proportion, t):
        target_value_ = max(target_value, initial_proportion)
        amount_implemented = numpy.where(
            t < time_to_start, 0,
            numpy.where(
                t < time_to_target,
                (t - time_to_start) / (time_to_target - time_to_start),
                1))
        return (initial_proportion
                + (target_value_ - initial_proportion) * amount_implemented)
    return f


'''
Linearly go from the initial proportion to the target value =
max(90%, initial_proportion) between 2015 and
2020.  Stay fixed at initial proportion before
2015 and fixed at the target value after 2020.
'''
target90 = target_linear(0.9, 2015, 2020)


def target95(self, initial_proportion, t):
    '''
    Linearly go from the initial proportion to
    target_value_0 = max(90%, initial_proportion) between 2015 and
    2020, then linearly go to
    target_value_1 = max(95%, initial_proportion) between 2020 and 2030.
    Stay fixed at initial proportion before 2015 and fixed at
    target_value_1 after 2030.
    '''
    time_0 = 2015
    time_1 = 2020
    time_2 = 2030
    target_value_0 = max(0.9, initial_proportion)
    target_value_1 = max(0.95, initial_proportion)
    amount_implemented_0 = numpy.where(
        t < time_0, 0,
        numpy.where(
            t < time_1,
            (t - time_0) / (time_1 - time_0),
            1))
    amount_implemented_1 = numpy.where(
        t < time_1, 0,
        numpy.where(
            t < time_2,
            (t - time_1) / (time_2 - time_1),
            1))
    return (initial_proportion
            + (target_value_0 - initial_proportion) * amount_implemented_0
            + (target_value_1 - target_value_0) * amount_implemented_1)


class Targets(container.Container):
    '''
    Base type for targets for diagnosis, treatment, viral suppression,
    and vaccination.
    '''
    _keys = ('diagnosed', 'treated', 'suppressed', 'vaccinated')

    vaccine_efficacy = 0

    def __init__(self, parameters, t):
        self.parameters = parameters
        self.t = numpy.asarray(t)
        initial_proportions = proportions.Proportions(
            self.parameters.initial_conditions)
        for k in self.keys():
            target = getattr(self, '{}_target'.format(k))
            ip = getattr(initial_proportions, k)
            setattr(self, k, target(ip, self.t))

    def control_rates(self, state):
        '''
        Get the control rates given the current state.
        '''
        return control_rates.ControlRates(self.t, state, self, self.parameters) 


class TargetsZero(Targets):
    '''
    All zero.
    '''
    diagnosed_target = target_zero
    treated_target = target_zero
    suppressed_target = target_zero
    vaccinated_target = target_zero


class TargetsStatusQuo(Targets):
    '''
    Fixed at the initial proportion with no vaccination.
    '''
    diagnosed_target = target_status_quo
    treated_target = target_status_quo
    suppressed_target = target_status_quo
    vaccinated_target = target_zero


class Targets909090(Targets):
    '''
    90-90-90 targets with no vaccination.
    '''
    diagnosed_target = target90
    treated_target = target90
    suppressed_target = target90
    vaccinated_target = target_zero


class Targets959595(Targets):
    '''
    95-95-95 targets with no vaccination.
    '''
    diagnosed_target = target95
    treated_target = target95
    suppressed_target = target95
    vaccinated_target = target_zero


def TargetsVaccine(TargetsTreatment = Targets959595,
                   time_to_start = 2020,
                   time_to_fifty_percent = 2,
                   coverage = 0.7,
                   vaccine_efficacy_ = 0.7):
    '''
    Factory to set vaccine parameters.
    '''
    time_to_target = coverage / 0.5 * time_to_fifty_percent + time_to_start

    class TargetsVaccine_(TargetsTreatment):
        vaccine_efficacy = vaccine_efficacy_
        vaccinated_target = target_linear(coverage,
                                          time_to_start,
                                          time_to_target)

    return TargetsVaccine_
