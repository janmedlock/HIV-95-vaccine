#!/usr/bin/python3
'''
Test the :mod:`model.optimization`.
'''

import sys

sys.path.append('..')
import model


def _main(parallel = True, debug = True, **kwargs):
    country = 'Nigeria'

    parameters = model.Parameters(country).mode()

    # 0 is just cost.
    # inf is just DALYs.
    # Other values are multiples of per-capita GDP.
    cost_effectiveness_threshold = 1

    result = model.optimization.net_benefit.maximize(
        parameters,
        cost_effectiveness_threshold,
        parallel = parallel,
        debug = debug,
        **kwargs)

    targets, incremental_net_benefit = result

    print('target values = {}'.format(targets))
    print('incremental net benefit = {:g} DALYs'.format(
        incremental_net_benefit))


if __name__ == '__main__':
    _main(nruns = 1)
