import numpy

from . import proportions


# diagnosis, treatment, nonadherance
control_rates_max = numpy.array([1, 10, 1])


def ramp(x, tol = 0.0001):
    '''
    Piecewise linear:
           { 0        if x < 0
    f(x) = { x / tol  if 0 <= x <= tol
           { 1        if x > tol
    '''
    return numpy.clip(x / tol, 0, 1)


def get_control_rates(t, state, target_funcs):
    '''
    Rates for diagnosis, treatment, & nonadherance are piecewise constant.

    rates['diagnosis'] is:
    rates_max['diagnosis']
             if target_funcs['diagnosed'](t) > current_proprtions['diagnosed'],
    0                       otherwise

    rates['treatment'] is:
    rates_max['treatment']
                if target_funcs['treated'](t) > current_proportions['treated'],
    0                       otherwise.

    rates['nonadherance'] is:
    rates_max['nonadherance']
         if target_funcss['suppressed'](t) < current_proportions['suppressed'],
    0                    otherwise.

    OK, so we actually use a piecewise linear function ('ramp' below)
    that smooths the transition in a tiny region.
    '''
    current_proportions = proportions.get_proportions(state)

    control_rates = numpy.empty((3, ) + state.shape[ : -1], numpy.float64)

    # diagnosis
    control_rates[0] = (control_rates_max[0]
                        * ramp(target_funcs[0](t) - current_proportions[0]))

    # treatment
    control_rates[1] = (control_rates_max[1]
                        * ramp(target_funcs[1](t) - current_proportions[1]))

    # nonadherance
    control_rates[2] = (control_rates_max[2]
                        * ramp(current_proportions[2] - target_funcs[2](t)))

    return control_rates.T
