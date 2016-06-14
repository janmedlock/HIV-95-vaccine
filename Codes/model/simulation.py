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
from . import ODEs
from . import parameters
from . import plot
from . import proportions
from . import targets


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

    def __init__(self, parameters_, targets_,
                 targets_kwds = {},
                 t_end = 20,
                 baseline = 'baseline',
                 run_baseline = True,
                 _use_log = False,
                 pts_per_year = 120, # = 10 per month
                 **kwargs):
        self.parameters = parameters_

        self.country = self.parameters.country

        self.t_end = t_end

        self.t = numpy.linspace(0, t_end,
                                numpy.abs(t_end) * pts_per_year + 1)

        if kwargs:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in kwargs.items():
                setattr(self.parameters, k, v)

        self.targets = targets.Targets(targets_, **targets_kwds)

        self._use_log = _use_log

        if self._use_log:
            # Take log, but map 0 to e^-20.
            Y0 = numpy.ma.log(self.parameters.initial_conditions).filled(-20)
            # Last two variables are not log transformed.
            Y0[-2 : ] = self.parameters.initial_conditions[-2 : ]
            fcn = ODEs.ODEs_log
        else:
            Y0 = self.parameters.initial_conditions.copy()
            fcn = ODEs.ODEs

        # Y = integrate.odeint(fcn,
        #                      Y0,
        #                      self.t,
        #                      args = (self.targets,
        #                              self.parameters),
        #                      mxstep = 2000)
        def fcn_swap_tY(t, Y, targets_, parameters):
            return fcn(Y, t, targets_, parameters)
        r = integrate.ode(fcn_swap_tY)
        r.set_integrator('dop853')
        r.set_f_params(self.targets, self.parameters)
        r.set_initial_value(Y0, 0)
        Y = numpy.empty((len(self.t), len(Y0)))
        Y[0] = Y0
        for (i, t_i) in enumerate(self.t[1 : ]):
            y_i = r.integrate(t_i)
            if not _use_log:
                # Force to be non-negative.
                y_i[ : -2] = y_i[ : -2].clip(0, numpy.inf)
                r.set_initial_value(y_i, t_i)
            Y[i] = y_i
            # assert r.successful()

        if self._use_log:
            self.state = numpy.hstack((numpy.exp(Y[:, : -2]),
                                       Y[:, -2 : ]))
        else:
            self.state = Y

        for (k, v) in zip(self.keys(), ODEs.split_state(self.state)):
            setattr(self, k, v)

        if run_baseline:
            self.baseline = Simulation(self.parameters,
                                       baseline,
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
