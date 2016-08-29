'''
Run multiple simulations in parallel.

.. todo:: Use the new style of simulation and results.
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
        return simulation.Simulation._keys

    @property
    def t(self):
        try:
            return self.simulations[0].t
        except IndexError:
            pass

    def __getattr__(self, k):
        return [getattr(s, k) for s in self.__getattribute__('simulations')]
