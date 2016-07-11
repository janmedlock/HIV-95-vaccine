'''
Generate, save and load parameter samples.
'''

import os.path

from . import parameters
from . import picklefile


samplesfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '../samples.pkl')


def load():
    samples = picklefile.load(samplesfile)
    print('Loaded {} samples.'.format(len(samples)))
    return samples


def generate(nsamples):
    samples = parameters.Parameters.generate_samples(nsamples)
    print('Generated {} samples.'.format(len(samples)))
    picklefile.dump(samples, samplesfile)
    return samples
