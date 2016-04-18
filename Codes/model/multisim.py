'''
Run multiple simulations in parallel.
'''

import joblib

from . import parameters
from . import simulation


class _MultiSimSuper:
    def keys(self):
        try:
            return self.simulations[0].keys()
        except IndexError:
            pass

    @property
    def t(self):
        try:
            return self.simulations[0].t
        except IndexError:
            pass

    def __getattr__(self, k):
        return [getattr(s, k)
                for s in self.__getattribute__('simulations')]


class _MultiSimBaseline(_MultiSimSuper):
    def __init__(self, simulations):
        self.simulations = [s.baseline for s in simulations]
    

class MultiSim(_MultiSimSuper):
    '''
    A class to hold the multi-simulation information.
    '''

    def __init__(self, samples, targets, **kwargs):
        with joblib.Parallel(n_jobs = -1, verbose = 5) as p:
            self.simulations = p(
                joblib.delayed(simulation.Simulation)(s, targets, **kwargs)
                for s in samples)

        self.baseline = _MultiSimBaseline(self.simulations)
