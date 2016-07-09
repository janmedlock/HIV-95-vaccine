#!/usr/bin/python3
'''
Map the initial proportion of the population with HIV.
'''

import os.path
import sys

from matplotlib import colors
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
        print(k, v)

    vmin = prevalence.min()
    vmax = prevalence.max()

    cmap = 'YlOrRd'
    norm = colors.LogNorm
    ticks = ticker.LogLocator(10, [1, 2, 5])
    m = mapplot.Basemap()
    m.choropleth(countries, 100 * prevalence,
                 cmap = cmap,
                 norm = norm(vmin = 100 * vmin,
                             vmax = 100 * vmax),
                 vmin = 100 * vmin,
                 vmax = 100 * vmax)
    cbar = m.colorbar(label = 'Prevalence',
                      format = '%g%%',
                      ticks = ticks)

    m.tighten()

    m.show()


if __name__ == '__main__':
    _main()
