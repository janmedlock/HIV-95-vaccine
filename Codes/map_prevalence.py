#!/usr/bin/python3
'''
Make an animated map of the prevalence at different times.
'''

import pickle

from matplotlib import colors as mcolors
from matplotlib import pyplot
import numpy

import mapplot


def _main(frames_per_year = 12, years_per_second = 2):
    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    prevalence = []
    for c in countries:
        r = results[c]
        prevalence.append(r[k909090].prevalence)
    prevalence = numpy.asarray(prevalence).T

    fig = pyplot.figure()
    m = mapplot.Basemap()

    # Initial frame for linking.
    fig0 = pyplot.figure()
    m0 = mapplot.Basemap()

    for z in (m, m0):
        z.tighten(aspect_adjustment = 1.35)

    t = results[countries[0]][k909090].t
    freq_ = (len(t) - 1) / (t[-1] - t[0])
    skip = max(int(freq_ / frames_per_year), 1)
    data = 100 * prevalence[: : skip]
    T = results[countries[0]][k909090].t[: : skip] + 2015

    cmap = 'afmhot_r'
    vmin = max(data.min(), 0.1)
    vmax = data.max()
    norm = mcolors.LogNorm(vmin = vmin, vmax = vmax)
    label_coords = (-120, -20)

    ani = m.choropleth_animate(countries, T, data,
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
        if len(ticklabels) > 0:
            ticklabels[0] = '≤{}'.format(ticklabels[0].get_text())
            cbar.ax.set_xticklabels(ticklabels)

    X, Y = label_coords
    m0.text_coords(X, Y, str(int(T[0])),
                   fontdict = dict(size = 20,
                                   weight = 'bold'),
                   horizontalalignment = 'left')

    m0.savefig('map_prevalence.pdf')

    ani.save('map_prevalence.mp4',
             fps = frames_per_year * years_per_second,
             dpi = 300,
             extra_args = ('-vcodec', 'libx264'))

    m.show()


if __name__ == '__main__':
    _main()
