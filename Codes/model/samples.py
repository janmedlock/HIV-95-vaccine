'''
Generate, save and load parameter samples.
'''

import os.path

import numpy

from . import parameters


samplesfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '../samples.npy')


def load():
    samples = numpy.load(samplesfile)
    print('Loaded {} samples.'.format(len(samples)))
    return samples


def generate(nsamples):
    samples = parameters.Parameters.generate_samples(nsamples)
    print('Generated {} samples.'.format(len(samples)))
    numpy.save(samplesfile, samples)
    return samples
