#!/usr/bin/python3
'''
Plot differences for samples from uncertainty analysis.
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

import seaborn


def plotcell(ax, tx,
             scale = 1, percent = False,
             xlabel = None, ylabel = None, title = None):
    t, x = tx

    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(max(x) for x in stats.values()) > 1e6:
            scale = 1e6
        else:
            scale = 1e3

    a = numpy.asarray(x['Status Quo'])
    b = numpy.asarray(x['90–90–90'])
    d = a - b
    q, C = common.getpercentiles(d)
    col = ax.pcolormesh(t + 2015, q / scale, C, cmap = common.cmap,
                        shading = 'gouraud')

    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    ax.grid(True, which = 'both', axis = 'both')
    ax.set_xticks([2015, 2025, 2035])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
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
                     scale = 1e6,
                     ylabel = ylabel,
                     title = ('People Living with HIV\n(M)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 1])
            plotcell(ax,
                     results.getfield('AIDS'),
                     scale = 1e3,
                     title = ('People with AIDS\n(1000s)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 2])
            plotcell(ax,
                     results.getfield('incidence_per_capita'),
                     scale = 1e-6,
                     title = ('HIV Incidence\n(per M people per y)'
                              if (i == 0) else None))

            ax = fig.add_subplot(gs[i, 3])
            plotcell(ax,
                     results.getfield('prevalence'),
                     percent = True,
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


def plot_all():
    countries = ['Global'] + sorted(model.get_country_list())

    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for (i, country) in enumerate(countries):
                if country == 'United States of America':
                    title = 'United States'
                else:
                    title = country

                fig, axes = pyplot.subplots(4,
                                            figsize = (11, 8.5),
                                            sharex = True,
                                            squeeze = True)

                try:
                    plotcell(axes[0],
                             results.getfield('infected'),
                             scale = 1e6,
                             ylabel = 'People Living with HIV\n(M)',
                             title = title)

                    plotcell(axes[1],
                             results.getfield('AIDS'),
                             scale = 1e3,
                             ylabel = 'People with AIDS\n(1000s)')

                    plotcell(axes[2],
                             results.getfield('incidence_per_capita'),
                             scale = 1e-6,
                             ylabel = 'HIV Incidence\n(per M people per y)')

                    plotcell(axes[3],
                             results.getfield('prevalence'),
                             percent = True,
                             ylabel = 'HIV Prevelance\n')
                except FileNotFoundError:
                    pass
                else:
                    fig.tight_layout()
                    pdf.savefig(fig)
                finally:
                    pyplot.close(fig)
                    break

if __name__ == '__main__':
    plot_selected()

    # plot_all()

    pyplot.show()
