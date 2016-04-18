#!/usr/bin/python3

import pickle

import model


samplesfile = 'samples.pkl'

nsamples = 10

if __name__ == '__main__':
    samples = model.Parameters.generate_samples(nsamples)

    with open(samplesfile, 'wb') as fd:
        pickle.dump(samples, fd)
