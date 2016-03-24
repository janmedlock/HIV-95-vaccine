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

    def __init__(self, country, targets_, targets_kwds = {},
                 t_end = 15,
                 baseline = 'baseline', parameters_ = None,
                 run_baseline = True, _use_log = False,
                 **kwargs):
        self.country = country

        self.t_end = t_end

        pts_per_year = 120  # = 10 per month
        self.t = numpy.linspace(0, t_end, t_end * pts_per_year + 1)

        if parameters_ is None:
            self.parameters = parameters.Parameters(self.country)
        else:
            self.parameters = parameters_

        if kwargs:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in kwargs.items():
                setattr(self.parameters, k, v)

        self.targets = targets.Targets(targets_, **targets_kwds)

        self._use_log = _use_log

        if self._use_log:
            # Take log, but map 0 to e^-20.
            Y0 = numpy.ma.log(self.parameters.initial_conditions).filled(-20)
            fcn = ODEs.ODEs_log
        else:
            Y0 = self.parameters.initial_conditions.copy()
            fcn = ODEs.ODEs

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

        for (k, v) in zip(self.keys(), ODEs.split_state(self.state)):
            setattr(self, k, v)

        if run_baseline:
            self.baseline = Simulation(self.country,
                                       baseline,
                                       t_end = self.t_end,
                                       parameters_ = self.parameters,
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
