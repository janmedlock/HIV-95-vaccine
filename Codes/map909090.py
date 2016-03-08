#!/usr/bin/python3

'''
Map the 90-90-90 results.
'''

import pickle

import numpy
from matplotlib import cm
from matplotlib import pyplot
import seaborn

import mapplot
import mapplot.cmap


def plot_effectiveness(countries, effectiveness, effectiveness_base):
    relative_effectiveness = ((effectiveness - effectiveness_base)
                              / effectiveness_base)

    fig = pyplot.figure()
    m = mapplot.Basemap()
    a = min(min(relative_effectiveness), 0)
    m.choropleth(countries, 100 * relative_effectiveness,
                 vmin = 100 * a,
                 cmap = 'Oranges')
    cbar = pyplot.colorbar(orientation = 'horizontal',
                           shrink = 0.8,
                           format = '%g%%')
    cbar.set_label('Effectiveness (DALYs averted), Relative to Baseline')


def plot_cost(countries, cost, cost_base):
    relative_cost = (cost - cost_base) / cost_base

    a = min(min(relative_cost), 0)
    b = max(max(relative_cost), 0)

    clist = []
    if a < 0:
        clist.append((a, 0, cm.Greens_r))
    if b > 0:
        clist.append((0, b, cm.Reds))
    cmap = mapplot.cmap.combine(clist)

    fig = pyplot.figure()
    m = mapplot.Basemap()
    m.choropleth(countries, 100 * relative_cost,
                 vmin = 100 * a,
                 cmap = cmap)
    cbar = pyplot.colorbar(orientation = 'horizontal',
                           shrink = 0.8,
                           format = '%g%%')
    cbar.set_label('Increased Cost, Relative to Baseline')


def plot_ICER(countries, ICER):
    colors = seaborn.color_palette('Paired', 8)
    # Reorder: flip the last two and move to the front.
    colors = colors[7 : 5 : -1] + colors[ : 6]
    # From min to 0, colors[0] -> colors[1];
    # from 0 to 1,   colors[2] -> colors[3];
    # from 1 to 3,   colors[4] -> colors[5];
    # from 3 to max, colors[6] -> colors[7].
    # Make sure the min is at most 0.
    # Make sure the max is at least 3.
    a = min(min(ICER), 0)
    b = max(max(ICER), 3)
    # Map [a, b] to [0, 1]
    def f(x):
        return (x - a) / (b - a)
    # Which colors to use: x, c0, c1.
    clist = []
    if a < 0:
        clist.append((f(a), f(0), colors[0], colors[1]))
    clist.append((f(0), f(1), colors[2], colors[3]))
    clist.append((f(1), f(3), colors[4], colors[5]))
    if b > 3:
        clist.append((f(3), f(b), colors[6], colors[7]))
    cmap = mapplot.cmap.build(clist)

    fig = pyplot.figure()
    m = mapplot.Basemap()
    m.choropleth(countries, ICER,
                 vmin = a, vmax = b,
                 cmap = cmap)
    cbar = pyplot.colorbar(orientation = 'horizontal',
                           shrink = 0.8)
    cbar.set_label('ICER (GDP per capita per DALY averted)')
    cticks = [0, 1, 3]
    cmin = numpy.ceil(numpy.min(ICER))
    cmax = numpy.floor(numpy.max(ICER))
    if cmin < 0:
        cticks.insert(0, cmin)
    if cmax > 3:
        cticks.append(cmax)
    cbar.set_ticks(cticks)


def _main():
    results = pickle.load(open('analyze909090.pkl', 'rb'))
    countries, values = zip(*results.items())
    effectiveness, cost, effectiveness_base, cost_base, ICER \
        = map(numpy.array, zip(*values))

    plot_effectiveness(countries, effectiveness, effectiveness_base)
    plot_cost(countries, cost, cost_base)
    plot_ICER(countries, ICER)

    pyplot.show()


if __name__ == '__main__':
    _main()
