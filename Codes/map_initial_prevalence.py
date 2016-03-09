#!/usr/bin/python3
'''
Map the prevalence at different times.
'''

from matplotlib import colors as mcolors
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

    m.colorbar(label = 'Initial Prevalence',
               format = '%g%%')

    m.tighten(aspect_adjustment = 1.35)

    m.savefig('initial_prevalence.pdf')

    m.show()

    return m


if __name__ == '__main__':
    _main()
