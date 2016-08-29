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

from . import simulation


def QALYs(sim):
    QALYs_rate = sim.state @ sim.parameters.QALY_rates_per_person
    return integrate.simps(QALYs_rate, simulation.t)


def DALYs(sim):
    DALYs_rate = sim.state @ sim.parameters.DALY_rates_per_person
    return integrate.simps(DALYs_rate, simulation.t)


class TestDALYsQALYs(unittest.TestCase):
    def test_DALYs_QALYs(self):
        from . import parameters
        from . import target
        country = 'Nigeria'
        params = parameters.Parameters(country).mode()
        targ = target.UNAIDS90()
        sim = simulation.Simulation(params, targ)
        self.assertTrue(numpy.isclose(
            integrate.simps(sim.alive + sim.dead, simulation.t) - sim.DALYs,
            sim.QALYs))
