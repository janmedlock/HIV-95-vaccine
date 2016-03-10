#!/usr/bin/python3
'''
Make an animated map of the prevalence at different times.
'''

import pickle

from matplotlib import animation
from matplotlib import colors as mcolors
from matplotlib import pyplot
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

    fig = pyplot.figure()
    m = mapplot.Basemap()

    # Initial frame for linking.
    fig0 = pyplot.figure()
    m0 = mapplot.Basemap()

    for z in (m, m0):
        z.tighten(aspect_adjustment = 1.35)

    data = 100 * infections_averted
    T = t + 2015
    cmap = 'viridis'
    vmin = 0
    vmax = max(data.max(), 50)
    label_coords = (-120, -20)

    m.choropleth_preinit(countries, T, data,
                         cmap = cmap,
                         vmin = vmin,
                         vmax = vmax,
                         label_coords = (-120, -20))

    m0.choropleth(countries, data[0],
                  cmap = cmap,
                  vmin = vmin,
                  vmax = vmax)

    for z in (m, m0):
        cbar = z.colorbar(
            label = 'Infections (Proportion Averted Below Baseline)',
            format = '%g%%')

    X, Y = label_coords
    m0.text_coords(X, Y, str(int(T[0])),
                   fontdict = dict(size = 20,
                                   weight = 'bold'),
                   horizontalalignment = 'left')

    m0.savefig('infections_averted.pdf')

    ani = animation.FuncAnimation(m.fig, m.choropleth_update,
                                  frames = len(infections_averted),
                                  init_func = m.choropleth_init,
                                  repeat = False,
                                  blit = True)

    # 10 years per second.
    ani.save('infections_averted.mp4', fps = 10 / (t[1] - t[0]),
             dpi = 300, extra_args = ('-vcodec', 'libx264'))

    m.show()


if __name__ == '__main__':
    _main()
