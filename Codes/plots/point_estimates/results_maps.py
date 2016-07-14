#!/usr/bin/python3
'''
Map the 90--90--90 results.
'''

import os.path
import sys

from matplotlib import cm
from matplotlib import pyplot
import numpy

sys.path.append('..')
import common
import mapplot
import mapplot.cmap
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('../..')
from model import picklefile


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
                 cmap = 'Oranges')

    cbar = m.colorbar(
        label = 'Proportion of DALYs Averted (Compared to Status Quo)',
        format = '%g%%')

    m.tighten(aspect_adjustment = 1.35)

    m.label(countries)

    m.savefig('{}_effectiveness.pdf'.format(common.get_filebase()))

    return m


def plot_cost(countries, cost, cost_base):
    # Drop nans
    ix = numpy.isfinite(cost)
    countries = numpy.compress(ix, countries)
    cost = numpy.compress(ix, cost)
    cost_base = numpy.compress(ix, cost_base)

    relative_cost = (cost - cost_base) / cost_base

    a = min(min(relative_cost), 0)
    b = max(max(relative_cost), 5)

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
                 vmax = 100 * b,
                 cmap = cmap)

    cbar = m.colorbar(label = 'Proportion of Cost Added (Compared to Status Quo)',
                      format = '%g%%')

    m.tighten(aspect_adjustment = 1.35)

    m.label(countries)

    m.savefig('{}_cost.pdf'.format(common.get_filebase()))

    return m


def plot_ICER(countries, ICER):
    # Drop nans
    ix = numpy.isfinite(ICER)
    countries = numpy.compress(ix, countries)
    ICER = numpy.compress(ix, ICER)

    colors = seaborn.color_palette('Paired', 8)
    # Reorder: flip the last two and move to the front.
    colors = colors[7 : 5 : -1] + colors[ : 6]
    # From min to 0, colors[0] -> colors[1];
    # from 0 to 1,   colors[2] -> colors[3];
    # from 1 to 3,   colors[4] -> colors[5];
    # from 3 to max, colors[6] -> colors[7].
    # Make sure the min is at most 0.
    # Make sure the max is at least 3.
    a = min(numpy.floor(min(ICER)), 0)
    # b = max(max(ICER), 3)
    b = max(max(max(ICER), 3), 8)
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

    cbar = m.colorbar(label = 'ICER (GDP per capita per DALY averted)')

    cticks = [0, 1, 3]
    cticklabels = list(map(str, cticks))
    cmin = numpy.ceil(a)
    cmax = numpy.floor(b)
    if cmin < 0:
        cticks.insert(0, cmin)
        cticklabels.insert(0, '{:g}'.format(cmin))
    if cmax > 3:
        cticks.append(cmax)
        cticklabels.append('{:g}'.format(cmax))
        # cticklabels.append('≥{:g}'.format(cmax))
    cbar.set_ticks(cticks)
    cbar.set_ticklabels(cticklabels)

    m.tighten(aspect_adjustment = 1.35)

    labels = ('Very Cost Effective',
              'Cost Effective',
              'Above Threshold')
    X = (0.11, 0.27, 0.6)
    y = 0.22
    C = (colors[3], colors[5], colors[7])
    for (l, x, c) in zip(labels, X, C):
        m.fig.text(x, y, l,
                   fontdict = dict(size = 5,
                                   color = c,
                                   weight = 'bold'),
                   verticalalignment = 'center',
                   horizontalalignment = 'left')

    m.label(countries)

    m.savefig('{}_ICER.pdf'.format(common.get_filebase()))

    return m


def _main():
    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    results = picklefile.load('909090.pkl')

    countries = list(results.keys())
    effectiveness = []
    effectiveness_base = []
    cost = []
    cost_base = []
    ICER = []
    for c in countries:
        r = results[c]

        effectiveness.append(r[k909090].DALYs)
        effectiveness_base.append(r[kbaseline].DALYs)

        cost.append(r[k909090].cost)
        cost_base.append(r[kbaseline].cost)

        incremental_cost = r[k909090].cost - r[kbaseline].cost
        incremental_effectiveness = - (r[k909090].DALYs - r[kbaseline].DALYs)
        ICER_ = (incremental_cost
                 / incremental_effectiveness
                 / r[k909090].parameters.GDP_per_capita)

        ICER.append(ICER_)

    plot_effectiveness(countries, effectiveness, effectiveness_base)
    plot_cost(countries, cost, cost_base)
    plot_ICER(countries, ICER)

    # pyplot.show()


if __name__ == '__main__':
    _main()
