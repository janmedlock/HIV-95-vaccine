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


def _main(every = 20):
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    prevalence = []
    for c in countries:
        r = results[c]
        t = r.t[: : every]
        state = r.state[: : every]
        prevalence.append(state[:, 1 : -2].sum(1) / state[:, : -2].sum(1))
    prevalence = numpy.asarray(prevalence).T

    fig = pyplot.figure()
    m = mapplot.Basemap()

    # Initial frame for linking.
    fig0 = pyplot.figure()
    m0 = mapplot.Basemap()

    for z in (m, m0):
        z.tighten(aspect_adjustment = 1.35)

    data = 100 * prevalence
    T = t + 2015
    cmap = 'afmhot_r'
    vmin = max(data.min(), 0.1)
    vmax = data.max()
    norm = mcolors.LogNorm(vmin = vmin, vmax = vmax)
    label_coords = (-120, -20)

    m.choropleth_preinit(countries, T, data,
                         cmap = cmap,
                         norm = norm,
                         vmin = vmin,
                         vmax = vmax,
                         label_coords = label_coords)

    m0.choropleth(countries, data[0],
                  cmap = cmap,
                  norm = norm,
                  vmin = vmin,
                  vmax = vmax)

    for z in (m, m0):
        cbar = z.colorbar(label = 'Prevalence',
                          format = '%g%%')
        ticklabels = cbar.ax.get_xticklabels()
        ticklabels[0] = '≤{}'.format(ticklabels[0].get_text())
        cbar.ax.set_xticklabels(ticklabels)

    X, Y = label_coords
    m0.text_coords(X, Y, str(int(T[0])),
                   fontdict = dict(size = 20,
                                   weight = 'bold'),
                   horizontalalignment = 'left')

    m0.savefig('prevalence.pdf')

    ani = animation.FuncAnimation(m.fig, m.choropleth_update,
                                  frames = len(prevalence),
                                  init_func = m.choropleth_init,
                                  repeat = False,
                                  blit = True)
    # 2 years per second.
    ani.save('prevalence.mp4', fps = 2 / (t[1] - t[0]),
             dpi = 300, extra_args = ('-vcodec', 'libx264'))

    m.show()


if __name__ == '__main__':
    _main()
