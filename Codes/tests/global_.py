#!/usr/bin/python3
'''
Test :mod:`model.global_`.

This requires data from the simulation runs in the directory './results'.
'''

import sys

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

# import seaborn
sys.path.append('../plots')
import seaborn_quiet as seaborn

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


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'


def plotcell(ax, results, attr):
    percent = False
    if attr == 'infected':
        ylabel = 'People Living with HIV\n(M)'
        scale = 1e6
    elif attr == 'AIDS':
        ylabel = 'People with AIDS\n(1000s)'
        scale = 1e3
    elif attr == 'incidence_per_capita':
        ylabel = 'HIV Incidence\n(per M people per y)'
        scale = 1e-6
    elif attr == 'prevalence':
        ylabel = 'HIV Prevelance\n'
        percent = True
    else:
        raise ValueError("Unknown attr '{}'!".format(attr))

    if percent:
        scale = 1 / 100

    t = results.t
    x = getattr(results, attr)
    avg, CI = getstats(x)
    lines = ax.plot(t, avg / scale, label = target,
                    zorder = 2)
    ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                    color = lines[0].get_color(),
                    alpha = 0.3)

    ax.set_ylabel(ylabel)
    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(int(t[0]), int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())


if __name__ == '__main__':
    target = model.targets.StatusQuo()

    results = model.results.Results('Global', str(target))

    fig, axes = pyplot.subplots(1, 4,
                                figsize = (8.5, 11),
                                sharex = True)
    plotcell(axes[0], results, 'infected')
    plotcell(axes[1], results, 'AIDS')
    plotcell(axes[2], results, 'incidence_per_capita')
    plotcell(axes[3], results, 'prevalence')
    fig.tight_layout()
    pyplot.show()
