'''
Analyze the 90-90-90 policy.
'''

from . import CE_stats
from . import datasheet


def analyze909090(country):
    parameters = datasheet.Parameters(country)

    stats = CE_stats.solve_and_get_CE_stats('909090', parameters)

    stats_base = CE_stats.solve_and_get_CE_stats('base', parameters)

    stats_inc = CE_stats.get_incremental_CE_stats(*stats, *stats_base,
                                                  parameters)

    print('{}'.format(country))
    CE_stats.print_incremental_CE_stats(*stats_inc, parameters)

    return (country, (stats, stats_base, stats_inc))
