#!/usr/bin/python3
'''
Run the 90-90-90 policies for one country.
'''

import sys

sys.path.append('..')
import model


def _main(parallel = True):
    country = 'Nigeria'
    parameters = model.Parameters(country).mode()

    results = {}
    for k in ('baseline', '909090'):
        results[k] = model.Simulation(parameters, k,
                                      run_baseline = False)
        print('{}: {:g} DALYs'.format(k, results[k].DALYs))


if __name__ == '__main__':
    _main()
