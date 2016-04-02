'''
Aggregate global results.
'''

import collections

import numpy

from . import container
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
    global_annual_new_infections = 2e6  # CI (1.9e6, 2.2e6), UNAIDS 2014
    global_annual_AIDS_deaths = 1.2e6  # CI (0.98e6, 1.6e6), UNAIDS 2014

    def __init__(self, data, t):
        for k in self.keys():
            setattr(self, k, 0)
        for (l, v) in data.items():
            for k in self.keys():
                setattr(self, k,
                        getattr(self, k) + getattr(v, k))

        # Convert global annual AIDS deaths
        # to global number of people with AIDS.
        self.global_AIDS = (self.global_annual_AIDS_deaths
                            / parameters.Parameters.death_rate_AIDS)
        self.AIDS *= self.global_AIDS / self.AIDS[0]

        self.alive *= self.global_alive / self.alive[0]

        # Compute death rate from slope.
        annual_AIDS_deaths = (self.dead[1] - self.dead[0]) / (t[1] - t[0])
        self.dead *= self.global_annual_AIDS_deaths / annual_AIDS_deaths

        self.infected *= self.global_infected / self.infected[0]

        # Compute incidence from slope.
        annual_new_infections = ((self.new_infections[1]
                                  - self.new_infections[0])
                                 / (t[1] - t[0]))
        self.new_infections *= (self.global_annual_new_infections
                                / annual_new_infections)

    @property
    def prevalence(self):
        prev = self.infected / self.alive
        prev *= self.global_prevalence / prev[0]
        return prev


def build_global(results, countries, levels, t):
    data = collections.OrderedDict()
    for l in levels:
        results_ = {c: results[c][l] for c in countries}
        data[l] = Global(results_, t)
    return data
