'''
Generate, save and load parameter samples.

.. todo:: Do I need to generate a random quantile for transmission_rate?
'''

import os.path
import pickle

from . import parameters


samplesfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '../samples.pkl')


def load():
    with open(samplesfile, 'rb') as fd:
        samples = pickle.load(fd)
    print('Loaded {} samples.'.format(len(samples)))
    return samples


def generate(nsamples):
    samples = parameters.Parameters.generate_samples(nsamples)
    print('Generated {} samples.'.format(len(samples)))
    with open(samplesfile, 'wb') as fd:
        pickle.dump(samples, fd)
    return samples
