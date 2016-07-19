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

cmap = 'viridis'
label_coords = (-150, -30)
ticks = ticker.MultipleLocator(10)
title = 'Reduction in New Infections (Compared to {})'.format(baseline)
height = 0.28
pad = 0.035
cpad = 0.05
aspect = 1.45


def plot(infections_averted):
    vmin = min(infections_averted.min().min().min(), 0)
    vmax = infections_averted.max().max().max()

    norm = mcolors.Normalize(vmin = vmin, vmax = vmax)
    countries = infections_averted.index
    interventions = infections_averted.columns

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

        mappable = m.choropleth(countries,
                                100 * infections_averted.loc[:, intervention],
                                cmap = cmap,
                                norm = norm,
                                vmin = 100 * vmin,
                                vmax = 100 * vmax)

        label = common.get_target_label(intervention).replace('+', '\n+')
        X, Y = label_coords
        m.text_coords(X, Y, label,
                      fontdict = dict(size = 20,
                                      weight = 'bold'),
                      horizontalalignment = 'left',
                      verticalalignment = 'center')

    cbar = fig.colorbar(mappable,
                        label = title,
                        format = '%g%%',
                        orientation = 'horizontal',
                        fraction = 0.2,
                        pad = cpad,
                        shrink = 0.8,
                        panchor = False,
                        ticks = ticks)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


def _get_infections_averted():
    results = model.results.load_modes()

    countries = list(results.keys())
    countries.remove('Global')

    infections_averted = pandas.DataFrame(columns = interventions,
                                          index = countries)
    for country in countries:
        infections_baseline = results[country][baseline].new_infections
        for intervention in interventions:
            x = infections_baseline[time]
            y = results[country][intervention].new_infections[time]
            infections_averted.loc[country, intervention] = (x - y) / x

    return infections_averted


if __name__ == '__main__':
    infections_averted = _get_infections_averted()
    plot(infections_averted)
    pyplot.show()
