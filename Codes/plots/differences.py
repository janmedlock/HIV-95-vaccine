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


targets = model.targets.all_


def _data_getter(results, country, attr):
    def f(target):
        return numpy.asarray(getattr(results[country][target], attr))
    return f
    

def _get_plot_info(results, country, targs, stat, skip_global = False):
    scale = None
    percent = False
    data_getter = _data_getter(results, country, stat)

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
    
    if (country == 'Global') and skip_global:
        t = results[common.countries_to_plot[-1]][targs[0]].t
        data = None
    else:
        t = results[country][targs[0]].t
        v_base, v_intv = map(data_getter, targs)
        data = v_base - v_intv
        # data = (v_base - v_intv) / v_base

    if percent:
        scale = 1 / 100
        unit = '%%'
    elif scale is None:
        vmax = numpy.max(data)
        if vmax > 1e6:
            scale = 1e6
            unit = 'M'
        elif vmax > 1e3:
            scale = 1e3
            unit = 'k'
        else:
            scale = 1
            unit = ''

    return (data, t, label, scale, unit)


def _plot_cell(ax, results, country, targs, stat,
               country_label = None,
               attr_label = None,
               skip_global = False):
    '''
    .. todo:: Do a better job with making the lower ylim 0.
    '''
    data, t, label, scale, unit = _get_plot_info(results, country,
                                                 targs, stat,
                                                 skip_global = skip_global)

    if not (country == 'Global' and skip_global):
        # Drop infinite data.
        ix = numpy.all(numpy.isfinite(data), axis = 0)
        q, C = common.getpercentiles(data[:, ix])
        col = ax.pcolormesh(t[ix], q / scale, C,
                            cmap = common.cmap_percentile,
                            shading = 'gouraud')
        if numpy.all(q > 0):
            ax.set_ylim(bottom = 0)
    else:
        col = None

    tick_interval = 10
    a = int(numpy.floor(t[0]))
    b = int(numpy.ceil(t[-1]))
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

    country_str = common.country_label_replacements.get(country,
                                                        country)
    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(label, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(label, size = 'medium')
    return col


def plot_selected(results, skip_global = False):
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
                           results,
                           country,
                           targs,
                           attr,
                           country_label = country_label,
                           attr_label = attr_label,
                           skip_global = skip_global)
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
                                  baseline.replace(' ', '_'))
        common.savefig(fig, '{}.pdf'.format(fileroot))
        common.savefig(fig, '{}.png'.format(fileroot))


def plot_all(results):
    countries = ['Global'] + sorted(model.get_country_list())

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
                title = common.country_label_replacements.get(country,
                                                              country)
                try:
                    for (row, attr) in enumerate(common.effectiveness_measures):
                        print('\t\t', attr)
                        country_label = 'title' if (row == 0) else None
                        ax = fig.add_subplot(gs[row, 0])
                        _plot_cell(ax,
                                   results,
                                   country,
                                   targs,
                                   attr,
                                   country_label = country_label,
                                   attr_label = 'ylabel',
                                   skip_global = skip_global)
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
    with model.results.samples.Cache() as results:
        plot_selected(results, skip_global = True)
        # plot_all(results)

    # pyplot.show()
