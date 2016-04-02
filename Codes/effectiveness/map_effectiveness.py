#!/usr/bin/python3
'''
Map the 90-90-90 results.
'''

import pickle
import sys
import warnings

from matplotlib import cm
from matplotlib import pyplot
from matplotlib import ticker
import numpy
# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

sys.path.append('..')
import mapplot
import mapplot.cmap


def plot_effectiveness(countries, effectiveness, effectiveness_base):
    # Drop nans
    ix = numpy.isfinite(effectiveness)
    countries = numpy.compress(ix, countries)
    effectiveness = numpy.compress(ix, effectiveness)
    effectiveness_base = numpy.compress(ix, effectiveness_base)

    relative_effectiveness = ((effectiveness_base - effectiveness)
                              / effectiveness_base)

    fig = pyplot.figure()
    m = mapplot.Basemap()

    a = min(min(relative_effectiveness), 0)
    b = max(max(relative_effectiveness), 0.6)
    m.choropleth(countries, 100 * relative_effectiveness,
                 vmin = 100 * a,
                 vmax = 100 * b,
                 cmap = 'viridis')

    cbar = m.colorbar(
        label = 'Reduction in DALYs',
        format = '%g%%',
        ticks = ticker.MultipleLocator(10))

    m.tighten(aspect_adjustment = 1.35)

    # m.label(countries)

    m.savefig('map_effectiveness.pdf')
    m.savefig('map_effectiveness.png')

    return m


def _main():
    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    effectiveness = []
    effectiveness_base = []
    for c in countries:
        r = results[c]

        effectiveness.append(r[k909090].DALYs)
        effectiveness_base.append(r[kbaseline].DALYs)


    plot_effectiveness(countries, effectiveness, effectiveness_base)

    # pyplot.show()


if __name__ == '__main__':
    _main()
