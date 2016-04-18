#!/usr/bin/python3

import pickle

import model


samplesfile = 'samples.pkl'

nsamples = 1000

if __name__ == '__main__':
    samples = model.Parameters.generate_samples(nsamples)

    print('Generated {} samples.'.format(len(samples)))

    with open(samplesfile, 'wb') as fd:
        pickle.dump(samples, fd)
