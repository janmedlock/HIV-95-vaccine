#!/usr/bin/python3
'''
Map the 90-90-90 results.
'''

import pickle
import warnings

from matplotlib import cm
from matplotlib import pyplot
import numpy
# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

import mapplot
import mapplot.cmap
import model


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
    b = max(max(relative_effectiveness), 0.225)
    m.choropleth(countries, 100 * relative_effectiveness,
                 vmin = 100 * a,
                 vmax = 100 * b,
                 cmap = 'Oranges')

    cbar = m.colorbar(
        label = 'Proportion of DALYs Averted (Compared to Status Quo)',
        format = '%g%%')

    m.tighten(aspect_adjustment = 1.35)

    m.label(countries)

    m.savefig('909090effectiveness.pdf')

    return m


def plot_cost(countries, cost, cost_base):
    # Drop nans
    ix = numpy.isfinite(cost)
    countries = numpy.compress(ix, countries)
    cost = numpy.compress(ix, cost)
    cost_base = numpy.compress(ix, cost_base)

    relative_cost = (cost - cost_base) / cost_base

    a = min(min(relative_cost), -0.5)
    b = max(max(relative_cost), 4)

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

    m.savefig('909090cost.pdf')

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
    b = min(max(max(ICER), 3), 10)
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
        # cticklabels.append(str(cmax))
        cticklabels.append('≥{:g}'.format(cmax))
    cbar.set_ticks(cticks)
    cbar.set_ticklabels(cticklabels)

    m.tighten(aspect_adjustment = 1.35)

    labels = ('Cost Saving',
              'Very Cost Effective',
              'Cost Effective',
              'Above Threshold')
    X = (0.11, 0.17, 0.29, 0.58)
    y = 0.22
    C = (colors[0], colors[3], colors[5], colors[7])
    for (l, x, c) in zip(labels, X, C):
        m.fig.text(x, y, l,
                   fontdict = dict(size = 5,
                                   color = c,
                                   weight = 'bold'),
                   verticalalignment = 'center',
                   horizontalalignment = 'left')

    m.label(countries)

    m.savefig('909090ICER.pdf')

    return m


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    effectiveness = []
    effectiveness_base = []
    cost = []
    cost_base = []
    ICER = []
    for c in countries:
        r = results[c]

        stats = model.get_effectiveness_and_cost(r.t,
                                                 r.state,
                                                 r.target,
                                                 r.parameters)
        stats_base = model.get_effectiveness_and_cost(r.t,
                                                      r.state_base,
                                                      r.target_base,
                                                      r.parameters)
        stats_inc = model.get_cost_effectiveness_stats(*(stats + stats_base),
                                                       r.parameters)

        # DALYs
        effectiveness.append(stats[0])
        effectiveness_base.append(stats_base[0])

        cost.append(stats[-1])
        cost_base.append(stats_base[-1])

        # In DALYs.
        ICER.append(stats_inc[3])

    plot_effectiveness(countries, effectiveness, effectiveness_base)
    plot_cost(countries, cost, cost_base)
    plot_ICER(countries, ICER)

    pyplot.show()


if __name__ == '__main__':
    _main()
