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
   >>> from model.datasheet import Parameters
   >>> from model.effectiveness import get_effectiveness
   >>> from model.simulation import solve
   >>> country = 'Nigeria'
   >>> parameters = Parameters(country)
   >>> t, state = solve('909090', parameters)
   >>> DALYs, QALYs = get_effectiveness(t, state, '909090', parameters)
   >>> assert isclose(DALYs, 8281790.7229896532)
   >>> assert isclose(QALYs, 957874221.35318017)
   >>> assert isclose(simps(state[:, : -1].sum(1), t) - DALYs, QALYs)
'''

import numpy
from scipy import integrate


def get_effectiveness(solution):
    # A component of Sphinx chokes on the '@'.
    # QALYs_rate = (solution.state[:, : -1]
    #               @ solution.parameters.QALY_rates_per_person)
    QALYs_rate = numpy.dot(solution.state[:, : -1],
                           solution.parameters.QALY_rates_per_person)
    QALYs = integrate.simps(QALYs_rate, solution.t)

    # A component of Sphinx chokes on the '@'.
    # DALYs_rate = (solution.state[:, : -1]
    #               @ solution.parameters.DALY_rates_per_person)
    DALYs_rate = numpy.dot(solution.state[:, : -1],
                           solution.parameters.DALY_rates_per_person)
    DALYs = integrate.simps(DALYs_rate, solution.t)

    return DALYs, QALYs


def solve_and_get_effectiveness(targs, parameters):
    from . import simulation
    solution = simulation.solve(targs, parameters)
    return get_effectiveness(solution)
