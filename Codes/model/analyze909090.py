from . import datasheet
from . import CE_stats


def analyze909090(country):
    print('{}'.format(country))

    parameters = datasheet.Parameters(country)

    incremental_effectiveness, incremental_cost, ICER \
        = CE_stats.solve_and_get_incremental_CE_stats('909090', parameters)

    CE_stats.print_incremental_CE_stats(incremental_effectiveness,
                                        incremental_cost,
                                        ICER,
                                        parameters)

    return ICER
