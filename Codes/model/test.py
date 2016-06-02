'''
Tests.
'''

import unittest

import numpy

from . import datasheet
from . import simulation
from .cost import TestRelativeCostOfEffort
from .effectiveness import TestDALYsQALYs


class TestCE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        country = 'Nigeria'
        cls.simulation = simulation.Simulation(country, '909090')

    def test_cost(self):
        self.assertTrue(numpy.isclose(self.simulation.cost,
                                      19579571706.41235))

    def test_DALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.DALYs,
                                      13807040.061347544))

    def test_QALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.QALYs,
                                      1542178864.3872309))

    def test_incremental_cost(self):
        self.assertTrue(numpy.isclose(self.simulation.incremental_cost,
                                      14362126332.038065))
        
    def test_incremental_DALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.incremental_DALYs,
                                      4564739.0117855407))

    def test_incremental_QALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.incremental_QALYs,
                                      5248944.484855175))

    def test_ICER_DALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.ICER_DALYs,
                                      0.98221278690875868))

    def test_ICER_QALYs(self):
        self.assertTrue(numpy.isclose(self.simulation.ICER_QALYs,
                                      0.85418030981532012))
