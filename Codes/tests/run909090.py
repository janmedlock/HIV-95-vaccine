#!/usr/bin/python3
'''
Run the 90-90-90 policies for one country.
'''

import sys

sys.path.append('..')
import model


def _main(parallel = True):
    country = 'Nigeria'
    parameters = model.Parameters(country)

    results = {}
    for k in ('baseline', '909090', '909090+50-5', '909090+50-10'):
        results[k] = model.Simulation(country, k,
                                      run_baseline = False,
                                      parameters = parameters)
        print('{}: {:g} DALYs'.format(k, results[k].DALYs))


if __name__ == '__main__':
    _main()
