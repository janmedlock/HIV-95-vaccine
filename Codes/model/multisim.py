'''
Run multiple simulations in parallel.
'''

import joblib

from . import parameters
from . import simulation


class MultiSim:
    '''
    A class to hold the multi-simulation information.
    '''
    def __init__(self, samples, targets, **kwargs):
        with joblib.Parallel(n_jobs = -1, verbose = 5) as parallel:
            self.simulations = parallel(
                joblib.delayed(simulation.Simulation)(s, targets, **kwargs)
                for s in samples)

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
        return [getattr(s, k) for s in self.__getattribute__('simulations')]
