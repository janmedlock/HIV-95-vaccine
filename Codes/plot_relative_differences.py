#!/usr/bin/python3

import warnings

from matplotlib import cm
from matplotlib import colorbar
from matplotlib import colors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

import model


countries_to_plot = (
    'Global',
    'India',
    'Nigeria',
    'Rwanda',
    'South Africa',
    'Uganda',
    'United States of America',
)


def getpercentiles(x):
    p = numpy.linspace(0, 100, 101)
    q = numpy.percentile(x, p, axis = 0)
    C = numpy.outer(p, numpy.ones(numpy.shape(x)[1]))
    return (q, C)


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'


def cmap_reflected(cmap_base):
    if cmap_base.endswith('_r'):
        cmap_base_r = cmap_base[ : -2]
    else:
        cmap_base_r = cmap_base + '_r'
    cmaps = (cmap_base_r, cmap_base)
    cmaps_ = [cm.get_cmap(c) for c in cmaps]
    def cfunc(k):
        def f(x):
            return numpy.where(x < 0.5,
                               cmaps_[0]._segmentdata[k](2 * x),
                               cmaps_[1]._segmentdata[k](2 * (x - 0.5)))
        return f
    cdict = {k: cfunc(k) for k in ('red', 'green', 'blue')}
    return colors.LinearSegmentedColormap(cmap_base + '_reflected', cdict)


cmap_base = 'afmhot'
cmap = cmap_reflected(cmap_base)


def plotcell(ax, tx,
             xlabel = None, ylabel = None, title = None):
    t, x = tx

    # percent == True
    scale = 1 / 100

    a = numpy.asarray(x['Status Quo'])
    b = numpy.asarray(x['90–90–90'])
    d = numpy.ma.divide(a - b, a)
    q, C = getpercentiles(d)
    col = ax.pcolormesh(t + 2015, q / scale, C, cmap = cmap)

    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    ax.grid(True, which = 'both', axis = 'both')
    ax.set_xticks([2015, 2025, 2035])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.yaxis.set_major_formatter(PercentFormatter())
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'medium')
    if title is not None:
        ax.set_title(title, size = 'medium')
    return col


def plot_selected():
    fig = pyplot.figure(figsize = (8.5, 11))
    # Bottom row is colorbar.
    nrow = len(countries_to_plot) + 1
    ncol = 4
    # Colorbar is shorter than the others.
    cbar_height = 1 / 3
    gs = gridspec.GridSpec(nrow, ncol,
                           height_ratios = [1] * (nrow - 1) + [cbar_height])
    for (i, country) in enumerate(countries_to_plot):
        with model.results.Results(country) as results:
            print(country)
            if country == 'United States of America':
                ylabel = 'United States'
            else:
                ylabel = country


            ax = fig.add_subplot(gs[i, 0])
            plotcell(ax,
                     results.getfield('infected'),
                     ylabel = ylabel,
                     title = ('People Living with HIV\n(M)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 1])
            plotcell(ax,
                     results.getfield('AIDS'),
                     title = ('People with AIDS\n(1000s)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 2])
            plotcell(ax,
                     results.getfield('incidence_per_capita'),
                     title = ('HIV Incidence\n(per M people per y)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 3])
            plotcell(ax,
                     results.getfield('prevalence'),
                     title = ('HIV Prevelance\n'
                              if (i == 0) else None))

    ax = fig.add_subplot(gs[-1, :])
    colorbar.ColorbarBase(ax,
                          cmap = cmap,
                          norm = colors.Normalize(vmin = 0, vmax = 100),
                          orientation = 'horizontal',
                          label = 'Percentile',
                          format = '%g%%')

    fig.tight_layout()

    fig.savefig('relative_differences.pdf')
    fig.savefig('relative_differences.png')


if __name__ == '__main__':
    plot_selected()

    pyplot.show()
