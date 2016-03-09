#!/usr/bin/python3

'''
Test :mod:`model.simulation`.
'''


import sys

sys.path.append('..')
import model


def _main():
    country = 'Nigeria'

    print(country)

    parameters = model.Parameters(country)

    solution = model.solve('909090', parameters, t_end = 10)

    stats = model.get_CE_stats(*solution, '909090', parameters)

    stats_base = model.solve_and_get_CE_stats('base', parameters)

    incremental_stats = model.get_incremental_CE_stats(*stats,
                                                       *stats_base,
                                                       parameters)

    model.print_incremental_CE_stats(*incremental_stats,
                                     parameters)

    model.plot_solution(*solution, '909090', parameters)


if __name__ == '__main__':
    _main()
