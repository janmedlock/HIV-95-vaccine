#!/usr/bin/python3
'''
Test :meth:`model.parameters.Parameters.sample`.
'''


import sys

sys.path.append('..')
import model


if __name__ == '__main__':
    country = 'South Africa'
    nsamples = 2

    print(country)

    parameters = model.parameters.Parameters(country)
    target = model.target.UNAIDS90()

    samples = parameters.sample(nsamples)

    multisim = model.simulation.MultiSim(samples, target)
