'''
Simulation of the HIV model.
'''

import copy

import numpy
from scipy import integrate

from . import container
from . import cost
from . import effectiveness
from . import net_benefit
from . import parameters
from . import plot
from . import proportions
from . import targets


def transform(state):
    '''
    Log transform all the state variables except the last two,
    cumulative dead and cumulative new infections.  These last two
    can be negative if time goes backwards.
    '''
    state_trans = numpy.ma.hstack((numpy.ma.log(state[..., : -2]),
                                   state[..., -2 : ]))
    return state_trans


def transform_inv(state_trans):
    '''
    Inverse log transform all the state variables except the last two,
    cumulative dead and cumulative new infections.  These last two
    can be negative if time goes backwards.
    '''
    state = numpy.hstack((numpy.exp(state_trans[..., : -2]),
                          state_trans[..., -2 : ]))
    return state


class Simulation(container.Container):
    '''
    A class to hold the simulation information.

    `integrator` is a
    :class:`scipy.integrate.ode` integrator---``'lsoda'``,
    ``'vode'``, ``'dopri5'``, ``'dop853'``---or
    ``'odeint'`` to use :func:`scipy.integrate.odeint`.
    '''

    _keys = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
             'diagnosed', 'treated', 'viral_suppression',
             'AIDS', 'dead', 'new_infections')

    _alive = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
              'diagnosed', 'treated', 'viral_suppression', 'AIDS')

    _infected = ('acute', 'undiagnosed', 'diagnosed', 'treated',
                 'viral_suppression', 'AIDS')

    def __init__(self, parameters_, targets_,
                 targets_kwds = {},
                 t_start = 2015,
                 t_end = 2035,
                 baseline = 'baseline',
                 run_baseline = True,
                 _use_log = True,
                 pts_per_year = 120, # = 10 per month
                 integrator = 'lsoda',
                 **kwargs):
        from . import ODEs

        self.parameters = parameters_

        self.country = self.parameters.country

        self.t_start = t_start
        self.t_end = t_end

        if kwargs:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in kwargs.items():
                setattr(self.parameters, k, v)

        self.targets = targets.Targets(targets_, **targets_kwds)

        self._use_log = _use_log

        t = numpy.linspace(
            self.t_start, self.t_end,
            numpy.abs(self.t_end - self.t_start) * pts_per_year + 1)

        if self._use_log:
            Y0 = transform(self.parameters.initial_conditions).copy()
            # Map 0 to exp(-20).
            Y0 = Y0.filled(-20)
            fcn = ODEs.ODEs_log
        else:
            Y0 = self.parameters.initial_conditions.copy()
            fcn = ODEs.ODEs

        if integrator == 'odeint':
            def fcn_swap_Yt(Y, t, targets_, parameters):
                return fcn(t, Y, targets_, parameters)
            Y = integrate.odeint(fcn_swap_Yt,
                                 Y0,
                                 t,
                                 args = (self.targets,
                                         self.parameters),
                                 mxstep = 2000)
        else:
            solver = integrate.ode(fcn)
            solver.set_integrator(integrator, nsteps = 2000)
            solver.set_f_params(self.targets, self.parameters)
            solver.set_initial_value(Y0, t[0])
            Y = numpy.empty((len(t), len(Y0)))
            Y[0] = Y0
            for i in range(1, len(t)):
                Y[i] = solver.integrate(t[i])
                if not _use_log:
                    # Force to be non-negative.
                    Y[i, : -2] = Y[i, : -2].clip(0, numpy.inf)
                    solver.set_initial_value(Y.iloc[i], t[i])
                try:
                    assert solver.successful()
                except AssertionError:
                    dY = fcn(t[i - 1], Y[i - 1],
                             self.targets, self.parameters)
                    print('t = {}'.format(t[i - 1]))
                    import pandas
                    if _use_log:
                        idx = ['S_log', 'Q_log', 'A_log', 'U_log', 'D_log',
                               'T_log', 'V_log', 'W_log', 'Z', 'R']
                    else:
                        idx = ['S', 'Q', 'A', 'U', 'D',
                               'T', 'V', 'W', 'Z', 'R']
                    print('Y = {}'.format(pandas.Series(Y[i - 1],
                                                        index = idx)))
                    print('dY = {}'.format(pandas.Series(dY,
                                                         index = idx)))
                    raise

        if self._use_log:
            self.state = transform_inv(Y)
        else:
            self.state = Y
        self.t = t

        for (k, v) in zip(self.keys(), ODEs.split_state(self.state)):
            setattr(self, k, v)

        if run_baseline:
            self.baseline = Simulation(self.parameters,
                                       baseline,
                                       t_start = self.t_start,
                                       t_end = self.t_end,
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

    @property
    def R0(self):
        return self.parameters.R0

    def plot(self):
        plot.simulation(self)
