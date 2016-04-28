'''
Aggregate global results.
'''

import numpy

from . import container
from . import parameters


class _GlobalSuper(container.Container):
    _keys = ('AIDS', 'alive', 'dead', 'infected', 'new_infections')
    global_alive = 7.2e9
    global_prevalence = 0.008  # CI (0.007, 0.009), UNAIDS 2014
    global_infected = 36.9e6  # CI (34.3e6, 41.4e6), UNAIDS 2014
    global_annual_new_infections = 2e6  # CI (1.9e6, 2.2e6), UNAIDS 2014
    global_annual_AIDS_deaths = 1.2e6  # CI (0.98e6, 1.6e6), UNAIDS 2014

    def __init__(self):
        self.t = None
        self._normalized = False

        for k in self.keys():
            setattr(self, k, 0)

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

            # Compute incidence from slope.
            annual_new_infections = ((self.new_infections[..., 1]
                                      - self.new_infections[..., 0])
                                     / (self.t[1] - self.t[0]))
            self.new_infections *= (self.global_annual_new_infections
                                    / annual_new_infections[..., numpy.newaxis])
        self._normalized = True

    def _add(self, k, v):
        '''
        self.k += v.k.
        '''
        setattr(self, k, getattr(self, k) + numpy.asarray(getattr(v, k)))
        
    @property
    def prevalence(self):
        prev = self.infected / self.alive
        prev *= (self.global_prevalence
                 / prev[..., 0][..., numpy.newaxis])
        return prev


class Global(_GlobalSuper):
    '''
    Class to hold global results.

    The aggregated simulation results are scaled so that the model
    current statistics match UNAIDS current estimates.
    '''

    def __init__(self, data):
        super().__init__()

        self.baseline = _GlobalSuper()
                
        for (c, v) in data.items():
            if self.t is None:
                self.t = self.baseline.t = v.t
            for k in self.keys():
                self._add(k, v)
                self.baseline._add(k, v.baseline)
            v.flush() # Free memory

        self._normalize()
        self.baseline._normalize()
