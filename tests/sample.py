#!/usr/bin/python3
'''
Test :meth:`model.parameters.Parameters.sample`.
'''


import sys

from matplotlib import pyplot
import seaborn

sys.path.append('..')
import model


if __name__ == '__main__':
    country = 'South Africa'
    nsamples = 2

    parameters = model.parameters.Parameters(country)
    target = model.target.UNAIDS90()
    samples = parameters.sample(nsamples)
    multisim = model.simulation.MultiSim(samples, target)

    pyplot.plot(model.simulation.t, multisim.new_infections.T)
    pyplot.ylabel('New infections')
    pyplot.show()
