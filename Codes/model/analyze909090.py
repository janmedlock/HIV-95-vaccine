'''
Analyze the 90-90-90 policy.
'''

import numpy

from . import cost_effectiveness
from . import datasheet
from . import effectiveness
from . import simulation


def analyze909090(country):
    parameters = datasheet.Parameters(country)

    t, state = simulation.solve('909090', parameters, t_end = 50)
    new_infections = state[:, -1]
    prevalence = state[:, 1 : -2].sum(1) / state[:, : -2].sum(1)

    t_base, state_base = simulation.solve('base', parameters, t_end = 50)
    new_infections_base = state_base[:, -1]

    infections_averted = ((new_infections_base - new_infections)
                          / new_infections_base)

    if numpy.isfinite(parameters.cost_AIDS_recurring_constant):
        DALYs, QALYs, cost_ \
            = cost_effectiveness.solve_and_get_effectiveness_and_cost(
                '909090', parameters)
        DALYs_base, QALYs_base, cost_base \
            = cost_effectiveness.solve_and_get_effectiveness_and_cost(
                'base', parameters)
    else:
        DALYs, QALYs = effectiveness.solve_and_get_effectiveness(
                '909090', parameters)
        DALYs_base, QALYs_base = effectiveness.solve_and_get_effectiveness(
                'base', parameters)
        cost_ = cost_base = numpy.nan

    CE_stats = cost_effectiveness.get_cost_effectiveness_stats(
        DALYs, QALYs, cost_,
        DALYs_base, QALYs_base, cost_base,
        parameters)

    print('{}'.format(country))
    cost_effectiveness.print_cost_effectiveness_stats(
        *(CE_stats + (parameters, )))

    return (country, ((t, prevalence, infections_averted),
                      (DALYs, QALYs, cost_),
                      (DALYs_base, QALYs_base, cost_base),
                      CE_stats))
