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
    state, stats, stats_base, stats_inc = map(numpy.array, zip(*values))

    every = 20
    t = state[0, 0, : : every]
    infections_averted = state[:, 2, : : every].T

    m = mapplot.Basemap()

    m.tighten(aspect_adjustment = 1.35)

    a = 0
    b = max(infections_averted.max(), 0.50)

    m.choropleth_preinit(countries,
                         t + 2015, 100 * infections_averted,
                         vmin = 100 * a,
                         vmax = 100 * b,
                         label_coords = (-120, -20),
                         cmap = 'viridis')

    cbar = m.colorbar(label = 'Infections (Proportion Averted Below Baseline)',
                      format = '%g%%')

    ani = animation.FuncAnimation(m.fig, m.choropleth_update,
                                  frames = len(infections_averted),
                                  init_func = m.choropleth_init,
                                  repeat = False,
                                  blit = True)

    # 10 years per second.
    ani.save('infections_averted.mp4', fps = 10 / (t[1] - t[0]),
             dpi = 300, extra_args = ('-vcodec', 'libx264'))

    # m.show()


if __name__ == '__main__':
    _main()
