#!/usr/bin/python3

import pickle

import model


samplesfile = 'samples.pkl'

if __name__ == '__main__':
    country = 'Nigeria'

    with open(samplesfile, 'rb') as fd:
        samples = pickle.load(fd)

    parametersamples = model.ParameterSample.from_samples(country, samples)

    multisim = model.MultiSim(parametersamples, '909090')
