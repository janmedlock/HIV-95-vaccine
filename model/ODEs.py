'''
ODEs representing the HIV model.
'''

import warnings

import numpy
from scipy import integrate
import pandas

from . import control_rates


variables = (
    'susceptible',        # S
    'vaccinated',         # Q
    'acute',              # A
    'undiagnosed',        # U
    'diagnosed',          # D
    'treated',            # T
    'viral_suppression',  # V
    'AIDS',               # W
    'dead',               # Z
    'new_infections',     # R
)

alive = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
         'diagnosed', 'treated', 'viral_suppression', 'AIDS')

infected = ('acute', 'undiagnosed', 'diagnosed', 'treated',
            'viral_suppression', 'AIDS')


def get_variable(state, name):
    i = variables.index(name)
    return state[..., i]


def get_alive(state):
    return sum(get_variable(state, k) for k in alive)


def get_infected(state):
    return sum(get_variable(state, k) for k in infected)


# Variables to log transform: S, U, D, T, V, W
vars_log = [0, 3, 4, 5, 6, 7]
# Variables to not log transform: Q, A, Z, R
vars_nonlog = [1, 2, 8, 9]


def transform(state, _log0 = -20):
    '''
    Log transform some of the state variables.
    '''
    state_trans = numpy.empty(numpy.shape(state))
    state_trans[..., vars_log] = numpy.ma.log(state[..., vars_log]).filled(
        _log0)
    state_trans[..., vars_nonlog] = state[..., vars_nonlog]
    return state_trans


def transform_inv(state_trans):
    '''
    Inverse log transform some of the state variables.
    '''
    state = numpy.empty(numpy.shape(state_trans))
    state[..., vars_log] = numpy.exp(state_trans[..., vars_log])
    state[..., vars_nonlog] = state_trans[..., vars_nonlog]
    return state


def split_state(state):
    if isinstance(state, (pandas.Series, pandas.DataFrame)):
        state = state.values
    return map(numpy.squeeze, numpy.split(state, state.shape[-1], -1))


