#!/usr/bin/python3
'''
Test the :mod:`model.optimization`.
'''

import sys

sys.path.append('..')
import model


def _main():
    country = 'Nigeria'

    # 0 is just cost.
    # inf is just QALYs.
    # Other values are multiples of per-capita GDP.
    cost_effectiveness_threshold = 1

    (targs,
     incremental_net_benefit) = model.optimization.net_benefit.maximize(
         country,
         cost_effectiveness_threshold,
         method = 'cobyla',
         debug = True)

    print('target values = {}'.format(targs))

    print('incremental net benefit = {:g} QALYs'.format(
        incremental_net_benefit))

    parameters = model.Parameters('Nigeria')

    CE_stats = model.solve_and_get_cost_effectiveness_stats(targs, parameters)

    model.print_cost_effectiveness_stats(*(CE_stats + (parameters, )))


if __name__ == '__main__':
    _main()
