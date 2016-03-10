#!/usr/bin/python3
'''
Map the initial prevalence.
'''

from matplotlib import colors as mcolors

import model
import mapplot


def _main():
    data = model.read_all_initial_conditions()

    countries = data.index

    # People with HIV.
    nHIV = data.iloc[:, 1 : ].sum(1)
    pHIV = nHIV / data.sum(1)

    m = mapplot.Basemap()

    a = max(pHIV.min(), 0.001)
    b = pHIV.max()

    m.choropleth(countries, 100 * pHIV,
                 norm = mcolors.LogNorm(vmin = 100 * a,
                                        vmax = 100 * b),
                 vmin = 100 * a,
                 vmax = 100 * b,
                 cmap = 'afmhot_r')

    cbar = m.colorbar(label = 'Initial Prevalence',
                      format = '%g%%')

    ticklabels = cbar.ax.get_xticklabels()
    ticklabels[0] = '≤{}'.format(ticklabels[0].get_text())
    cbar.ax.set_xticklabels(ticklabels)

    m.tighten(aspect_adjustment = 1.35)

    m.savefig('initial_prevalence.pdf')

    m.show()

    return m


if __name__ == '__main__':
    _main()
