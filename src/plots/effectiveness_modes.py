#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.
'''

import os.path
import sys

from matplotlib import lines
from matplotlib import pyplot
from matplotlib.backends import backend_pdf
import numpy
import seaborn
import tables

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


alpha0 = 0.9


def _plot_cell(ax, results, parameters, country, stat,
               plot_hist = True,
               country_label = None,
               country_short_name = True,
               stat_label = 'ylabel'):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    info = common.get_stat_info(stat)

    data = []
    for target in model.targets.all_:
        try:
            v = results[country][str(target)][stat]
        except tables.NoSuchNodeError:
            v = None
        data.append(v)
    if info.scale is None:
        info.autoscale(data)
    if info.units is None:
        info.autounits(data)

    if plot_hist and (parameters is not None):
        data_hist = common.data_hist_getter[stat](parameters)
        if data_hist is not None:
            data_hist = data_hist.dropna()
            if len(data_hist) > 0:
                ax.plot(data_hist.index, data_hist / info.scale,
                        label = 'Historical data',
                        zorder = 2,
                        **common.historical_data_style)

    for target in model.targets.all_:
        try:
            v = results[country][str(target)][stat]
        except tables.NoSuchNodeError:
            # Pop a style.
            next(ax._get_lines.prop_cycler)
        else:
            ax.plot(common.t, numpy.asarray(v) / info.scale,
                    label = common.get_target_label(target),
                    alpha = alpha0,
                    zorder = 1)

            # Make a dotted line connecting the end of the historical data
            # and the begining of the simulation.
            if (plot_hist and (parameters is not None)
                and (data_hist is not None) and (len(data_hist) > 0)):
                # Drop NaNs at the beginning of incidence.
                t = numpy.compress(numpy.isfinite(v), common.t)
                w = numpy.compress(numpy.isfinite(v), v)
                t = [data_hist.index[-1], t[0]]
                w = [data_hist.iloc[-1], w[0]]
                ax.plot(t, numpy.asarray(w) / info.scale,
                        color = 'black',
                        linestyle = 'dotted',
                        label = None,
                        alpha = alpha0,
                        zorder = 2)

    common.format_axes(ax, country, info, country_label, stat_label,
                       plot_hist = plot_hist,
                       country_short_name = country_short_name)


def _make_legend(fig, plot_hist = True):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    if plot_hist:
        handles.append(lines.Line2D([], [], **common.historical_data_style))
        labels.append('Historical data')
        # Blank spacer.
        handles.append(lines.Line2D([], [], linewidth = 0))
        labels.append(' ')
    for (t, c) in zip(model.targets.all_, colors):
        handles.append(lines.Line2D([], [], color = c, alpha = alpha0))
        labels.append(common.get_target_label(t))
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False)


def _plot_one(results, country, **kwargs):
    try:
        parameters = model.parameters.get_parameters(country)
    except KeyError:
        parameters = None

    with seaborn.color_palette(common.colors_paired):
        nrows = len(common.effectiveness_measures)
        ncols = 1
        fig, axes = pyplot.subplots(nrows, ncols,
                                    figsize = (8.5, 11),
                                    sharex = 'all', sharey = 'none')

        for (row, stat) in enumerate(common.effectiveness_measures):
            ax = axes[row]
            country_label = 'title' if ax.is_first_row() else None
            _plot_cell(ax, results, parameters, country, stat,
                       country_label = country_label,
                       country_short_name = False,
                       **kwargs)

        _make_legend(fig)

    fig.tight_layout(rect = (0, 0.055, 1, 1))

    return fig


def plot_one(country, **kwargs):
    with model.results.modes.open_() as results:
        return _plot_one(results, country, **kwargs)


def plot_all(**kwargs):
    with model.results.modes.open_() as results:
        regions_and_countries = results.keys()
        # Put regions first.
        regions = []
        for region in model.regions.all_:
            if region in regions_and_countries:
                regions.append(region)
                regions_and_countries.remove(region)
        # countries needs to be sorted by the name on graph.
        countries = sorted(regions_and_countries,
                           key = common.country_sort_key)
        regions_and_countries = regions + countries

        filename = '{}_all.pdf'.format(common.get_filebase())
        with backend_pdf.PdfPages(filename) as pdf:
            for region_or_country in regions_and_countries:
                print(region_or_country)
                fig = _plot_one(results, region_or_country, **kwargs)
                pdf.savefig(fig)
                pyplot.close(fig)


def plot_some(**kwargs):
    with model.results.modes.open_() as results:
        with seaborn.color_palette(common.colors_paired):
            ncols = len(common.countries_to_plot)
            nrows = len(common.effectiveness_measures)
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = (common.width_2column, 4.75),
                                        sharex = 'all', sharey = 'none')
            for (col, country) in enumerate(common.countries_to_plot):
                parameters = model.parameters.get_parameters(country)
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = axes[row, col]

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, parameters, country, stat,
                               country_label = country_label,
                               stat_label = stat_label,
                               plot_hist = False,
                               **kwargs)

            _make_legend(fig, plot_hist = False)

    fig.tight_layout(h_pad = 0.7, w_pad = 0,
                     rect = (0, 0.04, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_some()
    pyplot.show()

    # plot_all()
