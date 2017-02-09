'''
Aggregate multi-country (e.g. Global or regional) results.
'''

import numpy

from . import incidence
from . import parameters
from . import simulation


class MultiCountry(simulation._Super):
    '''
    Class to hold the results of multiple countries,
    e.g. Global or regional.
    '''
    def __init__(self, region, target, data):
        self.region = region
        self.target = target
        self.state = 0
        for v in data.values():
            self.state += v.state
            try:
                v.flush() # Free memory
            except AttributeError:
                pass

    @classmethod
    def _from_state(cls, region, target, state):
        obj = cls.__new__(cls)
        obj.region = region
        obj.target = target
        obj.state = state
        return obj


class Global(MultiCountry):
    '''
    Class to hold global results.

    The aggregated simulation results are scaled so that the model
    current statistics match UNAIDS current estimates.

    .. todo:: Adjust for ODE variables, infected, alive.
    '''
    global_alive = 7.2e9
    global_prevalence = 0.008  # CI (0.007, 0.009), UNAIDS 2014
    global_infected = 36.9e6  # CI (34.3e6, 41.4e6), UNAIDS 2014
    global_incidence = 2e6  # CI (1.9e6, 2.2e6), UNAIDS 2014
    global_annual_AIDS_deaths = 1.2e6  # CI (0.98e6, 1.6e6), UNAIDS 2014

    def __init__(self, target, data):
        super().__init__('Global', target, data)
        self._normalize()

    def _normalize(self):
        self._alive_scale = self.global_alive / super().alive[..., 0]
        self._infected_scale = self.global_infected / super().infected[..., 0]
        self._prevalence_scale = (self.global_prevalence
                                  / super().prevalence[..., 0])
        # Also scale viral_suppression by _infected_scale for now.
        # self._viral_suppression_scale = self._infected_scale
        # No, don't scale for now.
        self._viral_suppression_scale = numpy.asarray(1)

        # Convert global annual AIDS deaths
        # to global number of people with AIDS.
        global_AIDS = (self.global_annual_AIDS_deaths
                       / parameters.Parameters.death_rate_AIDS)
        self._AIDS_scale = global_AIDS / super().AIDS[..., 0]

        # Compute death rate from slope.
        annual_AIDS_deaths = ((super().dead[..., 1] - super().dead[..., 0])
                              / (simulation.t[1] - simulation.t[0]))
        self._scale_dead = self.global_annual_AIDS_deaths / annual_AIDS_deaths

        # I need the second value because the first is NaN.
        incidence0 = incidence.compute(super().new_infections)[..., 1]
        self._scale_new_infections = self.global_incidence / incidence0

    @property
    def alive(self):
        return self._alive_scale[..., numpy.newaxis] * super().alive

    @property
    def infected(self):
        return self._infected_scale[..., numpy.newaxis] * super().infected

    @property
    def prevalence(self):
        return self._prevalence_scale[..., numpy.newaxis] * super().prevalence

    @property
    def viral_suppression(self):
        return (self._viral_suppression_scale[..., numpy.newaxis]
                * super().viral_suppression)

    @property
    def AIDS(self):
        return self._AIDS_scale[..., numpy.newaxis] * super().AIDS

    @property
    def dead(self):
        return self._scale_dead[..., numpy.newaxis] * super().dead

    @property
    def new_infections(self):
        return (self._scale_new_infections[..., numpy.newaxis]
                * super().new_infections)

    @classmethod
    def _from_state(cls, target, state):
        obj = super()._from_state('Global', target, state)
        obj._normalize()
        return obj
