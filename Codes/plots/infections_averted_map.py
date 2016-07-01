#!/usr/bin/python3
'''
Make maps of the infections averted at different times.

.. todo:: Should read years from simulation output.
'''

import os.path
import pickle
import sys

from matplotlib import colors as mcolors
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))
import common
import mapplot
sys.path.append('..')
import model


cmap = 'viridis'
label_coords = (-120, -20)
ticks = ticker.MultipleLocator(10)
title = 'Reduction in New Infections (Compared to Status Quo)'
height = 0.4
pad = 0.035
cpad = 0.05
aspect = 1.05


def animation(infections_averted, vmin, vmax,
              frames_per_year = 12, years_per_second = 2):
    fig = pyplot.figure()
    m = mapplot.Basemap()

    m.tighten(aspect_adjustment = 1.35)

    countries = infections_averted.columns

    freq_ = (len(t) - 1) / (t[-1] - t[0])
    skip = max(int(freq_ / frames_per_year), 1)
    data = infections_averted.iloc[: : skip].as_matrix()
    T = infections_averted.index[: : skip]

    ani = m.choropleth_animate(countries, T, 100 * data,
                               cmap = cmap,
                               vmin = 100 * vmin,
                               vmax = 100 * vmax,
                               label_coords = label_coords)

    cbar = m.colorbar(
        label = title,
        format = '%g%%',
        ticks = ticks)

    ani.save('infections_averted_map.mp4',
             fps = frames_per_year * years_per_second,
             dpi = 300,
             extra_args = ('-vcodec', 'libx264'))


def plot(results, vmin, vmax):
    T = [10, 20]

    fig = pyplot.figure()

    countries = infections_averted.columns

    data = infections_averted.loc[T]

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
                                vmin = 100 * vmin,
                                vmax = 100 * vmax)

        X, Y = label_coords
        m.text_coords(X, Y, str(int(T[i])),
                      fontdict = dict(size = 20,
                                      weight = 'bold'),
                      horizontalalignment = 'left')

    cbar = fig.colorbar(mappable,
                        label = title,
                        format = '%g%%',
                        orientation = 'horizontal',
                        fraction = 0.2,
                        pad = cpad,
                        shrink = 0.8,
                        panchor = False,
                        ticks = ticks)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w, w * aspect, forward = True)

    fig.savefig('infections_averted_map.pdf')
    fig.savefig('infections_averted_map.png')


if __name__ == '__main__':
    countries = model.get_country_list()

    t_start = 2015
    t_end = 2035
    pts_per_year = 120
    t = numpy.linspace(t_start, t_end, (t_end - t_start) * pts_per_year + 1)
    infections_averted = pandas.DataFrame(columns = countries,
                                          index = t)

    for country in countries:
        with model.results.Results(country) as results:
            t, x = results.getfield('new_infections')
            a = numpy.asarray(x['Status Quo'])
            b = numpy.asarray(x['90–90–90'])
            d = numpy.ma.divide(a - b, a)
            m = numpy.median(d, axis = 0)
            infections_averted[country] = m.filled(0)

    vmin = min(infections_averted.min().min(), 0)
    vmax = max(infections_averted.max().max(), 0.6)

    plot(infections_averted, vmin, vmax)
    animation(infections_averted, vmin, vmax)

    # pyplot.show()
