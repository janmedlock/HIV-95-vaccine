#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.

.. todo:: Add 'Global' historical data.
'''

import collections
import itertools
import operator
import os.path
import sys

from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import matplotlib.lines
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

# import seaborn
import seaborn_quiet as seaborn


attrs_to_plot = ['infected', 'incidence', 'AIDS', 'dead', 'viral_suppression']

# data_start_year = 1990
data_start_year = 2005

data_hist_style = dict(marker = '.',
                       markersize = 10,
                       alpha = 0.7,
                       color = 'black')


country_label_replacements = {
    'United States of America': 'United States'
}


def _viral_suppression_getter(results):
    return results.viral_suppression / results.infected


def _get_plot_info(parameters, results, stat):
    data_hist = None
    scale = 1
    percent = False

    if stat == 'infected':
        data_sim_getter = operator.attrgetter(stat)
        try:
            data_hist = parameters.prevalence * parameters.population
        except AttributeError:
            pass
        label = 'Infected\n(M)'
        scale = 1e6
    elif stat == 'prevalence':
        data_sim_getter = operator.attrgetter(stat)
        try:
            data_hist = parameters.prevalence
        except AttributeError:
            pass
        label = 'Prevelance\n'
        percent = True
    elif stat == 'incidence':
        data_sim_getter = operator.attrgetter('incidence_per_capita')
        try:
            data_hist = parameters.incidence
        except AttributeError:
            pass
        label = 'Incidence\n(per 1000 per y)'
        scale = 1e-3
    elif stat == 'drug_coverage':
        data_sim_getter = operator.attrgetter('proportions.treated')
        try:
            data_hist = parameters.drug_coverage
        except AttributeError:
            pass
        label = 'Drug\ncoverage'
        percent = True
    elif stat == 'AIDS':
        data_sim_getter = operator.attrgetter(stat)
        data_hist = None
        label = 'AIDS\n(1000s)'
        scale = 1e3
    elif stat == 'dead':
        data_sim_getter = operator.attrgetter(stat)
        data_hist = None
        label = 'Deaths\n(M)'
        scale = 1e6
    elif stat == 'viral_suppression':
        data_sim_getter = _viral_suppression_getter
        data_hist = None
        label = 'Viral\nsupression'
        percent = True
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    
    if percent:
        scale = 1 / 100

    data_sim = map(data_sim_getter, results.values())

    t = list(results.values())[0].t

    targets = results.keys()

    return (data_hist, data_sim, t, targets, label, scale, percent)


def _plot_cell(ax, country, parameters, results, stat,
               plot_hist = True,
               country_label = None,
               attr_label = 'ylabel'):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    (data_hist, data_sim, t, targets, label, scale, percent) = _get_plot_info(
        parameters, results, stat)

    # Plot historical data.
    if plot_hist and (data_hist is not None):
        data_hist = data_hist.dropna()
        if len(data_hist) > 0:
            ax.plot(data_hist.index, data_hist / scale,
                    label = 'Historical data',
                    zorder = 2,
                    **data_hist_style)

    # Plot simulation data.
    for (target, x) in zip(targets, data_sim):
        if x is not None:
            ax.plot(t, x / scale,
                    label = common.get_target_label(target),
                    alpha = 0.7,
                    zorder = 1)
            # Make a dotted line connecting the end of the historical data
            # and the begining of the simulation.
            if plot_hist and (data_hist is not None) and (len(data_hist) > 0):
                t_ = numpy.compress(numpy.isfinite(x), t)
                x_ = numpy.compress(numpy.isfinite(x), x)
                t_ = [data_hist.index[-1], t_[0]]
                x_ = [data_hist.iloc[-1], x_[0]]
                ax.plot(t_, numpy.asarray(x_) / scale,
                        color = 'black',
                        linestyle = 'dotted',
                        alpha = 0.7,
                        zorder = 2)

    tick_interval = 10
    if plot_hist:
        a = data_start_year
    else:
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
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())

    country_str = country_label_replacements.get(country, country)
    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(label, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(label, size = 'medium')


def _make_legend(ax, targets, plot_hist = True):
    ax.tick_params(labelbottom = False, labelleft = False)
    ax.grid(False)

    # Make legend at bottom.
    handles = []
    labels = []

    if plot_hist:
        handles.append(matplotlib.lines.Line2D([], [], **data_hist_style))
        labels.append('Historical data')

        # Blank spacer.
        handles.append(matplotlib.lines.Line2D([], [], linewidth = 0))
        labels.append(' ')

    colors = seaborn.color_palette()
    for (t, c) in zip(targets, colors):
        handles.append(matplotlib.lines.Line2D([], [], color = c))
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

    if country != 'Global':
        parameters = model.parameters.Parameters(country)
    else:
        parameters = None

    gs = gridspec.GridSpec(
        len(attrs_to_plot) + 1, 1,
        height_ratios = ((1, ) * len(attrs_to_plot) + (0.2, )))
    with seaborn.color_palette(common.colors_paired):
        for (i, attr) in enumerate(attrs_to_plot):
            ax = fig.add_subplot(gs[i, 0])
            country_label = 'title' if (i == 0) else None
            _plot_cell(ax, country, parameters, results, attr,
                       country_label = country_label)
            if i != len(attrs_to_plot) - 1:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)
        # Make legend at bottom.
        ax = fig.add_subplot(gs[-1, 0], axis_bgcolor = 'none')
        targets = results.keys()
        _make_legend(ax, targets)

    fig.tight_layout()

    return fig


def plot_country(country):
    results = model.results.load_modes()
    return _plot_country(country, results[country])


def plot_some_countries():
    results = model.results.load_modes()

    fig = pyplot.figure(figsize = (8.5, 8))
    # Legend in tiny bottom row
    gs = gridspec.GridSpec(
        len(common.countries_to_plot) + 1, len(attrs_to_plot),
        height_ratios = ((1, ) * len(common.countries_to_plot) + (0.3, )))
    with seaborn.color_palette(common.colors_paired):
        for (i, country) in enumerate(common.countries_to_plot):
            if country != 'Global':
                parameters = model.parameters.Parameters(country)
            else:
                parameters = None
            attr_label = 'title' if (i == 0) else None
            for (j, attr) in enumerate(attrs_to_plot):
                ax = fig.add_subplot(gs[i, j])
                country_label = 'ylabel' if (j == 0) else None
                _plot_cell(ax, country, parameters, results[country], attr,
                           country_label = country_label,
                           attr_label = attr_label,
                           plot_hist = False)
                if i != len(common.countries_to_plot) - 1:
                    for l in ax.get_xticklabels():
                        l.set_visible(False)
                    ax.xaxis.offsetText.set_visible(False)

        ax = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
        targets = results[country].keys()
        _make_legend(ax, targets,
                     plot_hist = False)

    fig.tight_layout()

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))
    return fig


def plot_all_countries():
    results = model.results.load_modes()
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in results.keys():
            fig = _plot_country(country, results[country])
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    # plot_country('South Africa')
    plot_some_countries()
    pyplot.show()

    # plot_all_countries()
