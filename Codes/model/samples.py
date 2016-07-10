'''
Generate, save and load parameter samples.
'''

import os.path
import pickle

from . import parameters
from . import xzpickle


samplesfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '../samples.pkl.xz')


def load():
    samples = xzpickle.load(samplesfile)
    print('Loaded {} samples.'.format(len(samples)))
    return samples


def generate(nsamples):
    samples = parameters.Parameters.generate_samples(nsamples)
    print('Generated {} samples.'.format(len(samples)))
    xzpickle.dump(samples, samplesfile)
    return samples
