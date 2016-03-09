'''
Solve the HIV model.
'''

import numpy
from scipy import integrate

from . import control_rates
from . import proportions


def _ODEs(state, t, targs, parameters):
    # S is susceptible.
    # A is acute infection.
    # U is undiagnosed.
    # D is diagnosed but not treated.
    # T is treated but not viral suppressed.
    # V is viral suppressed.
    # W is AIDS.
    # Z is dead from AIDS.
    S, A, U, D, T, V, W, Z = state

    # Total sexually active population.
    N = S + A + U + D + T + V

    controls = control_rates.get_control_rates(t, state, targs, parameters)

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

    dZ = parameters.death_rate_AIDS * W

    return (dS, dA, dU, dD, dT, dV, dW, dZ)


def _ODEs_log(state_log, t, targs, parameters):
    state = numpy.exp(state_log)
    # S is susceptible.
    # A is acute infection.
    # U is undiagnosed.
    # D is diagnosed but not treated.
    # T is treated but not viral suppressed.
    # V is viral suppressed.
    # W is AIDS.
    # Z is dead from AIDS.
    S, A, U, D, T, V, W, Z = numpy.exp(state_log)
    S_log, A_log, U_log, D_log, T_log, V_log, W_log, Z_log = state_log

    # Total sexually active population.
    N = S + A + U + D + T + V
    N_log = numpy.log(N)

    controls = control_rates.get_control_rates(t, state, targs, parameters)

    force_of_infection = (
        (parameters.transmission_rate_acute
         * numpy.exp(A_log - N_log))
        + (parameters.transmission_rate_unsuppressed
           * (numpy.exp(U_log - N_log)
              + numpy.exp(D_log - N_log)
              + numpy.exp(T_log - N_log)))
        + (parameters.transmission_rate_suppressed
           * numpy.exp(V_log - N_log)))

    dS_log = (parameters.birth_rate * N * numpy.exp(- S_log)
              - force_of_infection
              - parameters.death_rate)

    dA_log = (force_of_infection * numpy.exp(S_log - A_log)
              - parameters.progression_rate_acute
              - parameters.death_rate)

    dU_log = (parameters.progression_rate_acute * numpy.exp(A_log - U_log)
              - controls[0]
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dD_log = (controls[0] * numpy.exp(U_log - D_log)
              + controls[2] * (numpy.exp(T_log - D_log)
                               + numpy.exp(V_log - D_log))
              - controls[1]
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dT_log = (controls[1] * numpy.exp(D_log - T_log)
              - controls[2]
              - parameters.suppression_rate
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dV_log = (parameters.suppression_rate * numpy.exp(T_log - V_log)
              - controls[2]
              - parameters.death_rate
              - parameters.progression_rate_suppressed)

    dW_log = (
        parameters.progression_rate_unsuppressed * (numpy.exp(U_log - W_log)
                                                    + numpy.exp(D_log - W_log)
                                                    + numpy.exp(T_log - W_log))
        + parameters.progression_rate_suppressed * numpy.exp(V_log - W_log)
        - parameters.death_rate_AIDS)

    dZ_log = parameters.death_rate_AIDS * numpy.exp(W_log - Z_log)

    return (dS_log, dA_log, dU_log, dD_log, dT_log, dV_log, dW_log, dZ_log)


def solve(targs, parameters, t_end = 10, use_log = True):
    t = numpy.linspace(0, t_end, 1001)

    if use_log:
        # Take log, but map 0 to e^-20.
        Y0 = numpy.ma.log(parameters.initial_conditions).filled(-20)
        fcn = _ODEs_log
    else:
        Y0 = parameters.initial_conditions.copy()
        fcn = _ODEs
        
    Y = integrate.odeint(fcn,
                         Y0,
                         t,
                         args = (targs, parameters),
                         mxstep = 1000)

    if use_log:
        state = numpy.exp(Y)
    else:
        state = Y

    return (t, state)


def split_state(state):
    return map(numpy.squeeze, numpy.hsplit(state, state.shape[-1]))
