#!/usr/bin/python3

import numpy
from scipy import integrate
import functools
from matplotlib import pyplot

# Silence warnings from matplotlib trigged by seaborn
import warnings
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

import datasheet


t_end = 10


def ODE_RHS(variables, t, parameters, target_funcs):
    # S is susceptible.
    # A is acute infection.
    # U is undiagnosed.
    # D is diagnosed but not treated.
    # T is treated but not viral suppressed.
    # V is viral suppressed.
    # W is AIDS.
    S, A, U, D, T, V, W = variables

    # Total sexually active population.
    N = S + A + U + D + T + V

    control_rates = get_control_rates(t, variables, target_funcs)

    force_of_infection = (
        parameters.transmission_rate_acute * A
        + parameters.transmission_rate_unsuppressed * (U + D + T)
        + parameters.transmission_rate_suppressed * V) / N

    dS = (parameters.birth_rate * N
          - force_of_infection * S
          - parameters.death_rate * S)

    dA = (force_of_infection * S
          - parameters.progression_rate_acute * A
          - parameters.death_rate * A)

    dU = (parameters.progression_rate_acute * A
          - control_rates[0] * U
          - parameters.death_rate * U
          - parameters.progression_rate_unsuppressed * U)

    dD = (control_rates[0] * U
          + control_rates[2] * (T + V)
          - control_rates[1] * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (control_rates[1] * D
          - control_rates[2] * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - control_rates[2] * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    return (dS, dA, dU, dD, dT, dV, dW)


def get_proportions(state):
    S, A, U, D, T, V, W = map(numpy.squeeze, numpy.hsplit(state, 7))

    proportions = numpy.ma.empty((3, ) + state.shape[ : -1])

    # diagnosed
    # (D + T + V + W) / (A + U + D + T + V + W)
    proportions[0] = numpy.ma.divide(D + T + V + W, A + U + D + T + V + W)

    # treated
    # (T + V) / (D + T + V + W)
    proportions[1] = numpy.ma.divide(T + V, D + T + V + W)

    # suppressed
    # V / (T + V)
    proportions[2] = numpy.ma.divide(V, T + V)

    return proportions.filled(0)


def target_func(target_value, initial_proportion, time_to_full_implementation,
                t):
    '''
    From the initial value initial_proportion,
    target_func goes linearly from initial_proportion to target_value
    in time_to_full_implementation years, then stays constant at
    target_value after that.
    '''
    return (initial_proportion
            + ((target_value - initial_proportion)
               * numpy.clip(t, 0, time_to_full_implementation)
               / time_to_full_implementation))


def get_target_funcs(target_values, parameters,
                     time_to_full_implementation = 5):
    initial_proportions = get_proportions(parameters.initial_conditions)

    if isinstance(target_values, str):
        if target_values == '909090':
            # Max of 90% and current the current level.
            target_values = initial_proportions.clip(0.9, None)
        elif target_values == 'base':
            # Fixed at initial values.
            target_values = initial_proportions
        elif target_values == 'nothing':
            target_funcs = [lambda x: numpy.zeros_like(x)
                            for i in range(3)]
            return target_funcs

    target_funcs = [functools.partial(target_func, v, p,
                                      time_to_full_implementation)
                    for (v, p) in zip(target_values, initial_proportions)]

    return target_funcs


def ramp(x, tol = 0.0001):
    '''
    Piecewise linear:
           { 0        if x < 0
    f(x) = { x / tol  if 0 <= x <= tol
           { 1        if x > tol
    '''
    return numpy.clip(x / tol, 0, 1)


# diagnosis, treatment, nonadherance
control_rates_max = numpy.array([1, 10, 1])

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
    current_proportions = get_proportions(state)

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


def solve(target_values, parameters):
    target_funcs = get_target_funcs(target_values, parameters)

    t = numpy.linspace(0, t_end, 1001)

    state = integrate.odeint(ODE_RHS,
                             parameters.initial_conditions.copy(),
                             t,
                             args = (parameters, target_funcs),
                             mxstep = 1000)

    return (t, state, target_funcs)


# Find the coefficient that gives 80-20.
def f_80_20(a):
    return (4 * (numpy.exp(a * 0.8) - 1 - 0.8 * a)
            - (numpy.exp(a) - numpy.exp(0.8 * a) - 0.2 * a))
# res_80_20 = optimize.root(f_80_20, 8, tol = 1e-12)
# a_80_20 = numpy.asscalar(res_80_20.x)
a_80_20 = 8.000463231639765

def relative_cost_of_effort(p):
    '''
    Gives 80% of total cost in last 20%:
    4 * \int_0^{0.8} f(p) dp = \int_{0.8}^1 f(p) dp.

    Normalized so that the value at p = 0 is 0
    and the derivative at p = 0 is 1:
    f(0) = 0, f'(0) = 1.
    '''
    # return 1 / a_80_20 * (numpy.exp(a_80_20 * p) - 1)
    return numpy.ones_like(p)


def get_qalys_and_cost(t, state, target_funcs, parameters):
    qalys_rate = state @ (parameters.qaly_rates_per_person)
    qalys = integrate.simps(qalys_rate, t)

    control_rates = get_control_rates(t, state, target_funcs)
    target_func_values = numpy.column_stack(v(t) for v in target_funcs)
    relative_cost_of_control = relative_cost_of_effort(target_func_values)

    control_cost_rates_per_person = (
        (control_rates
         @ parameters.control_cost_per_transition_constant)
        + ((relative_cost_of_control * control_rates)
           @ parameters.control_cost_per_transition_increasing))

    state_cost_rates_per_person = (
        (relative_cost_of_control
         @ parameters.state_cost_rates_per_person_increasing)
        + parameters.state_cost_rates_per_person_constant)

    total_cost_rate = ((control_cost_rates_per_person
                        + state_cost_rates_per_person)
                       * state).sum(1)
    cost = integrate.simps(total_cost_rate, t)

    return qalys, cost


def solve_and_get_qalys_and_cost(target_values, parameters):
    t, state, target_funcs = solve(target_values, parameters)

    return get_qalys_and_cost(t, state, target_funcs, parameters)


def plot_solution(t, state, target_funcs, show = True):
    (fig, ax) = pyplot.subplots(2, 1)

    proportions = get_proportions(state)

    for (i, k) in enumerate(('diagnosed', 'treated', 'suppressed')):
        l = ax[0].plot(t, proportions[i], label = k.capitalize())
        ax[0].plot(t, target_funcs[i](t),
                   color = l[0].get_color(), linestyle = ':')
    ax[0].legend(loc = 'lower right')

    control_rates = get_control_rates(t, state, target_funcs)

    for (i, k) in enumerate(('diagnosis', 'treatment', 'nonadherance')):
        ax[1].plot(t, control_rates[:, i], label = '{} rate'.format(k))
    ax[1].legend(loc = 'upper right')


    (fig1, ax1) = pyplot.subplots()

    S, A, U, D, T, V, W = map(numpy.squeeze, numpy.hsplit(state, 7))

    ax1.semilogy(t, S, label = 'S')
    ax1.semilogy(t, A, label = 'A')
    ax1.semilogy(t, U, label = 'U')
    ax1.semilogy(t, D, label = 'D')
    ax1.semilogy(t, T, label = 'T')
    ax1.semilogy(t, V, label = 'V')
    ax1.semilogy(t, W, label = 'W')
    ax1.legend(loc = 'upper right')

    (fig2, ax2) = pyplot.subplots()

    N = state.sum(1)
    PLHI = N - S
    diagnosed = PLHI - A - U
    treated = diagnosed - D - W
    suppressed = treated - T
    ax2.plot(t, PLHI, label = 'PLHI')
    ax2.plot(t, diagnosed, label = 'diagnosed')
    ax2.plot(t, treated, label = 'treated')
    ax2.plot(t, suppressed, label = 'suppressed')
    ax2.legend(loc = 'upper right')

    if show:
        pyplot.show()


if __name__ == '__main__':
    country = 'Nigeria'

    print(country)

    parameters = datasheet.Parameters(country)

    t, state, target_funcs = solve('909090', parameters)

    qalys, cost = get_qalys_and_cost(t, state, target_funcs, parameters)

    qalys_base, cost_base = solve_and_get_qalys_and_cost('base', parameters)

    incremental_qalys = qalys - qalys_base
    incremental_cost = cost - cost_base
    ICER = incremental_cost / incremental_qalys

    print('incremental effectiveness = {:g} QALYs gained'.format(
        incremental_qalys))
    print('incremental cost = {:g} USD'.format(incremental_cost))
    print('incremental cost = {:g} GDP per capita'.format(
        incremental_cost / parameters.GDP_per_capita))
    print('ICER = {:g} USD per QALY averted'.format(ICER))
    print('ICER = {:g} x per capita GDP'.format(ICER
                                                / parameters.GDP_per_capita))

    plot_solution(t, state, target_funcs)
