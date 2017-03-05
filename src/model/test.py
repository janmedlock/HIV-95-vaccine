'''
Tests.
'''

import unittest

# Import tests from other modules.
# These get automatically run without any further code.
from .cost import TestRelativeCostOfEffort
from .effectiveness import TestDALYsQALYs


class TestEffectiveness(unittest.TestCase):
    '''
    Tests of statsistics from a run of the simulation with
    precomputed values.
    '''
    country = 'Nigeria'
    # Precomputed values.
    stats = dict(DALYs = 25024927.454149053,
                 QALYs = 2201169624.7756662)

    def test_stats(self):
        from numpy import isclose
        from .parameters import Parameters
        from .simulation import Simulation
        from .target import UNAIDS90
        parameters = Parameters(self.country).mode()
        simulation = Simulation(parameters, UNAIDS90())
        for (i, kv) in enumerate(self.stats.items()):
            k, v = kv
            with self.subTest(stat = k):
                actual = getattr(simulation, k)
                msg = '{}: Expected {}.  Got {}.'.format(k, v, actual)
                self.assertTrue(isclose(actual, v), msg)
