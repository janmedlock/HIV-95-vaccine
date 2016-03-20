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

.. doctest::

   >>> from numpy import isclose
   >>> from scipy.integrate import simps
   >>> from model.simulation import Simulation
   >>> country = 'Nigeria'
   >>> simulation = Simulation(country, '909090')
   >>> assert isclose(simps(simulation.alive + simulation.dead, simulation.t)
   ...                - simulation.DALYs,
   ...                simulation.QALYs)
'''

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
