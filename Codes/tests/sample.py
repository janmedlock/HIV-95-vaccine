#!/usr/bin/python3

import sys

sys.path.append('..')
import model


if __name__ == '__main__':
    country = 'Nigeria'
    nsamples = 2

    print(country)

    parameters = model.Parameters(country)

    samples = parameters.sample(nsamples)

    multisim = model.MultiSim(samples, '909090')
