#!/usr/bin/python3
'''
Map the prevalence at different times.
'''

from matplotlib import colors as mcolors
from matplotlib import pyplot
import numpy
import pandas

import model
import mapplot


def _main():
    data = model.read_all_initial_conditions()

    countries = data.index

    # People with HIV.
    nHIV = data.iloc[:, 1 : ].sum(1)
    pHIV = nHIV / data.sum(1)

    m = mapplot.Basemap()

    m.choropleth(countries, 100 * pHIV,
                 norm = mcolors.LogNorm(vmin = 100 * min(pHIV),
                                        vmax = 100 * max(pHIV)),
                 cmap = 'Purples')

    cbar = pyplot.colorbar(format = '%g%%',
                           orientation = 'horizontal',
                           fraction = 0.2,
                           pad = 0,
                           shrink = 0.8,
                           panchor = False)
    cbar.set_label('Initial Prevalence')

    w, h = m.fig.get_size_inches()
    extent = m.ax.get_extent()
    aspect = (extent[3] - extent[2]) / (extent[1] - extent[0]) * (1 + 0.35)
    m.fig.set_size_inches(w, w * aspect, forward = True)

    mapplot.pyplot.show()

    return m


if __name__ == '__main__':
    _main()