def rhs(t, state, target, parameters):
    # Force the state variables to be non-negative.
    # The last two state variables, dead from AIDS and new infections,
    # are cumulative numbers that are set to 0 at t = 0: these
    # can be negative if time goes backwards.
    state[ : -2] = state[ : - 2].clip(0, numpy.inf)

    S, Q, A, U, D, T, V, W, Z, R = state

    # Total sexually active population.
    N = S + Q + A + U + D + T + V

    control_rates_ =  control_rates.get(t, state, target, parameters)

    force_of_infection = (
        parameters.transmission_rate_acute * A
        + parameters.transmission_rate_unsuppressed * (U + D + T)
        + parameters.transmission_rate_suppressed * V) / N

    dS = (parameters.birth_rate * N
          - control_rates_.vaccination * S
          - force_of_infection * S
          - parameters.death_rate * S)

    dQ = (control_rates_.vaccination * S
          - (1 - target.vaccine_efficacy) * force_of_infection * Q
          - parameters.death_rate * Q)

    dA = (force_of_infection * S
          + (1 - target.vaccine_efficacy) * force_of_infection * Q
          - parameters.progression_rate_acute * A
          - parameters.death_rate * A)

    dU = (parameters.progression_rate_acute * A
          - control_rates_.diagnosis * U
          - parameters.death_rate * U
          - parameters.progression_rate_unsuppressed * U)

    dD = (control_rates_.diagnosis * U
          + control_rates_.nonadherence * (T + V)
          - control_rates_.treatment * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (control_rates_.treatment * D
          - control_rates_.nonadherence * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - control_rates_.nonadherence * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    dZ = parameters.death_rate_AIDS * W

    dR = (force_of_infection * S
          + (1 - target.vaccine_efficacy) * force_of_infection * Q)

    return [dS, dQ, dA, dU, dD, dT, dV, dW, dZ, dR]


def rhs_log(t, state_trans, target, parameters):
    state = transform_inv(state_trans)
    S, Q, A, U, D, T, V, W, Z, R = state
    (S_log, U_log, D_log, T_log, V_log, W_log) = state_trans[vars_log]

    # Total sexually active population.
    N = S + Q + A + U + D + T + V
    N_log = numpy.log(N)

    control_rates_ =  control_rates.get(t, state, target, parameters)

    force_of_infection = (
        parameters.transmission_rate_acute * A / N
        + (parameters.transmission_rate_unsuppressed
           * (numpy.exp(U_log - N_log)
              + numpy.exp(D_log - N_log)
              + numpy.exp(T_log - N_log)))
        + parameters.transmission_rate_suppressed * numpy.exp(V_log - N_log))

    dS_log = (parameters.birth_rate * numpy.exp(N_log - S_log)
              - control_rates_.vaccination
              - force_of_infection
              - parameters.death_rate)

    dQ = (control_rates_.vaccination * numpy.exp(S_log)
          - (1 - target.vaccine_efficacy) * force_of_infection * Q
          - parameters.death_rate * Q)

    dA = (force_of_infection * numpy.exp(S_log)
          + (1 - target.vaccine_efficacy) * force_of_infection * Q
          - parameters.progression_rate_acute * A
          - parameters.death_rate * A)

    dU_log = (parameters.progression_rate_acute * A * numpy.exp(- U_log)
              - control_rates_.diagnosis
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dD_log = (control_rates_.diagnosis * numpy.exp(U_log - D_log)
              + control_rates_.nonadherence * (numpy.exp(T_log - D_log)
                                               + numpy.exp(V_log - D_log))
              - control_rates_.treatment
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dT_log = (control_rates_.treatment * numpy.exp(D_log - T_log)
              - control_rates_.nonadherence
              - parameters.suppression_rate
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dV_log = (parameters.suppression_rate * numpy.exp(T_log - V_log)
              - control_rates_.nonadherence
              - parameters.death_rate
              - parameters.progression_rate_suppressed)

    dW_log = (
        parameters.progression_rate_unsuppressed * (numpy.exp(U_log - W_log)
                                                    + numpy.exp(D_log - W_log)
                                                    + numpy.exp(T_log - W_log))
        + parameters.progression_rate_suppressed * numpy.exp(V_log - W_log)
        - parameters.death_rate_AIDS)

    dZ = parameters.death_rate_AIDS * numpy.exp(W_log)

    dR = (force_of_infection * numpy.exp(S_log)
          + (1 - target.vaccine_efficacy) * force_of_infection * Q)

    dstate = [dS_log, dQ, dA, dU_log, dD_log, dT_log, dV_log, dW_log, dZ, dR]
    return dstate


def _solve_odeint(t, target, parameters, Y0, fcn):
    def fcn_swap_Yt(Y, t, target, parameters):
        return fcn(t, Y, target, parameters)
    return integrate.odeint(fcn_swap_Yt, Y0, t,
                            args = (target, parameters),
                            mxstep = 2000,
                            mxhnil = 1)


def _solve_ode(t, target, parameters, Y0, fcn, integrator):
    solver = integrate.ode(fcn)
    if integrator == 'lsoda':
        kwds = dict(max_hnil = 1)
    else:
        kwds = {}
    solver.set_integrator(integrator,
                          nsteps = 2000,
                          **kwds)
    solver.set_f_params(target, parameters)
    solver.set_initial_value(Y0, t[0])
    Y = numpy.empty((len(t), len(Y0)))
    Y[0] = Y0
    for i in range(1, len(t)):
        Y[i] = solver.integrate(t[i])
        if not use_log:
            # Force to be non-negative.
            Y[i, : -2] = Y[i, : -2].clip(0, numpy.inf)
            solver.set_initial_value(Y[i], t[i])
        assert solver.successful()
    return Y


def solve(t, target, parameters,
          integrator = 'odeint', use_log = True):
    '''
    `integrator` is a
    :class:`scipy.integrate.ode` integrator---``'lsoda'``,
    ``'vode'``, ``'dopri5'``, ``'dop853'``---or
    ``'odeint'`` to use :func:`scipy.integrate.odeint`.
    '''

    assert numpy.isfinite(parameters.R0)
    assert not numpy.all(parameters.initial_conditions == 0)

    Y0 = parameters.initial_conditions.copy().values
    if use_log:
        Y0 = transform(Y0)
        fcn = rhs_log
    else:
        fcn = rhs

    # Scale time to start at 0 to avoid some solver warnings.
    t_scaled = t - t[0]
    def fcn_scaled(t_scaled, Y, target, parameters):
        return fcn(t_scaled + t[0], Y, target, parameters)

    if integrator == 'odeint':
        Y = _solve_odeint(t_scaled, target, parameters, Y0, fcn_scaled)
    else:
        Y = _solve_ode(t_scaled, target, parameters, Y0, fcn_scaled)

    if numpy.any(numpy.isnan(Y)):
        msg = ("country = '{}': NaN in solution!").format(parameters.country)
        if use_log:
            msg += "  Re-running with use_log = False."
            warnings.warn(msg)
            return solve(t, target, parameters,
                         integrator = integrator,
                         use_log = False)
        else:
            raise ValueError(msg)
    elif use_log:
        return transform_inv(Y)
    else:
        return Y
