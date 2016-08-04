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
import tables

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

scale = 1e-3
title = 'Infections per 1000 Averted (Compared to {})'.format(baseline)
vmin = 0.0025 / scale
vmax = 0.25 / scale
norm = mcolors.LogNorm(vmin = vmin, vmax = vmax)
cmap = common.cmap_scaled('magma_r', vmax = 0.85)
label_coords = (-130, -30)
height = 0.28
pad = 0.035
cpad = 0.05
aspect = 1.45


def plot(infections_per_capita_averted):
    countries = infections_per_capita_averted.index
    interventions = infections_per_capita_averted.columns

    fig = pyplot.figure()
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
            infections_per_capita_averted.loc[:, intv] / scale,
            cmap = cmap,
            norm = norm,
            vmin = vmin,
            vmax = vmax)

        label = common.get_target_label(intv)
        label = label.replace('_', ' ').replace('+', '\n+')
        X, Y = label_coords
        m.text_coords(X, Y, label,
                      fontdict = dict(size = 20,
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
                        ticks = ticker.LogLocator(subs = [1, 2.5, 5]),
                        format = ticker.LogFormatter(labelOnlyBase = False))

    ticklabels = cbar.ax.get_xticklabels()
    if infections_per_capita_averted.min().min() < vmin * scale:
        ticklabels[0].set_text('≤' + ticklabels[0].get_text())
    if infections_per_capita_averted.max().max() > vmax * scale:
        ticklabels[-1].set_text('≥' + ticklabels[-1].get_text())
    cbar.ax.set_xticklabels(ticklabels)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


def _get_infections_per_capita(country, target):
    try:
        with model.results.samples.open_(country, target) as results:
            alive = results.alive
            new_infections = results.new_infections
    except FileNotFoundError:
        print('{}, {} failed!'.format(country, target))
        return None
    else:
        person_years = integrate.trapz(alive, common.t)
        # exposure is number of 20-person-years lived.
        exposure = person_years / (common.t[-1] - common.t[0])
        infections_per_capita = (numpy.asarray(new_infections)[:, -1]
                                 / exposure)
        return numpy.median(infections_per_capita)


def _get_infections_per_capita_averted():
    countries = model.datasheet.get_country_list()
    infections_per_capita_averted = pandas.DataFrame(
        columns = interventions,
        index = countries)
    for country in countries:
        print(country)
        x = _get_infections_per_capita(country, baseline)
        if x is not None:
            for intv in interventions:
                y = _get_infections_per_capita(country, intv)
                if y is not None:
                    infections_per_capita_averted.loc[country, intv] = x - y
    return infections_per_capita_averted


if __name__ == '__main__':
    infections_per_capita_averted = _get_infections_per_capita_averted()
    plot(infections_per_capita_averted)
    pyplot.show()
