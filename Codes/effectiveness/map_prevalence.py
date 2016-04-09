#!/usr/bin/python3
'''
Make maps of the prevalence at different times.
'''

import pickle
import sys

from matplotlib import colors as mcolors
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

sys.path.append('..')
import mapplot


k909090 = ('909090', 0)
kbaseline = ('baseline', 0)
# cmap = 'afmhot_r'
cmap = 'YlOrRd'
norm = mcolors.LogNorm
label_coords = (-120, -20)
ticks = ticker.LogLocator(10, [1, 2, 5])
title = 'Prevalence'
height = 0.28
pad = 0.035
cpad = 0.05
aspect = 1.5


def animation(prevalence, vmin, vmax, norm,
              frames_per_year = 12, years_per_second = 2):
    fig = pyplot.figure()
    m = mapplot.Basemap()

    m.tighten(aspect_adjustment = 1.35)

    countries = prevalence.columns

    freq_ = (len(t) - 1) / (t[-1] - t[0])
    skip = max(int(freq_ / frames_per_year), 1)
    data = prevalence.iloc[: : skip].as_matrix()
    T = prevalence.index[: : skip]

    ani = m.choropleth_animate(countries, T + 2015, 100 * data,
                               cmap = cmap,
                               norm = norm(vmin = 100 * vmin,
                                           vmax = 100 * vmax),
                               vmin = 100 * vmin,
                               vmax = 100 * vmax,
                               label_coords = label_coords)

    cbar = m.colorbar(label = 'Prevalence',
                      format = '%g%%',
                      ticks = ticks)
    ticklabels = cbar.ax.get_xticklabels()
    if len(ticklabels) > 0:
        ticklabels[0] = '≤{}'.format(ticklabels[0].get_text())
        ticklabels[-1] = '≥{}'.format(ticklabels[-1].get_text())
        cbar.ax.set_xticklabels(ticklabels)

    ani.save('map_prevalence.mp4',
             fps = frames_per_year * years_per_second,
             dpi = 300,
             extra_args = ('-vcodec', 'libx264'))


def plot(prevalence, vmin, vmax, norm):
    T = [0, 10, 20]

    fig = pyplot.figure()

    countries = prevalence.columns

    data = prevalence.loc[T]

    for i in range(len(T)):
        if i < len(T) - 1:
            h = height
            b = 1 - height - (height + pad) * i
        else:
            h = 1 - (height + pad) * (len(T) - 1)
            b = 0

        m = mapplot.Basemap(rect = (0, b, 1, h),
                            anchor = (0.5, 1))

        mappable = m.choropleth(countries, 100 * data.iloc[i],
                                cmap = cmap,
                                norm = norm(100 * vmin,
                                            100 * vmax),
                                vmin = 100 * vmin,
                                vmax = 100 * vmax)

        X, Y = label_coords
        m.text_coords(X, Y, str(int(T[i] + 2015)),
                      fontdict = dict(size = 20,
                                      weight = 'bold'),
                      horizontalalignment = 'left')

    cbar = fig.colorbar(mappable,
                        label = title,
                        format = '%g%%',
                        ticks = ticks,
                        orientation = 'horizontal',
                        fraction = 0.2,
                        pad = cpad,
                        shrink = 0.8,
                        panchor = False)
    ticklabels = cbar.ax.get_xticklabels()
    if len(ticklabels) > 0:
        ticklabels[0] = '≤{}'.format(ticklabels[0].get_text())
        ticklabels[-1] = '≥{}'.format(ticklabels[-1].get_text())
        cbar.ax.set_xticklabels(ticklabels)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    fig.savefig('map_prevalence.pdf')
    fig.savefig('map_prevalence.png')



if __name__ == '__main__':
    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    t = results[countries[0]][k909090].t

    prevalence = pandas.DataFrame(columns = countries,
                                  index = t)
    for c in countries:
        prevalence[c] = results[c][k909090].prevalence

    vmin = max(prevalence.min().min(), 0.005)
    vmax = min(prevalence.max().max(), 0.2)

    # plot(prevalence, vmin, vmax, norm)
    animation(prevalence, vmin, vmax, norm)

    pyplot.show()
