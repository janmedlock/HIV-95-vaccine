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

    (targets,
     incremental_net_benefit) = model.optimization.net_benefit.maximize(
         country,
         cost_effectiveness_threshold,
         method = 'cobyla',
         parallel = False,
         debug = True)

    print('target values = {}'.format(targets))

    print('incremental net benefit = {:g} DALYs'.format(
        incremental_net_benefit))


if __name__ == '__main__':
    _main()
