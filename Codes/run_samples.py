#!/usr/bin/python3

import pickle

from matplotlib import pylab

import model


samplesfile = 'samples.pkl'

if __name__ == '__main__':
    country = 'Nigeria'

    with open(samplesfile, 'rb') as fd:
        samples = pickle.load(fd)

    parametersamples = model.ParameterSample.from_samples(country, samples)

    multisim = model.MultiSim(parametersamples, '909090')

    # for s in multisim.simulations:
    #     p = ax.plot(s.t, s.prevalence)
    #     ax.plot(s.baseline.t, s.baseline.prevalence, linestyle = ':',
    #             color = p[0].get_color())
    for s in (multisim.baseline, multisim):
        y = getattr(s, 'infected')
        p = pylab.plot(multisim.t, numpy.median(y, axis = 0),
                       linewidth = 2, zorder = 2)
        a, b = numpy.percentile(y, [2.5, 97.5], axis = 0)
        pylab.fill_between(multisim.t, a, b, color = p[0].get_color(),
                           alpha = 0.3)

    pylab.show()
