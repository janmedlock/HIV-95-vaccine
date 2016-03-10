'''
Compute cost-effectiveness.

.. doctest::

   >>> from numpy import isclose
   >>> from model.datasheet import Parameters
   >>> from model.cost_effectiveness import solve_and_get_cost_effectiveness_stats
   >>> country = 'Nigeria'
   >>> parameters = Parameters(country)
   >>> stats = solve_and_get_cost_effectiveness_stats('909090', parameters)
   >>> assert all(isclose(stats, (1842392.6202638801,
   ...                            2015631.942163229,
   ...                            9053869705.7548714,
   ...                            1.5341041609991664,
   ...                            1.4022511381257359)))
'''

import numpy
from scipy import integrate

from . import cost
from . import effectiveness
from . import simulation


def get_effectiveness_and_cost(t, state, targs, parameters):
    DALYs, QALYs = effectiveness.get_effectiveness(t, state, targs, parameters)

    cost_ = cost.get_cost(t, state, targs, parameters)

    return DALYs, QALYs, cost_


def solve_and_get_effectiveness_and_cost(targs, parameters):
    t, state = simulation.solve(targs, parameters)
    return get_effectiveness_and_cost(t, state, targs, parameters)


def get_cost_effectiveness_stats(DALYs, QALYs, cost_,
                                 DALYs_base, QALYs_base, cost_base,
                                 parameters):
    incremental_DALYs = DALYs_base - DALYs
    incremental_QALYs = QALYs - QALYs_base
    incremental_cost = cost_ - cost_base
    ICER_DALYs = (incremental_cost
                  / incremental_DALYs
                  / parameters.GDP_per_capita)
    ICER_QALYs = (incremental_cost
                  / incremental_QALYs
                  / parameters.GDP_per_capita)
    return (incremental_DALYs,
            incremental_QALYs,
            incremental_cost,
            ICER_DALYs,
            ICER_QALYs)


def solve_and_get_cost_effectiveness_stats(targs, parameters):
    DALYs, QALYs, cost_ = solve_and_get_effectiveness_and_cost(
        targs, parameters)

    DALYs_base, QALYs_base, cost_base = solve_and_get_effectiveness_and_cost(
        'base', parameters)

    return get_cost_effectiveness_stats(DALYs, QALYs, cost_,
                                        DALYs_base, QALYs_base, cost_base,
                                        parameters)


def print_cost_effectiveness_stats(incremental_DALYs, incremental_QALYs,
                                   incremental_cost, ICER_DALYs, ICER_QALYs,
                                   parameters):
    print('incremental effectiveness = {:g} DALYs'.format(
        incremental_DALYs))
    print('incremental effectiveness = {:g} QALYs'.format(
        incremental_QALYs))
    if numpy.isfinite(incremental_cost):
        print('incremental cost = {:g} USD'.format(incremental_cost))
        print('incremental cost = {:g} GDP per capita'.format(
            incremental_cost / parameters.GDP_per_capita))
        print('ICER = {:g} USD per DALY'.format(
            ICER_DALYs * parameters.GDP_per_capita))
        print('ICER = {:g} GDP per capita per DALY'.format(
            ICER_DALYs))
        print('ICER = {:g} USD per QALY'.format(
            ICER_QALYs * parameters.GDP_per_capita))
        print('ICER = {:g} GDP per capita per QALY'.format(
            ICER_QALYs))


def get_net_benefit(DALYs, QALYs, cost_, cost_effectiveness_threshold,
                    parameters, effectiveness_ = 'DALYs'):
    r'''Net benefit is

    .. math::
    
       N = E - \frac{C}{T G},

    where :math:`E` is `effectiveness`, :math:`C` is `cost`, :math:`T`
    is `cost_effectiveness_threshold`, and :math:`G` is
    :attr:`model.datasheet.Parameters.GDP_per_capita`.
    '''
    if effectiveness_ == 'DALYs':
        effectiveness_ = - DALYs
    elif effectiveness_ == 'QALYs':
        effectiveness_ = QALYs

    if cost_effectiveness_threshold == 0:
        # Just cost.
        net_benefit = - cost_
    elif cost_effectiveness_threshold == numpy.inf:
        # Just Effectiveness.
        net_benefit = effectiveness_
    else:
        net_benefit = (effectiveness_
                       - (cost_
                          / parameters.GDP_per_capita
                          / cost_effectiveness_threshold))

    return net_benefit


def solve_and_get_net_benefit(targs, cost_effectiveness_threshold, parameters):
    DALYs, QALYs, cost_ = solve_and_get_effectiveness_and_cost(targs,
                                                               parameters)
    return get_net_benefit(DALYs, QALYs, cost_, cost_effectiveness_threshold,
                           parameters)
