'''
Aggregate global results.
'''

import numpy

from . import container
from . import incidence
from . import parameters


class Global(container.Container):
    '''
    Class to hold global results.

    The aggregated simulation results are scaled so that the model
    current statistics match UNAIDS current estimates.
    '''
    _keys = ('AIDS', 'alive', 'dead', 'infected', 'new_infections')
    global_alive = 7.2e9
    global_prevalence = 0.008  # CI (0.007, 0.009), UNAIDS 2014
    global_infected = 36.9e6  # CI (34.3e6, 41.4e6), UNAIDS 2014
    global_incidence = 2e6  # CI (1.9e6, 2.2e6), UNAIDS 2014
    global_annual_AIDS_deaths = 1.2e6  # CI (0.98e6, 1.6e6), UNAIDS 2014

    def __init__(self, data):
        self._normalized = False

        self.t = None
        for k in self.keys():
            setattr(self, k, 0)

        for (c, v) in data.items():
            if self.t is None:
                self.t = v.t
            for k in self.keys():
                # Do self.k += v.k
                setattr(self, k,
                        getattr(self, k) + numpy.asarray(getattr(v, k)))
            try:
                v.flush() # Free memory
            except AttributeError:
                pass

        self._normalize()

    def _normalize(self):
        if not self._normalized:
            self.alive *= (self.global_alive
                           / self.alive[..., 0][..., numpy.newaxis])

            self.infected *= (self.global_infected
                              / self.infected[..., 0][..., numpy.newaxis])

            # Convert global annual AIDS deaths
            # to global number of people with AIDS.
            self.global_AIDS = (self.global_annual_AIDS_deaths
                                / parameters.Parameters.death_rate_AIDS)
            self.AIDS *= (self.global_AIDS
                          / self.AIDS[..., 0][..., numpy.newaxis])

            # Compute death rate from slope.
            annual_AIDS_deaths = ((self.dead[..., 1] - self.dead[..., 0])
                                  / (self.t[1] - self.t[0]))
            self.dead *= (self.global_annual_AIDS_deaths
                          / annual_AIDS_deaths[..., numpy.newaxis])

            # I need the second value because the first is NaN.
            incidence0 = incidence.compute(self.t, self.new_infections)[..., 1]
            self.new_infections *= (self.global_incidence
                                    / incidence0[..., numpy.newaxis])

        self._normalized = True

    @property
    def prevalence(self):
        prev = self.infected / self.alive
        prev *= (self.global_prevalence
                 / prev[..., 0][..., numpy.newaxis])
        return prev

    @property
    def incidence(self):
        return incidence.compute(self.t, self.new_infections)

    @property
    def incidence_per_capita(self):
        return self.incidence / numpy.asarray(self.alive)
