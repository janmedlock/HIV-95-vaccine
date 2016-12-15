#!/usr/bin/python3
'''
Map the initial proportion of the population with HIV.
'''

import os.path
import sys

from matplotlib import colors
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
import mapplot
sys.path.append('..')
import model


def _main():
    data = model.datasheet.InitialConditions.get_all()

    countries = data.columns

    nHIV = data.iloc[1 :].sum(0)
    n = data.sum(0)
    prevalence = nHIV / n
    for (k, v) in prevalence.items():
        print('{}: {:g}%'.format(k, 100 * v))

    # vmin = prevalence.min()
    # vmax = prevalence.max()
    vmin = 0.0005
    vmax = 0.25

    cmap = 'YlOrRd'
    norm = colors.LogNorm
    ticks = ticker.LogLocator(10, [1, 2.5, 5])
    fig = pyplot.figure(figsize = (common.width_2column, 3))
    m = mapplot.Basemap()
    m.choropleth(countries, 100 * prevalence,
                 cmap = cmap,
                 norm = norm(vmin = 100 * vmin,
                             vmax = 100 * vmax),
                 vmin = 100 * vmin,
                 vmax = 100 * vmax)
    cbar = m.colorbar(label = '2015 HIV Prevalence',
                      format = '%g%%',
                      ticks = ticks)

    ticklabels = cbar.ax.get_xticklabels()
    if prevalence.min() < vmin:
        ticklabels[0].set_text(r'$\leq\!$' + ticklabels[0].get_text())
    if prevalence.max() > vmax:
        ticklabels[-1].set_text(r'$\geq\!$' + ticklabels[-1].get_text())
    cbar.ax.set_xticklabels(ticklabels)
    cbar.ax.tick_params(labelsize = pyplot.rcParams['font.size'])

    m.tighten(aspect_adjustment = 1.35)

    common.savefig(m.fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(m.fig, '{}.png'.format(common.get_filebase()))

    m.show()


if __name__ == '__main__':
    _main()
