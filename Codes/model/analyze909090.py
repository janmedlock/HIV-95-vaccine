'''
Analyze the 90-90-90 policy.
'''

import numpy

from . import cost_effectiveness
from . import datasheet
from . import effectiveness


def analyze909090(country):
    parameters = datasheet.Parameters(country)

    if numpy.isnan(parameters.cost_AIDS_recurring_constant):
        DALYs, QALYs = effectiveness.solve_and_get_effectiveness(
                '909090', parameters)
        DALYs_base, QALYs_base = effectiveness.solve_and_get_effectiveness(
                '909090', parameters)
        cost_ = cost_base = numpy.nan
    else:
        DALYs, QALYs, cost_ \
            = cost_effectiveness.solve_and_get_effectiveness_and_cost(
                '909090', parameters)

        DALYs_base, QALYs_base, cost_base \
            = cost_effectiveness.solve_and_get_effectiveness_and_cost(
                'base', parameters)

    CE_stats = cost_effectiveness.get_cost_effectiveness_stats(
        DALYs, QALYs, cost_,
        DALYs_base, QALYs_base, cost_base,
        parameters)

    print('{}'.format(country))
    cost_effectiveness.print_cost_effectiveness_stats(
        *(CE_stats + (parameters, )))

    return (country, ((DALYs, QALYs, cost_),
                      (DALYs_base, QALYs_base, cost_base),
                      CE_stats))
