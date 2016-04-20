#!/usr/bin/python3

import pickle
import warnings

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn


data = results['South Africa']
t = data.t
k = 'prevalence'
x = numpy.vstack(getattr(data.baseline, k))
y = numpy.vstack(getattr(data, k))
z = x - y

m = numpy.median(z, axis = 0)
p = numpy.linspace(0, 100, 101)
q = numpy.percentile(z, p, axis = 0)
C = numpy.outer(2 * numpy.abs(p / 100 - 0.5), numpy.ones(numpy.shape(z)[1]))

pyplot.pcolormesh(t, q, C, cmap = 'afmhot')
    




pyplot.show()
