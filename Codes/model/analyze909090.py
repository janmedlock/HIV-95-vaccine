'''
Analyze the 90-90-90 policy.
'''

from . import CE_stats
from . import datasheet


def analyze909090(country):
    parameters = datasheet.Parameters(country)

    effectiveness, cost = CE_stats.solve_and_get_CE_stats(
        '909090', parameters)

    effectiveness_base, cost_base = CE_stats.solve_and_get_CE_stats(
        'base', parameters)

    effectiveness_inc, cost_inc, ICER = CE_stats.get_incremental_CE_stats(
        effectiveness, cost, effectiveness_base, cost_base, parameters)

    print('{}'.format(country))
    CE_stats.print_incremental_CE_stats(effectiveness_inc, cost_inc, ICER,
                                        parameters)

    return (country, (effectiveness, cost, effectiveness_base, cost_base, ICER))
