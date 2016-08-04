'''
Simulation of the HIV model.
'''

import copy
import warnings

import numpy
from scipy import integrate
import tables

from . import container
# from . import cost
from . import effectiveness
from . import incidence
# from . import net_benefit
from . import ODEs
from . import plot
from . import proportions


class Simulation(container.Container):
    '''
    A class to hold the simulation information.

    `integrator` is a
    :class:`scipy.integrate.ode` integrator---``'lsoda'``,
    ``'vode'``, ``'dopri5'``, ``'dop853'``---or
    ``'odeint'`` to use :func:`scipy.integrate.odeint`.
    '''

    _keys = ['susceptible', 'vaccinated', 'acute', 'undiagnosed',
             'diagnosed', 'treated', 'viral_suppression',
             'AIDS', 'dead', 'new_infections']

    _alive = ('susceptible', 'vaccinated', 'acute', 'undiagnosed',
              'diagnosed', 'treated', 'viral_suppression', 'AIDS')

    _infected = ('acute', 'undiagnosed', 'diagnosed', 'treated',
                 'viral_suppression', 'AIDS')

    def __init__(self, parameters, targets,
                 t_start = 2015, t_end = 2035,
                 pts_per_year = 120, # = 10 per month
                 integrator = 'odeint',
                 _use_log = True,
                 **kwargs):
        self.parameters = parameters
        self.country = self.parameters.country
        self.targets = targets
        self.pts_per_year = pts_per_year
        self.integrator = integrator
        self._use_log = _use_log
        self.kwargs = kwargs

        if len(self.kwargs) > 0:
            self.parameters = copy.copy(self.parameters)
            for (k, v) in self.kwargs.items():
                setattr(self.parameters, k, v)

        self.t = numpy.linspace(
            t_start, t_end,
            numpy.abs(t_end - t_start) * self.pts_per_year + 1)

        self.simulate()

    def simulate(self):
        Y0 = self.parameters.initial_conditions.copy().values
        if self._use_log:
            Y0 = ODEs.transform(Y0)
            fcn = ODEs.rhs_log
        else:
            fcn = ODEs.rhs

        # Scale time to start at 0 to avoid some solver warnings.
        t_scaled = self.t - self.t[0]
        def fcn_scaled(t_scaled, Y, targets, parameters):
            return fcn(t_scaled + self.t[0], Y, targets, parameters)

        assert numpy.isfinite(self.parameters.R0)
        assert not numpy.all(self.parameters.initial_conditions == 0)

        if self.integrator == 'odeint':
            def fcn_scaled_swap_Yt(Y, t_scaled, targets, parameters):
                return fcn_scaled(t_scaled, Y, targets, parameters)
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
                assert solver.successful()

        if numpy.any(numpy.isnan(Y)):
            msg = ("country = '{}': NaN in solution!").format(self.country)
            if self._use_log:
                msg += "  Re-running with _use_log = False."
                warnings.warn(msg)
                self._use_log = False
                retval = self.simulate()
                self._use_log = True
                return retval
            else:
                raise ValueError(msg)

        if self._use_log:
            self.state = ODEs.transform_inv(Y)
        else:
            self.state = Y

        for (k, v) in zip(self.keys(), ODEs.split_state(self.state)):
            setattr(self, k, v)

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
    def infected(self):
        return sum(getattr(self, k) for k in self._infected)

    @property
    def alive(self):
        return sum(getattr(self, k) for k in self._alive)

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

    def dump(self, h5file):
        for key in self.keys():
            obj = getattr(self, key)
            group = '/{}/{}'.format(self.country, str(self.targets))
            try:
                arr = h5file.get_node(group, key)
            except tables.NoSuchNodeError:
                results.create_carray(group, key, obj = obj,
                                      createparents = True)
            else:
                arr[:] = obj

    @classmethod
    def _build_keys(cls):
        '''
        Build list of keys to dump.
        '''
        for attr in dir(cls):
            if not attr.startswith('_'):
                obj = getattr(cls, attr)
                if not callable(obj):
                    cls._keys.append(attr)

Simulation._build_keys()
