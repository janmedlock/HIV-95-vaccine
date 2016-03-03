#!/usr/bin/python3

'''
Map the 90-90-90 results.
'''

import pickle

import numpy
from matplotlib import pyplot
from matplotlib import colors as mcolors

import mapplot

import seaborn


def _main():
    results = pickle.load(open('analyze909090.pkl', 'rb'))
    countries, values = zip(*results.items())

    colors = seaborn.color_palette('Paired', 8)
    # Reorder: move last two to the front.
    colors = colors[6 : ] + colors[ : 6]
    # From min to 0, colors[0] -> colors[1];
    # from 0 to 1,   colors[2] -> colors[3];
    # from 1 to 3,   colors[4] -> colors[5];
    # from 3 to max, colors[6] -> colors[7].
    # Make sure the min is at most 0.
    # Make sure the max is at least 3.
    a = min(min(values), 0)
    b = max(max(values), 3)
    # Map [a, b] to [0, 1]
    def f(x):
        return (x - a) / (b - a)
    # Which colors to use: x, y0, y1.
    clist = []
    if a < 0:
        clist.append((f(a), colors[0], colors[0]))
    clist.append((f(0), colors[1], colors[2]))
    clist.append((f(1), colors[3], colors[4]))
    clist.append((f(3), colors[5], colors[6]))
    if b > 3:
        clist.append((f(b), colors[7], colors[7]))
    cdict = {k: [(x, c1[i], c2[i]) for (x, c1, c2) in clist]
             for (i, k) in enumerate(('red', 'green', 'blue'))}

    cmap = mcolors.LinearSegmentedColormap('CEthresholds', cdict)

    pyplot.figure()
    m = mapplot.Basemap()
    m.choropleth(countries, values,
                 vmin = a, vmax = b,
                 cmap = cmap)
    cbar = pyplot.colorbar(orientation = 'horizontal',
                           shrink = 0.8)
    cbar.set_label('ICER (GDP per capita per DALY averted)')
    cticks = [0, 1, 3]
    cmin = numpy.ceil(numpy.min(values))
    cmax = numpy.floor(numpy.max(values))
    if cmin < 0:
        cticks.insert(0, cmin)
    if cmax > 3:
        cticks.append(cmax)
    cbar.set_ticks(cticks)

    pyplot.show()


if __name__ == '__main__':
    _main()
