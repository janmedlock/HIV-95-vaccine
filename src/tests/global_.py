#!/usr/bin/python3
'''
Test :mod:`model.global_`.

This requires data from the simulation runs.
'''

import sys

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy
import seaborn

sys.path.append('..')
import model


countries_to_plot = ('Global', )


def getstats(x):
    avg = numpy.median(x, axis = 0)
    CIlevel = 0.5
    CI = numpy.percentile(x,
                          [100 * CIlevel / 2, 100 * (1 - CIlevel / 2)],
                          axis = 0)
    # avg = numpy.mean(x, axis = 0)
    # std = numpy.std(x, axis = 0, ddof = 1)
    # CI = [avg + std, avg - std]
    return (avg, CI)


def plotcell(ax, results, attr):
    if attr == 'infected':
        ylabel = 'People Living with HIV'
        scale = 1e6
        ytickappend = 'M'
    elif attr == 'AIDS':
        ylabel = 'People with AIDS'
        scale = 1e6
        ytickappend = 'M'
    elif attr == 'incidence_per_capita':
        ylabel = 'HIV Incidence\n(per M people per y)'
        scale = 1e-6
        ytickappend = ''
    elif attr == 'prevalence':
        ylabel = 'HIV Prevelance\n'
        scale = 1e-2
        ytickappend = '%'
    else:
        raise ValueError("Unknown attr '{}'!".format(attr))

    t = model.simulation.t
    x = getattr(results, attr)
    avg, CI = getstats(x)
    lines = ax.plot(t, avg / scale, label = target,
                    zorder = 2)
    ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                    color = lines[0].get_color(),

    ax.set_ylabel(ylabel)
    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    a = int(t[0])
    b = int(t[-1])
    c = 10
    if (b - a) % c == 0:
        b += c
    ax.set_xticks(range(a, b, c))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter(
        '{{x:g}}{}'.format(ytickappend)))


if __name__ == '__main__':
    target = model.target.StatusQuo()

    results = model.results.load('Global', target)

    fig, axes = pyplot.subplots(1, 4,
                                sharex = True)
    plotcell(axes[0], results, 'infected')
    plotcell(axes[1], results, 'AIDS')
    plotcell(axes[2], results, 'incidence_per_capita')
    plotcell(axes[3], results, 'prevalence')
    fig.tight_layout()
    pyplot.show()
