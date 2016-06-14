'''
Tests.
'''

import unittest

# Import tests from other modules.
# These get automatically run without any further code.
from .cost import TestRelativeCostOfEffort
from .effectiveness import TestDALYsQALYs


class TestCE(unittest.TestCase):
    '''
    Tests of statsistics from a run of the simulation with
    precomputed values.
    '''
    country = 'Nigeria'
    # Precomputed values.
    stats = dict(cost = 44373373515.342896,
                 DALYs = 25118516.824676983,
                 QALYs = 2201334748.7090836,
                 incremental_cost = 32324197633.36628,
                 incremental_DALYs = 23269279.560440436,
                 incremental_QALYs = 27464382.193239689,
                 ICER_DALYs = 0.43365824620362664,
                 ICER_QALYs = 0.36741823987165301)

    def test_stats(self):
        import numpy
        from .parameters import Parameters
        from .simulation import Simulation
        parameters = Parameters(self.country).mode()
        simulation = Simulation(parameters, '909090')
        for (i, kv) in enumerate(self.stats.items()):
            k, v = kv
            with self.subTest(i = i):
                actual = getattr(simulation, k)
                msg = '{}: Expected {}.  Got {}.'.format(k, v, actual)
                self.assertTrue(numpy.isclose(actual, v), msg)
