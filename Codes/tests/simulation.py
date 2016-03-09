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

    t, state = model.solve('909090', parameters, t_end = 10)

    DALYs, QALYs, cost = model.get_effectiveness_and_cost(t, state,
                                                          '909090', parameters)

    DALYs_base, QALYs_base, cost_base \
        = model.solve_and_get_effectiveness_and_cost('base', parameters)

    CE_stats = model.get_cost_effectiveness_stats(
        DALYs, QALYs, cost,
        DALYs_base, QALYs_base, cost_base,
        parameters)

    model.print_cost_effectiveness_stats(*(CE_stats + (parameters, )))

    model.plot_solution(t, state, '909090', parameters)


if __name__ == '__main__':
    _main()
