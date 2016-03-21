'''
Solve the HIV model.
'''

import copy
import numpy
from scipy import integrate

from . import container
from . import cost
from . import datasheet
from . import effectiveness
from . import net_benefit
from . import plot
from . import proportions
from . import targets


def _ODEs(state, t, targets_, parameters):
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
          + control_rates.nonadherance * (T + V)
          - control_rates.treatment * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (control_rates.treatment * D
          - control_rates.nonadherance * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - control_rates.nonadherance * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    dZ = parameters.death_rate_AIDS * W

    dR = force_of_infection * S

    return (dS, dQ, dA, dU, dD, dT, dV, dW, dZ, dR)


def _ODEs_log(state_log, t, targets_, parameters):
    state = numpy.exp(state_log)
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
    S, Q, A, U, D, T, V, W, Z, R = numpy.exp(state_log)
    (S_log, Q_log, A_log, U_log, D_log,
     T_log, V_log, W_log, Z_log, R_log) = state_log

    # Total sexually active population.
    N = S + Q + A + U + D + T + V
    N_log = numpy.log(N)

    control_rates = targets_(parameters, t).control_rates(state)

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
              - control_rates.vaccination
              - force_of_infection
              - parameters.death_rate)

    dQ_log = (control_rates.vaccination * numpy.exp(S_log - Q_log)
              - (1 - parameters.vaccine_efficacy) * force_of_infection
              - parameters.death_rate)

    dA_log = (force_of_infection * numpy.exp(S_log - A_log)
              + ((1 - parameters.vaccine_efficacy) * force_of_infection
                 * numpy.exp(Q_log - A_log))
              - parameters.progression_rate_acute
              - parameters.death_rate)

    dU_log = (parameters.progression_rate_acute * numpy.exp(A_log - U_log)
              - control_rates.diagnosis
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dD_log = (control_rates.diagnosis * numpy.exp(U_log - D_log)
              + control_rates.nonadherance * (numpy.exp(T_log - D_log)
                                              + numpy.exp(V_log - D_log))
              - control_rates.treatment
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dT_log = (control_rates.treatment * numpy.exp(D_log - T_log)
              - control_rates.nonadherance
              - parameters.suppression_rate
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dV_log = (parameters.suppression_rate * numpy.exp(T_log - V_log)
              - control_rates.nonadherance
              - parameters.death_rate
              - parameters.progression_rate_suppressed)

    dW_log = (
        parameters.progression_rate_unsuppressed * (numpy.exp(U_log - W_log)
                                                    + numpy.exp(D_log - W_log)
                                                    + numpy.exp(T_log - W_log))
        + parameters.progression_rate_suppressed * numpy.exp(V_log - W_log)
        - parameters.death_rate_AIDS)

    dZ_log = parameters.death_rate_AIDS * numpy.exp(W_log - Z_log)

    dR_log = force_of_infection * numpy.exp(S_log - R_log)

    return (dS_log, dQ_log, dA_log, dU_log, dD_log,
            dT_log, dV_log, dW_log, dZ_log, dR_log)


def split_state(state):
    return map(numpy.squeeze, numpy.hsplit(state, state.shape[-1]))


class Simulation(container.Container):
    '''
    A class to hold the simulation information.
    '''

    _keys = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
             'diagnosed', 'treated', 'viral_suppression',
             'AIDS', 'dead', 'new_infections')

    _alive = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
              'diagnosed', 'treated', 'viral_suppression', 'AIDS')

    _infected = ('acute', 'undiagnosed', 'diagnosed', 'treated',
                 'viral_suppression', 'AIDS')

    def __init__(self, country, targets_, targets_kwds = {},
                 t_end = 15,
                 baseline = 'baseline', parameters = None,
                 run_baseline = True, _use_log = False,
                 **kwargs):
        self.country = country

        self.t_end = t_end

        self.t = numpy.linspace(0, t_end, 1001)

        if parameters is None:
            self.parameters = datasheet.Parameters(self.country)
        else:
            self.parameters = parameters

        if kwargs:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in kwargs.items():
                setattr(self.parameters, k, v)

        self.targets = targets.Targets(targets_, **targets_kwds)

        self._use_log = _use_log

        if self._use_log:
            # Take log, but map 0 to e^-20.
            Y0 = numpy.ma.log(self.parameters.initial_conditions).filled(-20)
            fcn = _ODEs_log
        else:
            Y0 = self.parameters.initial_conditions.copy()
            fcn = _ODEs

        Y = integrate.odeint(fcn,
                             Y0,
                             self.t,
                             args = (self.targets,
                                     self.parameters),
                             mxstep = 2000)

        if self._use_log:
            self.state = numpy.exp(Y)
        else:
            self.state = Y

        for (k, v) in zip(self.keys(), split_state(self.state)):
            setattr(self, k, v)

        if run_baseline:
            self.baseline = Simulation(self.country,
                                       baseline,
                                       t_end = self.t_end,
                                       parameters = self.parameters,
                                       run_baseline = False,
                                       _use_log = self._use_log)

    @property
    def proportions(self):
        return proportions.Proportions(self.state)

    @property
    def cost(self):
        return cost.cost(self)
    
    @property
    def DALYs(self):
        return effectiveness.DALYs(self)

    @property
    def QALYs(self):
        return effectiveness.QALYs(self)

    @property
    def incremental_cost(self):
        return self.cost - self.baseline.cost

    @property
    def incremental_DALYs(self):
        return self.baseline.DALYs - self.DALYs

    @property
    def incremental_QALYs(self):
        return self.QALYs - self.baseline.QALYs

    @property
    def ICER_DALYs(self):
        return (self.incremental_cost
                / self.incremental_DALYs
                / self.parameters.GDP_per_capita)

    @property
    def ICER_QALYs(self):
        return (self.incremental_cost
                / self.incremental_QALYs
                / self.parameters.GDP_per_capita)

    def net_benefit(self, cost_effectiveness_threshold,
                    effectiveness = 'DALYs'):
        return net_benefit.net_benefit(self, cost_effectiveness_threshold,
                                       effectiveness = effectiveness)

    def incremental_net_benefit(self, cost_effectiveness_threshold,
                                effectiveness = 'DALYs'):
        return (self.net_benefit(cost_effectiveness_threshold,
                                 effectiveness = effectiveness)
                - self.baseline.net_benefit(cost_effectiveness_threshold,
                                            effectiveness = effectiveness))

    @property
    def target_values(self):
        return self.targets(self.parameters, self.t)

    @property
    def control_rates(self):
        return self.target_values.control_rates(self.state)

    @property
    def infected(self):
        return sum(getattr(self, k) for k in self._infected)

    @property
    def alive(self):
        return sum(getattr(self, k) for k in self._alive)

    @property
    def prevalence(self):
        return self.infected / self.alive

    def plot(self):
        plot.simulation(self)
