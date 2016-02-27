import numpy
from scipy import integrate

from . import target_functions
from . import control_rates
from . import proportions


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

    controls = control_rates.get_control_rates(t, variables, target_funcs)

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
          - controls[0] * U
          - parameters.death_rate * U
          - parameters.progression_rate_unsuppressed * U)

    dD = (controls[0] * U
          + controls[2] * (T + V)
          - controls[1] * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (controls[1] * D
          - controls[2] * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - controls[2] * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    return (dS, dA, dU, dD, dT, dV, dW)


def solve(target_values, parameters):
    target_funcs = target_functions.get_target_funcs(target_values, parameters)

    t = numpy.linspace(0, t_end, 1001)

    state = integrate.odeint(ODE_RHS,
                             parameters.initial_conditions.copy(),
                             t,
                             args = (parameters, target_funcs),
                             mxstep = 1000)

    return (t, state, target_funcs)


def split_state(state):
    return map(numpy.squeeze, numpy.hsplit(state, state.shape[-1]))
