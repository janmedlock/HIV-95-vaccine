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
import tables

sys.path.append(os.path.dirname(__file__))
import common
import mapplot
sys.path.append('..')
import model


baseline = model.target.StatusQuo()
interventions = (
    model.target.UNAIDS95(),
    model.target.Vaccine(treatment_target = model.target.StatusQuo()),
    model.target.Vaccine(treatment_target = model.target.UNAIDS95()))

baseline = str(baseline)
interventions = list(map(str, interventions))

time = 2035

scale = 0.01
title = 'Infections Averted (Compared to {})'.format(
    baseline)
vmin = 0.1 / scale
vmax = 0.9 / scale
norm = mcolors.Normalize(vmin = vmin, vmax = vmax)
cmap = 'plasma_r'
label_coords = (-130, -30)
height = 0.28
pad = 0.02
cpad = 0.05
aspect = 1.45


def plot(infections_averted):
    countries = infections_averted.index
    interventions = infections_averted.columns

    fig = pyplot.figure(figsize = (common.width_1_5column, 6))
    nrows = len(interventions)
    for (i, intv) in enumerate(interventions):
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
            infections_averted.loc[:, intv] / scale,
            cmap = cmap,
            norm = norm,
            vmin = vmin,
            vmax = vmax)

        label = common.get_target_label(intv)
        label = label.replace('_', ' ').replace('+', '\n+')
        X, Y = label_coords
        m.text_coords(
            X, Y, label,
            fontdict = dict(size = pyplot.rcParams['font.size'] + 3,
                            weight = 'bold'),
            horizontalalignment = 'center',
            verticalalignment = 'center')

    cbar = fig.colorbar(mappable,
                        label = title,
                        orientation = 'horizontal',
                        fraction = 0.2,
                        pad = cpad,
                        shrink = 0.8,
                        panchor = False,
                        format = common.PercentFormatter())
    # Try to work around ugliness from viewer bugs.
    cbar.solids.set_edgecolor('face')
    cbar.solids.drawedges = False

    ticklabels = cbar.ax.get_xticklabels()
    if infections_averted.min().min() < vmin * scale:
        ticklabels[0].set_text(r'$\leq\!$' + ticklabels[0].get_text())
    if infections_averted.max().max() > vmax * scale:
        ticklabels[-1].set_text(r'$\geq\!$' + ticklabels[-1].get_text())
    cbar.ax.set_xticklabels(ticklabels)
    cbar.ax.tick_params(labelsize = pyplot.rcParams['font.size'])

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))


def _get_infections_averted():
    with model.results.samples.stats.open_() as results:
        countries = list(results.keys())

        infections_averted = pandas.DataFrame(columns = interventions,
                                              index = countries)
        for country in countries:
            if model.regions.is_country(country):
                try:
                    x = results[country][baseline].new_infections.median[-1]
                    for intv in interventions:
                        y = results[country][intv].new_infections.median[-1]
                        infections_averted.loc[country, intv] = (x - y) / x
                except tables.exceptions.NoSuchNodeError:
                    pass
    return infections_averted


if __name__ == '__main__':
    infections_averted = _get_infections_averted()
    plot(infections_averted)
    pyplot.show()
