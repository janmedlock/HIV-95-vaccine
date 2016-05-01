#!/usr/bin/python3
'''
Test :mod:`mapplot`.
'''


import os.path
import sys

import numpy
from matplotlib import pyplot

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import mapplot


def _main():
    countries = ('Canada', 'United States of America', 'Mexico',
                 'Guatemala', 'Honduras', 'El Salvador', 'Belize',
                 'Costa Rica', 'Nicaragua', 'Panama')

    data = numpy.random.uniform(size = (len(countries), 5))

    m = mapplot.Basemap()

    m.choropleth(countries, data[:, 0], zorder = 1)

    m.scatter(countries, c = data[:, 1], s = 40 * data[:, 2],
              zorder = 2)

    data_normalized = data[:, 0 : -1] / data[:, 0 : -1].sum(1)[:, numpy.newaxis]
    m.pies(countries, data_normalized,
           s = 40 * data[-1],
           wedgeprops = dict(linewidth = 0, zorder = 3))
    
    pyplot.show()


if __name__ == '__main__':
    _main()
