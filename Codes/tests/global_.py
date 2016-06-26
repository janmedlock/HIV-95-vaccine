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

# Silence warnings from matplotlib trigged by seaborn.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
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


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'

cp = seaborn.color_palette('colorblind')
colors = {'Status Quo': cp[2],
          '90–90–90': cp[0]}

def plotcell(ax, tx,
             scale = 1, percent = False,
             title = None, legend = True):
    t, x = tx

    if percent:
        scale = 1 / 100

    for k in ('Status Quo', '90–90–90'):
        v = x[k]
        avg, CI = getstats(v)
        ax.plot(t, avg / scale, color = colors[k], label = k,
                zorder = 2)
        ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                        color = colors[k],
                        alpha = 0.3)

    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(int(t[0]), int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())
    if title is not None:
        ax.set_title(title, size = 'medium')
    if legend:
        ax.legend(loc = 'best')


if __name__ == '__main__':
    fig, axes = pyplot.subplots(1, 4,
                                figsize = (8.5, 11),
                                sharex = True,
                                squeeze = False)

    results = model.results.Results('Global')

    plotcell(axes[0, 0],
             results.getfield('infected'),
             scale = 1e6,
             legend = True,
             title = 'People Living with HIV\n(M)')

    plotcell(axes[0, 1],
             results.getfield('AIDS'),
             scale = 1e3,
             legend = False,
             title = 'People with AIDS\n(1000s)')

    plotcell(axes[0, 2],
             results.getfield('incidence_per_capita'),
             scale = 1e-6,
             legend = False,
             title = 'HIV Incidence\n(per M people per y)')

    plotcell(axes[0, 3],
             results.getfield('prevalence'),
             percent = True,
             legend = False,
             title = 'HIV Prevelance\n')

    fig.tight_layout()

    pyplot.show()
