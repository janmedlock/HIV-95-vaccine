#!/usr/bin/python3
'''
Plot relative differences for samples from uncertainty analysis.
'''

import os.path
import sys

from matplotlib import colorbar
from matplotlib import colors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


def plotcell(ax, tx,
             xlabel = None, ylabel = None, title = None):
    t, x = tx

    # percent == True
    scale = 1 / 100

    a = numpy.asarray(x['Status Quo'])
    b = numpy.asarray(x['90–90–90'])
    d = numpy.ma.divide(a - b, a)
    q, C = common.getpercentiles(d)
    col = ax.pcolormesh(t, q / scale, C, cmap = common.cmap,
                        shading = 'gouraud')

    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(data_start_year, int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.yaxis.set_major_formatter(common.PercentFormatter())
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
    nrow = len(common.countries_to_plot) + 1
    ncol = 4
    # Colorbar is shorter than the others.
    cbar_height = 1 / 3
    gs = gridspec.GridSpec(nrow, ncol,
                           height_ratios = [1] * (nrow - 1) + [cbar_height])
    for (i, country) in enumerate(common.countries_to_plot):
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
                          cmap = common.cmap,
                          norm = colors.Normalize(vmin = 0, vmax = 100),
                          orientation = 'horizontal',
                          label = 'Percentile',
                          format = '%g%%')

    fig.tight_layout()

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


if __name__ == '__main__':
    plot_selected()

    pyplot.show()
