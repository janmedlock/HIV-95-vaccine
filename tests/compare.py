#!/usr/bin/python3
'''
Run the 90-90-90 policies for one country.
'''

import sys

sys.path.append('..')
import model


def _main(parallel = True):
    country = 'South Africa'
    parameters = model.parameters.Parameters(country).mode()
    targets = [model.target.StatusQuo(), model.target.UNAIDS90()]
    results = {}
    for target in targets:
        target_ = str(target)
        results[target_] = model.simulation.Simulation(parameters, target)
        print('{}: {:g} DALYs'.format(target_, results[target_].DALYs))
    return results


if __name__ == '__main__':
    results = _main()
