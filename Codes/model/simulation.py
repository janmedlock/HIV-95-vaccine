'''
Solve the HIV model.
'''

import numpy
from scipy import integrate

from . import container
from . import control_rates
from . import cost
from . import datasheet
from . import effectiveness
from . import net_benefit
from . import plot
from . import proportions
from . import targets


def _ODEs(state, t, targets_, parameters):
    # S is susceptible.
    # A is acute infection.
    # U is undiagnosed.
    # D is diagnosed but not treated.
    # T is treated but not viral suppressed.
    # V is viral suppressed.
    # W is AIDS.
    # Z is dead from AIDS.
    # R is new infectons.
    S, A, U, D, T, V, W, Z, R = state

    # Total sexually active population.
    N = S + A + U + D + T + V

    controls = control_rates.ControlRates(t, state, targets_, parameters)

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
          - controls.diagnosis * U
          - parameters.death_rate * U
          - parameters.progression_rate_unsuppressed * U)

    dD = (controls.diagnosis * U
          + controls.nonadherance * (T + V)
          - controls.treatment * D
          - parameters.death_rate * D
          - parameters.progression_rate_unsuppressed * D)

    dT = (controls.treatment * D
          - controls.nonadherance * T
          - parameters.suppression_rate * T
          - parameters.death_rate * T
          - parameters.progression_rate_unsuppressed * T)

    dV = (parameters.suppression_rate * T
          - controls.nonadherance * V
          - parameters.death_rate * V
          - parameters.progression_rate_suppressed * V)

    dW = (parameters.progression_rate_unsuppressed * (U + D + T)
          + parameters.progression_rate_suppressed * V
          - parameters.death_rate_AIDS * W)

    dZ = parameters.death_rate_AIDS * W

    dR = force_of_infection * S

    return (dS, dA, dU, dD, dT, dV, dW, dZ, dR)


def _ODEs_log(state_log, t, targets_, parameters):
    state = numpy.exp(state_log)
    # S is susceptible.
    # A is acute infection.
    # U is undiagnosed.
    # D is diagnosed but not treated.
    # T is treated but not viral suppressed.
    # V is viral suppressed.
    # W is AIDS.
    # Z is dead from AIDS.
    # R is new infectons.
    S, A, U, D, T, V, W, Z, R = numpy.exp(state_log)
    S_log, A_log, U_log, D_log, T_log, V_log, W_log, Z_log, R_log = state_log

    # Total sexually active population.
    N = S + A + U + D + T + V
    N_log = numpy.log(N)

    controls = control_rates.ControlRates(t, state, targets_, parameters)

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
              - controls.diagnosis
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dD_log = (controls.diagnosis * numpy.exp(U_log - D_log)
              + controls.nonadherance * (numpy.exp(T_log - D_log)
                                         + numpy.exp(V_log - D_log))
              - controls.treatment
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dT_log = (controls.treatment * numpy.exp(D_log - T_log)
              - controls.nonadherance
              - parameters.suppression_rate
              - parameters.death_rate
              - parameters.progression_rate_unsuppressed)

    dV_log = (parameters.suppression_rate * numpy.exp(T_log - V_log)
              - controls.nonadherance
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

    return (dS_log, dA_log, dU_log, dD_log, dT_log,
            dV_log, dW_log, dZ_log, dR_log)


def split_state(state):
    return map(numpy.squeeze, numpy.hsplit(state, state.shape[-1]))


class Simulation(container.Container):
    '''
    A class to hold the simulation information.
    '''

    _keys = ('susceptible', 'acute', 'undiagnosed',
             'diagnosed', 'treated', 'viral_suppression',
             'AIDS', 'dead', 'new_infections')

    _alive = ('susceptible', 'acute', 'undiagnosed',
              'diagnosed', 'treated', 'viral_suppression', 'AIDS')

    _infected = ('acute', 'undiagnosed', 'diagnosed', 'treated',
                 'viral_suppression', 'AIDS')

    def __init__(self, country, targets_, t_end = 15,
                 baseline = 'baseline', _use_log = True,
                 _parameters = None):
        self.country = country

        self.targets = targets_

        self.t_end = t_end

        self.t = numpy.linspace(0, t_end, 1001)

        self._use_log = _use_log

        if _parameters is None:
            self.parameters = datasheet.Parameters(self.country)
        else:
            self.parameters = _parameters

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
                             args = (self.targets, self.parameters),
                             mxstep = 2000)

        if self._use_log:
            self.state = numpy.exp(Y)
        else:
            self.state = Y

        for (k, v) in zip(self.keys(), split_state(self.state)):
            setattr(self, k, v)

        if baseline != self.targets:
            self.baseline = Simulation(self.country,
                                       baseline,
                                       t_end = self.t_end,
                                       _use_log = self._use_log,
                                       _parameters = self.parameters)

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

    @property
    def target_values(self):
        return targets.TargetValues(self.t, self.targets, self.parameters)

    @property
    def control_rates(self):
        return control_rates.ControlRates(self.t, self.state, self.targets,
                                          self.parameters)

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
