#!/usr/bin/python3
'''
Make maps of the infections averted at different times.
'''

import os.path
import sys

from matplotlib import colors as mcolors
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas
from scipy import integrate

sys.path.append(os.path.dirname(__file__))
import common
import mapplot
sys.path.append('..')
import model


baseline = model.targets.StatusQuo()
interventions = (
    model.targets.UNAIDS95(),
    model.targets.Vaccine(treatment_targets = model.targets.StatusQuo()),
    model.targets.Vaccine(treatment_targets = model.targets.UNAIDS95()))

baseline = str(baseline)
interventions = list(map(str, interventions))

time = 2035

cmap = common.cmap_scaled('magma', vmin = 0.12)
label_coords = (-150, -30)
ticklocator = ticker.LogLocator(base = 10, subs = [1, 2, 5])
tickformatter = ticker.LogFormatter(base = 10, labelOnlyBase = False)
scale = 1e-3
title = 'Infections per 1000 Averted (Compared to {})'.format(baseline)
height = 0.28
pad = 0.035
cpad = 0.05
aspect = 1.45


def plot(infections_averted_per_capita):
    # vmin = infections_averted_per_capita.min().min() / scale
    # vmax = infections_averted_per_capita.max().max() / scale
    vmin = 0.001 / scale
    vmax = 0.5 / scale

    norm = mcolors.LogNorm(vmin = vmin, vmax = vmax)
    countries = infections_averted_per_capita.index
    interventions = infections_averted_per_capita.columns

    fig = pyplot.figure()
    nrows = len(interventions)
    for (i, intervention) in enumerate(interventions):
        if i <  nrows - 1:
            h = height
            b = 1 - height - (height + pad) * i
        else:
            h = 1 - (height + pad) * (nrows - 1)
            b = 0

        m = mapplot.Basemap(rect = (0, b, 1, h),
                            anchor = (0.5, 1))

        mappable = m.choropleth(
            countries,
            infections_averted_per_capita.loc[:, intervention] / scale,
            cmap = cmap,
            norm = norm,
            vmin = vmin,
            vmax = vmax)

        label = common.get_target_label(intervention).replace('+', '\n+')
        X, Y = label_coords
        m.text_coords(X, Y, label,
                      fontdict = dict(size = 20,
                                      weight = 'bold'),
                      horizontalalignment = 'left',
                      verticalalignment = 'center')

    cbar = fig.colorbar(mappable,
                        label = title,
                        orientation = 'horizontal',
                        fraction = 0.2,
                        pad = cpad,
                        shrink = 0.8,
                        panchor = False,
                        ticks = ticklocator,
                        format = tickformatter)

    ticklabels = cbar.ax.get_xticklabels()
    if infections_averted_per_capita.min().min() < vmin * scale:
        ticklabels[0].set_text('≤' + ticklabels[0].get_text())
    if infections_averted_per_capita.max().max() > vmax * scale:
        ticklabels[-1].set_text('≥' + ticklabels[-1].get_text())
    cbar.ax.set_xticklabels(ticklabels)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


def _mean(x, t):
    return integrate.trapz(x, t) / (t[-1] - t[0])


def _get_infections_per_capita(result):
    '''
    Infections per capita.
    '''
    alive_avg = _mean(result.alive, result.t)
    return result.new_infections[-1] / alive_avg


def _get_infections_per_capita_averted():
    results = model.results.load_modes()

    countries = list(results.keys())
    countries.remove('Global')

    infections_per_capita_averted = pandas.DataFrame(columns = interventions,
                                                     index = countries)
    for country in countries:
        x = _get_infections_per_capita(results[country][baseline])
        for intv in interventions:
            y = _get_infections_per_capita(results[country][intv])
            infections_per_capita_averted.loc[country, intv] = x - y
    return infections_per_capita_averted


if __name__ == '__main__':
    infections_per_capita_averted = _get_infections_per_capita_averted()
    plot(infections_per_capita_averted)
    pyplot.show()
