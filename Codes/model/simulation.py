'''
Simulation of the HIV model.
'''

import copy
import warnings

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
                 baseline_targets = 'baseline',
                 baseline_targets_kwds = {},
                 pts_per_year = 120, # = 10 per month
                 integrator = 'lsoda',
                 _use_log = True,
                 **kwargs):
        self.parameters = parameters_
        self.country = self.parameters.country
        self.baseline_targets = baseline_targets
        self.baseline_targets_kwds = baseline_targets_kwds
        self.pts_per_year = pts_per_year
        self.integrator = integrator
        self._use_log = _use_log
        self.kwargs = kwargs

        if len(self.kwargs) > 0:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in self.kwargs.items():
                setattr(self.parameters, k, v)

        self.targets = targets.Targets(targets_, **targets_kwds)

        self.t = numpy.linspace(
            t_start, t_end,
            numpy.abs(t_end - t_start) * self.pts_per_year + 1)

        self.simulate()

    def simulate(self):
        '''
        ... todo:: Why is the solver failing part way through some simulations?
        '''
        from . import ODEs

        Y0 = self.parameters.initial_conditions.copy().values
        if self._use_log:
            Y0 = ODEs.transform(Y0)
            fcn = ODEs.ODEs_log
        else:
            fcn = ODEs.ODEs

        # Scale time to start at 0 to avoid some solver warnings.
        t_scaled = self.t - self.t[0]
        def fcn_scaled(t_scaled, Y, targets_, parameters):
            return fcn(t_scaled + self.t[0], Y, targets_, parameters)

        # If R0 is nan or the initial conditions are all 0 or fcn() is nan,
        # then return nans without running solver.
        if (numpy.isnan(self.parameters.R0)
            or numpy.all(self.parameters.initial_conditions == 0)):
            msg = "country = '{}': ".format(self.country)
            if numpy.isnan(self.parameters.R0):
                msg += "R_0 = NaN!"
                msg += "  There are probably NaN parameter values!"
            else:
                msg += 'I.C.s are all 0!'
            msg += "  Skipping solver."
            warnings.warn(msg)
            Y = numpy.nan * numpy.ones((len(self.t), len(Y0)))
        elif self.integrator == 'odeint':
            def fcn_scaled_swap_Yt(Y, t_scaled, targets_, parameters):
                return fcn_scaled(t_scaled, Y, targets_, parameters)
            Y = integrate.odeint(fcn_scaled_swap_Yt,
                                 Y0,
                                 t_scaled,
                                 args = (self.targets,
                                         self.parameters),
                                 mxstep = 2000,
                                 mxhnil = 1)
        else:
            solver = integrate.ode(fcn_scaled)
            if self.integrator == 'lsoda':
                kwds = dict(max_hnil = 1)
            else:
                kwds = {}
            solver.set_integrator(self.integrator,
                                  nsteps = 2000,
                                  **kwds)
            solver.set_f_params(self.targets, self.parameters)
            solver.set_initial_value(Y0, t_scaled[0])
            Y = numpy.empty((len(t_scaled), len(Y0)))
            Y[0] = Y0
            for i in range(1, len(t_scaled)):
                Y[i] = solver.integrate(t_scaled[i])
                if not self._use_log:
                    # Force to be non-negative.
                    Y[i, : -2] = Y[i, : -2].clip(0, numpy.inf)
                    solver.set_initial_value(Y[i], t_scaled[i])
                try:
                    assert solver.successful()
                except AssertionError:
                    dY = fcn_scaled(t_scaled[i - 1], Y[i - 1],
                                    self.targets, self.parameters)
                    print('t = {}'.format(t_scaled[i - 1]))
                    import pandas
                    idx = ['S', 'Q', 'A', 'U', 'D',
                           'T', 'V', 'W', 'Z', 'R']
                    if self._use_log:
                        for i in ODEs.vars_log:
                            idx[i] += '_log'
                    print('Y = {}'.format(pandas.Series(Y[i - 1],
                                                        index = idx)))
                    print('dY = {}'.format(pandas.Series(dY,
                                                         index = idx)))
                    raise
                if numpy.any(numpy.isnan(Y[i])):
                    msg = ("country = '{}': "
                           + "At t = {}, NaN state values!").format(
                               self.country, self.t[i])
                    warnings.warn(msg)
                    Y[i : ] = numpy.nan
                    break

        if self._use_log:
            self.state = ODEs.transform_inv(Y)
        else:
            self.state = Y

        for (k, v) in zip(self.keys(), ODEs.split_state(self.state)):
            setattr(self, k, v)

        if self.baseline_targets is not None:
            self.baseline = Simulation(
                self.parameters,
                self.baseline_targets,
                targets_kwds = self.baseline_targets_kwds,
                t_start = self.t[0],
                t_end = self.t[-1],
                baseline_targets = None,
                pts_per_year = self.pts_per_year,
                integrator = self.integrator,
                _use_log = self._use_log,
                **self.kwargs)

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
