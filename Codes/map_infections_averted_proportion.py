#!/usr/bin/python3
'''
Make an animated map of the infections averted (proportion) at different times.
'''

import pickle

from matplotlib import colors as mcolors
from matplotlib import pyplot
import numpy

import model
import mapplot


def _main(every = 20):
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    infections_averted = []
    for c in countries:
        r = results[c]
        infections_averted.append((r.solution_base.new_infections
                                   - r.solution.new_infections)
                                  / r.solution_base.new_infections)
    infections_averted = numpy.asarray(infections_averted).T

    fig = pyplot.figure()
    m = mapplot.Basemap()

    # Initial frame for linking.
    fig0 = pyplot.figure()
    m0 = mapplot.Basemap()

    for z in (m, m0):
        z.tighten(aspect_adjustment = 1.35)

    data = 100 * infections_averted[: : every]
    T = results[countries[0]].solution.t[: : every] + 2015

    cmap = 'viridis'
    vmin = min(data.min(), 0)
    vmax = data.max()
    label_coords = (-120, -20)

    ani = m.choropleth_animate(countries, T, data,
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
            label = 'Infections Averted (Compared to Status Quo)',
            format = '%g%%')

    X, Y = label_coords
    m0.text_coords(X, Y, str(int(T[0])),
                   fontdict = dict(size = 20,
                                   weight = 'bold'),
                   horizontalalignment = 'left')

    m0.savefig('map_infections_averted_proportion.pdf')

    speed = 2  # years per second.
    ani.save('map_infections_averted_proportion.mp4',
             fps = speed / (T[1] - T[0]),
             dpi = 300,
             extra_args = ('-vcodec', 'libx264'))

    m.show()


if __name__ == '__main__':
    _main()