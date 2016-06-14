'''
Compute effectiveness.

For disability weights :math:`\mathbf{w}`
and state variables :math:`\mathbf{y}(t)`,
DALYs are

.. math:: D = \int_0^{t_\mathrm{end}} \mathbf{w}^{\mathrm{T}}
          \mathbf{y}(t)\;\mathrm{d} t,

and QALYs are

.. math:: Q = \int_0^{t_\mathrm{end}}
          (\mathbf{1} - \mathbf{w})^{\mathrm{T}}
          \mathbf{y}(t)\;\mathrm{d} t,

so DALYs and QALYs are related by

.. math:: Q = \int_0^{t_\mathrm{end}} \mathbf{1}^{\mathrm{T}}
          \mathbf{y}(t)\;\mathrm{d} t - D.
'''

import unittest

import numpy
from scipy import integrate


def QALYs(simulation):
    # A component of Sphinx chokes on the '@'.
    # QALYs_rate = (simulation.state[:, : -1]
    #               @ simulation.parameters.QALY_rates_per_person)
    QALYs_rate = numpy.dot(simulation.state[:, : -1],
                           simulation.parameters.QALY_rates_per_person)
    return integrate.simps(QALYs_rate, simulation.t)


def DALYs(simulation):
    # A component of Sphinx chokes on the '@'.
    # DALYs_rate = (simulation.state[:, : -1]
    #               @ simulation.parameters.DALY_rates_per_person)
    DALYs_rate = numpy.dot(simulation.state[:, : -1],
                           simulation.parameters.DALY_rates_per_person)
    return integrate.simps(DALYs_rate, simulation.t)


class TestDALYsQALYs(unittest.TestCase):
    def test_DALYs_QALYs(self):
        from .parameters import Parameters
        from .simulation import Simulation
        country = 'Nigeria'
        parameters = Parameters(country).mode()
        simulation = Simulation(parameters, '909090')
        self.assertTrue(numpy.isclose(
            integrate.simps(simulation.alive + simulation.dead, simulation.t)
            - simulation.DALYs,
            simulation.QALYs))
