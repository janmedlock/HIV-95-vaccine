#!/usr/bin/python3


if __name__ == '__main__':
    import sys
    sys.path.append('..')

    import model


    country = 'Nigeria'

    print(country)

    parameters = model.Parameters(country)

    t, state = model.solve('909090', parameters)

    QALYs, cost = model.get_CE_stats(t, state, '909090', parameters)

    QALYs_base, cost_base = model.solve_and_get_CE_stats('base', parameters)

    incremental_QALYs, incremental_cost, ICER = model.get_incremental_CE_stats(
        QALYs, cost, QALYs_base, cost_base, parameters)

    model.print_incremental_CE_stats(incremental_QALYs, incremental_cost, ICER,
                                     parameters)

    model.plot_solution(t, state, '909090', parameters)
