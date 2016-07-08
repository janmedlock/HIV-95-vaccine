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

    targets = [model.targets.StatusQuo(),
               model.targets.UNAIDS90()]
    results = {}
    for target in targets:
        results[str(target)] = model.simulation.Simulation(parameters, target)
        print('{}: {:g} DALYs'.format(str(target), results[str(target)].DALYs))


if __name__ == '__main__':
    _main()
