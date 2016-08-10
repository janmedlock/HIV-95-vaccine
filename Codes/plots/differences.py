#!/usr/bin/python3
'''
Plot differences for samples from uncertainty analysis.

.. todo:: Clean up.
'''

import operator
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
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


# Pairs (baseline, baseline + vaccine)
targets = [model.targets.all_[i : i + 2]
           for i in range(0, len(model.targets.all_), 2)]


def _get_plot_info(country, targs, stat):
    scale = None
    percent = False
    units = ''

    if stat == 'infected':
        label = 'PLHIV'
        scale = 1e6
    elif stat == 'prevalence':
        label = 'Prevelance'
        percent = True
    elif stat == 'incidence_per_capita':
        label = 'Incidence\n(per M per y)'
        scale = 1e-6
        units = ''
    elif stat == 'AIDS':
        label = 'AIDS'
    elif stat == 'dead':
        label = 'HIV-Related\nDeaths'
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    
    with model.results.samples.open_(country, targs[0]) as results:
        v_base = numpy.asarray(getattr(results, stat))
    with model.results.samples.open_(country, targs[1]) as results:
        v_intv = numpy.asarray(getattr(results, stat))

    data = v_base - v_intv
    # data = (v_base - v_intv) / v_base

    if percent:
        scale = 1 / 100
        units = '%%'
    elif scale is None:
        vmax = numpy.max(data)
        if vmax > 1e6:
            scale = 1e6
            units = 'M'
        elif vmax > 1e3:
            scale = 1e3
            units = 'k'
        else:
            scale = 1
            units = ''

    return (data, label, scale, units)


def _plot_cell(ax, country, targs, stat,
               country_label = None,
               attr_label = None):
    '''
    .. todo:: Do a better job with making the lower ylim 0.
    '''
    data, label, scale, unit = _get_plot_info(country, targs, stat)

    # Drop infinite data.
    ix = numpy.all(numpy.isfinite(data), axis = 0)
    q, C = common.getpercentiles(data[:, ix])
    col = ax.pcolormesh(common.t[ix], q / scale, C,
                        cmap = common.cmap_percentile,
                        shading = 'gouraud')
    if numpy.all(q > 0):
        ax.set_ylim(bottom = 0)

    tick_interval = 10
    a = int(numpy.floor(common.t[0]))
    b = int(numpy.ceil(common.t[-1]))
    ticks = range(a, b, tick_interval)
    if ((b - a) % tick_interval) == 0:
        ticks = list(ticks) + [b]
    ax.set_xticks(ticks)
    ax.set_xlim(a, b)

    ax.grid(True, which = 'both', axis = 'both')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    # One minor tick between major ticks.
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_major_formatter(common.UnitsFormatter(unit))
    ax.grid(True, which = 'both', axis = 'both')

    country_str = common.get_country_label(country)
    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(label, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(label, size = 'medium')
    return col


def plot_selected():
    for targs in targets:
        baseline = targs[0]
        print(baseline)
        fig = pyplot.figure(figsize = (8.5, 11))
        # Bottom row is colorbar.
        nrows = len(common.effectiveness_measures) + 1
        ncols = len(common.countries_to_plot)
        legend_height_ratio = 1 / 3
        gs = gridspec.GridSpec(nrows, ncols,
                               height_ratios = ((1, ) * (nrows - 1)
                                                + (legend_height_ratio, )))
        for (col, country) in enumerate(common.countries_to_plot):
            print('\t', country)
            attr_label = 'ylabel' if (col == 0) else None
            for (row, attr) in enumerate(common.effectiveness_measures):
                print('\t\t', attr)
                country_label = 'title' if (row == 0) else None
                ax = fig.add_subplot(gs[row, col])
                _plot_cell(ax,
                           country,
                           targs,
                           attr,
                           country_label = country_label,
                           attr_label = attr_label)
                if row != nrows - 2:
                    for l in ax.get_xticklabels():
                        l.set_visible(False)
                    ax.xaxis.offsetText.set_visible(False)

        ax = fig.add_subplot(gs[-1, :])
        colorbar.ColorbarBase(ax,
                              cmap = common.cmap_percentile,
                              norm = colors.Normalize(vmin = 0, vmax = 100),
                              orientation = 'horizontal',
                              label = 'Percentile',
                              format = '%g%%')

        fig.tight_layout()
        fileroot = '{}_{}'.format(common.get_filebase(),
                                  str(baseline).replace(' ', '_'))
        common.savefig(fig, '{}.pdf'.format(fileroot))
        common.savefig(fig, '{}.png'.format(fileroot))


def plot_all():
    countries = common.all_regions_and_countries

    for targs in targets:
        baseline = targs[0]
        print(baseline)
        filename = '{}_{}_all.pdf'.format(common.get_filebase(),
                                          baseline.replace(' ', '_'))
        with backend_pdf.PdfPages(filename) as pdf:
            nrows = len(common.effectiveness_measures) + 1
            ncols = 1
            legend_height_ratio = 1 / 3
            gs = gridspec.GridSpec(nrows, ncols,
                                   height_ratios = ((1, ) * (nrows - 1)
                                                    + (legend_height_ratio, )))
            for (i, country) in enumerate(common.countries_to_plot):
                print('\t', country)
                fig = pyplot.figure(figsize = (8.5, 11))
                title = common.get_country_label(country)
                try:
                    for (row, attr) in enumerate(common.effectiveness_measures):
                        print('\t\t', attr)
                        country_label = 'title' if (row == 0) else None
                        ax = fig.add_subplot(gs[row, 0])
                        _plot_cell(ax,
                                   country,
                                   targs,
                                   attr,
                                   country_label = country_label,
                                   attr_label = 'ylabel')
                        if row != nrows - 2:
                            for l in ax.get_xticklabels():
                                l.set_visible(False)
                            ax.xaxis.offsetText.set_visible(False)
                except FileNotFoundError:
                    pass
                else:
                    fig.tight_layout()
                    pdf.savefig(fig)
                finally:
                    pyplot.close(fig)


if __name__ == '__main__':
    plot_selected()
    # plot_all()

    # pyplot.show()
