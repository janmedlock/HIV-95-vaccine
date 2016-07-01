#!/usr/bin/python3
'''
Run the 90-90-90 policies for one country.
'''

import sys

sys.path.append('..')
import model


def _main(parallel = True):
    country = 'South Africa'
    parameters = model.Parameters(country).mode()

    results = {}
    targets = {'Status Quo': model.TargetsStatusQuo,
               '90-90-90': model.Targets909090},
    for (k, v) in targets.items():
        results[k] = model.Simulation(parameters, v)
        print('{}: {:g} DALYs'.format(k, results[k].DALYs))


if __name__ == '__main__':
    _main()
