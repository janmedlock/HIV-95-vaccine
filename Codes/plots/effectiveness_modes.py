#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.
'''

import os.path
import sys

from matplotlib import gridspec
from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

# import seaborn
import seaborn_quiet as seaborn


def _get_plot_info(parameters, results, stat):
    data_hist = common.data_hist_getter[stat](parameters)

    data_sim = []
    for target in model.targets.all_:
        try:
            x = common.data_getter[stat](results[str(target)])
        except (KeyError, AttributeError):
            x = None
        data_sim.append(x)

    info = common.get_stat_info(stat)
    if info.scale is None:
        info.autoscale(data_sim)

    return (data_hist, data_sim, info)


def _plot_cell(ax, country, parameters, results, stat,
               plot_hist = True,
               country_label = None,
               attr_label = 'ylabel'):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    (data_hist, data_sim, info) = _get_plot_info(parameters, results, stat)

    # Plot historical data.
    if plot_hist and (data_hist is not None):
        data_hist = data_hist.dropna()
        if len(data_hist) > 0:
            ax.plot(data_hist.index, data_hist / info.scale,
                    label = 'Historical data',
                    zorder = 2,
                    **common.historical_data_style)

    # Plot simulation data.
    for (target, x) in zip(model.targets.all_, data_sim):
        if x is not None:
            ax.plot(common.t, numpy.asarray(x) / info.scale,
                    label = common.get_target_label(target),
                    alpha = 0.7,
                    zorder = 1)
            # Make a dotted line connecting the end of the historical data
            # and the begining of the simulation.
            if plot_hist and (data_hist is not None) and (len(data_hist) > 0):
                t_ = numpy.compress(numpy.isfinite(x), common.t)
                x_ = numpy.compress(numpy.isfinite(x), x)
                t_ = [data_hist.index[-1], t_[0]]
                x_ = [data_hist.iloc[-1], x_[0]]
                ax.plot(t_, numpy.asarray(x_) / info.scale,
                        color = 'black',
                        linestyle = 'dotted',
                        label = None,
                        alpha = 0.7,
                        zorder = 2)
        else:
            # Pop a style.
            next(ax._get_lines.prop_cycler)

    common.format_axes(ax, country, info, country_label, attr_label,
                       plot_hist = plot_hist)


def _make_legend(ax, plot_hist = True):
    ax.tick_params(labelbottom = False, labelleft = False)
    ax.grid(False)

    # Make legend at bottom.
    handles = []
    labels = []

    if plot_hist:
        handles.append(lines.Line2D([], [], **common.historical_data_style))
        labels.append('Historical data')

        # Blank spacer.
        handles.append(lines.Line2D([], [], linewidth = 0))
        labels.append(' ')

    colors = seaborn.color_palette()
    for (t, c) in zip(model.targets.all_, colors):
        handles.append(lines.Line2D([], [], color = c))
        labels.append(common.get_target_label(t))

    fig = ax.get_figure()
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


def _plot_country(country, results):
    fig = pyplot.figure(figsize = (8.5, 11))

    parameters = model.parameters.get_parameters(country)

    nrows = len(common.effectiveness_measures) + 1
    ncols = 1
    legend_height_ratio = 0.2
    gs = gridspec.GridSpec(nrows, ncols,
                           height_ratios = ((1, ) * (nrows - 1)
                                            + (legend_height_ratio, )))
    with seaborn.color_palette(common.colors_paired):
        for (row, attr) in enumerate(common.effectiveness_measures):
            ax = fig.add_subplot(gs[row, 0])
            country_label = 'title' if (row == 0) else None
            _plot_cell(ax, country, parameters, results, attr,
                       country_label = country_label)
            if row != nrows - 2:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)
        # Make legend at bottom.
        ax = fig.add_subplot(gs[-1, 0], axis_bgcolor = 'none')
        _make_legend(ax)

    fig.tight_layout()

    return fig


def plot_country(country):
    with model.results.modes.load() as results:
        return _plot_country(country, results[country])


def plot_somecountries():
    with model.results.modes.load() as results:
        fig = pyplot.figure(figsize = (8.5, 7.5))
        # Legend in tiny bottom row
        ncols = len(common.countries_to_plot)
        nrows = len(common.effectiveness_measures) + 1
        legend_height_ratio = 0.35
        gs = gridspec.GridSpec(nrows, ncols,
                               height_ratios = ((1, ) * (nrows - 1)
                                                + (legend_height_ratio, )))
        with seaborn.color_palette(common.colors_paired):
            for (col, country) in enumerate(common.countries_to_plot):
                parameters = model.parameters.get_parameters(country)
                attr_label = 'ylabel' if (col == 0) else None
                for (row, attr) in enumerate(common.effectiveness_measures):
                    ax = fig.add_subplot(gs[row, col])
                    country_label = 'title' if (row == 0) else None
                    _plot_cell(ax, country, parameters, results[country], attr,
                               country_label = country_label,
                               attr_label = attr_label,
                               plot_hist = False)
                    if row != nrows - 2:
                        for l in ax.get_xticklabels():
                            l.set_visible(False)
                        ax.xaxis.offsetText.set_visible(False)

            ax = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
            _make_legend(ax, plot_hist = False)

    fig.tight_layout()

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))
    return fig


def plot_all_countries():
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        with model.results.modes.load() as results:
            countries = sorted(results.keys())
            # Move Global to front.
            countries.remove('Global')
            countries = ['Global'] + countries
            for country in countries:
                fig = _plot_country(country, results[country])
                pdf.savefig(fig)
                pyplot.close(fig)


if __name__ == '__main__':
    # plot_country('South Africa')
    plot_somecountries()
    pyplot.show()

    # plot_all_countries()
