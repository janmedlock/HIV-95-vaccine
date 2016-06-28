'''
ODEs representing the HIV model.
'''

import numpy

from . import simulation


# S is susceptible.
# Q is vaccinated.
# A is acute infection.
# U is undiagnosed.
# D is diagnosed but not treated.
# T is treated but not viral suppressed.
# V is viral suppressed.
# W is AIDS.
# Z is dead from AIDS.
# R is new infectons.

# Variables to log transform: S, U, D, T, V, W
vars_log = [0, 3, 4, 5, 6, 7]
# Variables to not log transform: Q, A, Z, R
vars_nonlog = [1, 2, 8, 9]

def transform(state):
    '''
    Log transform some of the state variables.
    '''
    state_trans = numpy.empty(numpy.shape(state))
    state_trans[..., vars_log] = numpy.log(state[..., vars_log])
    state_trans[..., vars_nonlog] = state[..., vars_nonlog]
    return state_trans

def transform_inv(state_trans):
    '''
    Inverse log transform all the state variables.
    '''
    state = numpy.empty(numpy.shape(state_trans))
    state[..., vars_log] = numpy.exp(state_trans[..., vars_log])
    state[..., vars_nonlog] = state_trans[..., vars_nonlog]
    return state


def split_state(state):
    return map(numpy.squeeze, numpy.hsplit(state, state.shape[-1]))


def ODEs(t, state, targets_, parameters):
    # Force the state variables to be non-negative.
    # The last two state variables, dead from AIDS and new infections,
    # are cumulative numbers that are set to 0 at t = 0: these
    # can be negative if time goes backwards.
    state[ : -2] = state[ : - 2].clip(0, numpy.inf)

    S, Q, A, U, D, T, V, W, Z, R = state

    # Total sexually active population.
    N = S + Q + A + U + D + T + V

    control_rates = targets_(parameters, t).control_rates(state)

    force_of_infection = (
        parameters.transmission_rate_acute * A
        + parameters.transmission_rate_unsuppressed * (U + D + T)
        + parameters.transmission_rate_suppressed * V) / N

    dS = (parameters.birth_rate * N
          - control_rates.vaccination * S
          - force_of_infection * S
          - parameters.death_rate * S)

    dQ = (control_rates.vaccination * S
          - (1 - parameters.vaccine_efficacy) * force_of_infection * Q
          - parameters.death_rate * Q)
    
    dA = (force_of_infection * S
          + (1 - parameters.vaccine_efficacy) * force_of_infection * Q
          - parameters.progression_rate_acute * A
          - parameters.death_rate * A)

    dU = (parameters.progression_rate_acute * A
          - control_rates.diagnosis * U
          - parameters.death_rate * U
          - parameters.progression_rate_unsuppressed * U)

    dD = (control_rates.diagnosis * U
          + control_rates.nonadherence * (T + V)
          - control_rates.treatment * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (control_rates.treatment * D
          - control_rates.nonadherence * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - control_rates.nonadherence * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    dZ = parameters.death_rate_AIDS * W

    dR = force_of_infection * S

    return [dS, dQ, dA, dU, dD, dT, dV, dW, dZ, dR]


def ODEs_log(t, state_log, targets_, parameters):
    state = transform_inv(state_log)
    S, Q, A, U, D, T, V, W, Z, R = state
    (S_log, U_log, D_log, T_log, V_log, W_log) = state_log[vars_log]

    # Total sexually active population.
    N = S + Q + A + U + D + T + V
    N_log = numpy.log(N)

    control_rates = targets_(parameters, t).control_rates(state)

    force_of_infection = (
        parameters.transmission_rate_acute * A / N
        + (parameters.transmission_rate_unsuppressed
           * (numpy.exp(U_log - N_log)
              + numpy.exp(D_log - N_log)
              + numpy.exp(T_log - N_log)))
        + parameters.transmission_rate_suppressed * numpy.exp(V_log - N_log))

    dS_log = (parameters.birth_rate * N * numpy.exp(- S_log)
              - control_rates.vaccination
              - force_of_infection
              - parameters.death_rate)

    dQ = (control_rates.vaccination * numpy.exp(S_log)
          - (1 - parameters.vaccine_efficacy) * force_of_infection * Q
          - parameters.death_rate * Q)

    dA = (force_of_infection * numpy.exp(S_log)
          + (1 - parameters.vaccine_efficacy) * force_of_infection * Q
          - parameters.progression_rate_acute * A
          - parameters.death_rate * A)

    dU_log = (parameters.progression_rate_acute * A * numpy.exp(- U_log)
              - control_rates.diagnosis
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dD_log = (control_rates.diagnosis * numpy.exp(U_log - D_log)
              + control_rates.nonadherence * (numpy.exp(T_log - D_log)
                                              + numpy.exp(V_log - D_log))
              - control_rates.treatment
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dT_log = (control_rates.treatment * numpy.exp(D_log - T_log)
              - control_rates.nonadherence
              - parameters.suppression_rate
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dV_log = (parameters.suppression_rate * numpy.exp(T_log - V_log)
              - control_rates.nonadherence
              - parameters.death_rate
              - parameters.progression_rate_suppressed)

    dW_log = (
        parameters.progression_rate_unsuppressed * (numpy.exp(U_log - W_log)
                                                    + numpy.exp(D_log - W_log)
                                                    + numpy.exp(T_log - W_log))
        + parameters.progression_rate_suppressed * numpy.exp(V_log - W_log)
        - parameters.death_rate_AIDS)

    dZ = parameters.death_rate_AIDS * W

    dR = force_of_infection * S

    return [dS_log, dQ, dA, dU_log, dD_log, dT_log, dV_log, dW_log, dZ, dR]
