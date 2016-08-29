'''
Simulation of the HIV model.
'''

import copy

import numpy

# from . import cost
from . import effectiveness
from . import incidence
# from . import net_benefit
from . import ODEs
from . import plot
from . import proportions


t_start = 2015
t_end = 2035
pts_per_year = 120  # = 10 per month
t = numpy.linspace(t_start, t_end,
                   numpy.abs(t_end - t_start) * pts_per_year + 1)


class Simulation:
    '''
    A class to hold the simulation information.

    `integrator` is a
    :class:`scipy.integrate.ode` integrator---``'lsoda'``,
    ``'vode'``, ``'dopri5'``, ``'dop853'``---or
    ``'odeint'`` to use :func:`scipy.integrate.odeint`.

    .. todo:: Implement dumping and loading that to/from an npy file.
              Implement moving that to Multisims, too.
    '''

    def __init__(self, parameters, targets):
        self.parameters = parameters
        self.targets = targets
        self.solve()

    def solve(self):
        self.state = ODEs.solve(t, self.targets, self.parameters)

    @property
    def alive(self):
        return ODEs.get_alive(self.state)

    @property
    def infected(self):
        return ODEs.get_infected(self.state)

    @property
    def proportions(self):
        return proportions.Proportions(self.state)

    # @property
    # def cost(self):
    #     return cost.cost(self)
    
    @property
    def DALYs(self):
        return effectiveness.DALYs(self)

    @property
    def QALYs(self):
        return effectiveness.QALYs(self)

    # def incremental_cost(self, baseline):
    #     return self.cost - baseline.cost

    def incremental_DALYs(self, baseline):
        return baseline.DALYs - self.DALYs

    def incremental_QALYs(self, baseline):
        return self.QALYs - baseline.QALYs

    # @property
    # def ICER_DALYs(self):
    #     return (self.incremental_cost
    #             / self.incremental_DALYs
    #             / self.parameters.GDP_per_capita)

    # @property
    # def ICER_QALYs(self):
    #     return (self.incremental_cost
    #             / self.incremental_QALYs
    #             / self.parameters.GDP_per_capita)

    # def net_benefit(self, cost_effectiveness_threshold,
    #                 effectiveness = 'DALYs'):
    #     return net_benefit.net_benefit(self, cost_effectiveness_threshold,
    #                                    effectiveness = effectiveness)

    # def incremental_net_benefit(self, baseline,
    #                             cost_effectiveness_threshold,
    #                             effectiveness = 'DALYs'):
    #     return (self.net_benefit(cost_effectiveness_threshold,
    #                              effectiveness = effectiveness)
    #             - baseline.net_benefit(cost_effectiveness_threshold,
    #                                         effectiveness = effectiveness))

    @property
    def target_values(self):
        return self.targets(self.parameters, self.t)

    @property
    def control_rates(self):
        return self.target_values.control_rates(self.state)

    @property
    def prevalence(self):
        return self.infected / self.alive

    @property
    def incidence(self):
        return incidence.compute(self.t, self.new_infections)

    @property
    def incidence_per_capita(self):
        return self.incidence / numpy.asarray(self.alive)

    @property
    def R0(self):
        return self.parameters.R0

    def plot(self, *args, **kwargs):
        plot.simulation(self, *args, **kwargs)

    @classmethod
    def _from_state(cls, country, targets, state):
        obj = super().__new__(cls)
        obj.country = country
        obj.targets = targets
        obj.state = state
        return obj

    @classmethod
    def _add_variables_as_attrs(cls):
        '''
        Add ODE variables as attributes.
        '''
        for v in ODEs.variables:
            def getter(self):
                try:
                    return ODEs.get_variable(self.state, v)
                except ValueError:
                    raise AttributeError
            setattr(cls, v, property(getter))


Simulation._add_variables_as_attrs()
