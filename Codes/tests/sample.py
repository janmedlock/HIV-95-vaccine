#!/usr/bin/python3
'''
Test :meth:`model.parameter.Parameter.sample`.
'''


import sys

sys.path.append('..')
import model


if __name__ == '__main__':
    country = 'South Africa'
    nsamples = 2

    print(country)

    parameters = model.parameters.Parameters(country)
    targets = model.targets.UNAIDS90()

    samples = parameters.sample(nsamples)

    multisim = model.multisim.MultiSim(samples, targets)
