#!/usr/bin/python3
'''
Make an animated map of the prevalence at different times.
'''

from matplotlib import animation
from matplotlib import colors as mcolors
import numpy

import model
import mapplot


def _main():
    data = model.read_all_initial_conditions()

    countries = data.index

    # People with HIV.
    nHIV = data.iloc[:, 1 : ].sum(1)
    pHIV = nHIV / data.sum(1)

    data = numpy.row_stack(0.7 ** i * pHIV for i in range(11))

    m = mapplot.Basemap()

    m.tighten(aspect_adjustment = 1.35)

    m.choropleth_init(countries,
                      100 * data,
                      norm = mcolors.LogNorm(vmin = 100 * data.min(),
                                             vmax = 100 * data.max()),
                      cmap = 'Purples')

    cbar = m.colorbar(label = 'Prevalence',
                      format = '%g%%')

    ani = animation.FuncAnimation(m.fig, m.choropleth_update,
                                  frames = len(data),
                                  repeat = False)

    ani.save('prevalence.mp4', fps = 1, extra_args = ('-vcodec', 'libx264'))

    # m.show()


if __name__ == '__main__':
    _main()
