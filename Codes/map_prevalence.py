#!/usr/bin/python3
'''
Make an animated map of the prevalence at different times.
'''

import pickle

from matplotlib import animation
from matplotlib import colors as mcolors
import numpy

import model
import mapplot


def _main():
    results = pickle.load(open('analyze909090.pkl', 'rb'))
    countries, values = zip(*results.items())
    prevalence, stats, stats_base, stats_inc = map(numpy.array, zip(*values))

    every = 20
    t = prevalence[0, 0, : : every]
    prevalence = prevalence[:, 1, : : every].T

    m = mapplot.Basemap()

    m.tighten(aspect_adjustment = 1.35)

    a = max(prevalence.min(), 1e-4)
    b = prevalence.max()

    m.choropleth_preinit(countries,
                         t + 2015, 100 * prevalence,
                         norm = mcolors.LogNorm(vmin = 100 * a,
                                                vmax = 100 * b),
                         label_coords = (-120, -20),
                         cmap = 'afmhot_r')

    cbar = m.colorbar(label = 'Prevalence',
                      format = '%g%%')

    ani = animation.FuncAnimation(m.fig, m.choropleth_update,
                                  frames = len(prevalence),
                                  init_func = m.choropleth_init,
                                  repeat = False,
                                  blit = True)

    # 10 years per second.
    ani.save('prevalence.mp4', fps = 10 / (t[1] - t[0]),
             dpi = 300, extra_args = ('-vcodec', 'libx264'))

    # m.show()


if __name__ == '__main__':
    _main()
