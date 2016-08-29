'''
Simulation of the HIV model.
'''

import copy

import joblib
import numpy

# from . import cost
from . import effectiveness
from . import incidence
# from . import net_benefit
from . import ODEs
from . import parameters
from . import plot
from . import proportions
from . import results


t_start = 2015
t_end = 2035
pts_per_year = 120  # = 10 per month
t = numpy.linspace(t_start, t_end,
                   numpy.abs(t_end - t_start) * pts_per_year + 1)


def _add_ODE_vars_as_attrs(cls):
    '''
    Add ODE variables as attributes.
    '''
    def _getter(v):
        def getter(self):
            try:
                return ODEs.get_variable(self.state, v)
            except ValueError:
                raise AttributeError
        return getter
    
    for v in ODEs.variables:
        setattr(cls, v, property(_getter(v)))
    return cls
    

@_add_ODE_vars_as_attrs
class _Super:
    '''
    Superclass for Simulation and MultiSim.
    '''

    @property
    def alive(self):
        return ODEs.get_alive(self.state)

    @property
    def infected(self):
        return ODEs.get_infected(self.state)

    @property
    def proportions(self):
        return proportions.get(self.state)

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
        return self.target(self.parameters, t)

    @property
    def control_rates(self):
        return self.target_values.control_rates(self.state)

    @property
    def prevalence(self):
        return self.infected / self.alive

    @property
    def incidence(self):
        return incidence.compute(self.new_infections)

    @property
    def incidence_per_capita(self):
        return self.incidence / numpy.asarray(self.alive)

    @property
    def R0(self):
        return self.parameters.R0

    def dump(self, parameters_type):
        return results.dump(self, parameters_type = parameters_type)

    @classmethod
    def _from_state(cls, params, target, state):
        obj = cls.__new__(cls)
        obj.parameters = params
        obj.target = target
        obj.state = state
        return obj


class Simulation(_Super):
    '''
    A class to hold the simulation information.
    '''
    def __init__(self, params, target):
        self.parameters = params
        self.target = target
        self.solve()

    def solve(self):
        self.state = ODEs.solve(t, self.target, self.parameters)

    def plot(self, *args, **kwargs):
        plot.simulation_(self, *args, **kwargs)


class MultiSim(_Super):
    '''
    A class to hold the multi-simulation information.
    '''
    def __init__(self, params, target):
        self.parameters = params
        self.target = target
        self.solve()

    def solve(self):
        with joblib.Parallel(n_jobs = -1, verbose = 5) as parallel:
            simulations = parallel(joblib.delayed(Simulation)(p, self.target)
                                   for p in self.parameters)
        self.state = numpy.array([s.state for s in simulations])

    def dump(self):
        return super().dump(parameters_type = 'sample')

    @classmethod
    def load(cls, country, target, state):
        params = parameters.Samples(country)
        return cls._from_state(params, target, state)


def _from_state(country, target, state, parameters_type):
    '''
    Factory to rebuild a Simulation or MultiSims object from state.
    '''
    if parameters_type == 'sample':
        params = parameters.Samples(country)
        return MultiSim._from_state(params, target, state)
    elif parameters_type == 'mode':
        params = parameters.Mode.from_country(country)
        return Simulation._from_state(params, target, state)
    else:
        raise ValueError("Unknown parameters_type '{}'!".format(
            parameters_type))
