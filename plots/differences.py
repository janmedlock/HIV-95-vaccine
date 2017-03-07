#!/usr/bin/python3
'''
Plot differences for samples from uncertainty analysis.
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
import seaborn

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


# Pairs (baseline, baseline + vaccine)
targets = [model.target.all_[i : i + 2]
           for i in range(0, len(model.target.all_), 2)]


_cmap_base = 'cubehelix'
cmap = common.cmap_reflected(_cmap_base)


def _get_percentiles(x):
    p = numpy.linspace(0, 100, 101)
    # Plot the points near 50% last, so they show up clearest.
    # This gives [0, 100, 1, 99, 2, 98, ..., 48, 52, 49, 51, 50].
    M = len(p) // 2
    p_ = numpy.column_stack((p[ : M], p[-1 : -(M + 1) : -1]))
    p_ = p_.flatten()
    if len(p) % 2 == 1:
        p_ = numpy.hstack((p_, p[M]))
    q = numpy.percentile(x, p_, axis = 0)
    C = numpy.outer(p_, numpy.ones(numpy.shape(x)[1]))
    return (q, C)


def _plot_cell(ax, results, country, targets, stat,
               country_label = None, stat_label = None,
               space_to_newline = False):
    info = common.get_stat_info(stat)

    if ((results[targets[0]] is not None)
        and (results[targets[1]] is not None)):
        v_base = getattr(results[targets[0]], stat)
        v_intv = getattr(results[targets[1]], stat)
        data = v_base - v_intv
        # data = (v_base - v_intv) / v_base
        # Drop infinite data.
        ix = numpy.all(numpy.isfinite(data), axis = 0)
        q, C = _get_percentiles(data[:, ix])

        if info.scale is None:
            info.autoscale(data)
        if info.units is None:
            info.autounits(data)

        col = ax.pcolormesh(common.t[ix], q / info.scale, C,
                            cmap = cmap)
                            # shading = 'gouraud')

        # TODO: Do a better job with making the lower ylim 0.
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

        common.format_axes(ax, country, info, country_label, stat_label,
                           space_to_newline = space_to_newline)

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
            results = common.get_country_results(country, targs)
            for (row, stat) in enumerate(common.effectiveness_measures):
                ax = fig.add_subplot(gs[row, col])

                stat_label = 'ylabel' if ax.is_first_col() else None
                country_label = 'title' if ax.is_first_row() else None

                _plot_cell(ax, results, country, targs, stat,
                           country_label = country_label,
                           stat_label = stat_label)

        ax = fig.add_subplot(gs[-1, :])
        colorbar.ColorbarBase(ax,
                              cmap = cmap,
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
                                          str(baseline).replace(' ', '_'))
        with backend_pdf.PdfPages(filename) as pdf:
            nrows = len(common.effectiveness_measures) + 1
            ncols = 1
            legend_height_ratio = 1 / 3
            gs = gridspec.GridSpec(nrows, ncols,
                                   height_ratios = ((1, ) * (nrows - 1)
                                                    + (legend_height_ratio, )))
            for country in common.countries_to_plot:
                print('\t', country)
                results = common.get_country_results(country, targs)
                fig = pyplot.figure(figsize = (8.5, 11))
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = fig.add_subplot(gs[row, 0])

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, country, targs, stat,
                               country_label = country_label,
                               stat_label = stat_label,
                               space_to_newline = True)
                fig.tight_layout()
                pdf.savefig(fig)
                pyplot.close(fig)
                break


if __name__ == '__main__':
    plot_selected()
    pyplot.show()

    # plot_all()
