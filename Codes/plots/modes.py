#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.

.. todo:: Add 'Global' historical data.
'''

import collections
import operator
import os.path
import sys

from matplotlib.backends import backend_pdf
from matplotlib import pyplot
from matplotlib import ticker
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

# import seaborn
import seaborn_quiet as seaborn


def _viral_suppression_getter(results):
    return results.viral_suppression / results.infected


def _plot_sim_cell(ax, parameters, results, stat):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    percent = False
    data_hist = None
    if stat == 'infected':
        data_sim_getter = operator.attrgetter(stat)
        try:
            data_hist = parameters.prevalence * parameters.population
        except AttributeError:
            pass
        ylabel = 'Infected\n(M)'
        scale = 1e6
    elif stat == 'prevalence':
        data_sim_getter = operator.attrgetter(stat)
        try:
            data_hist = parameters.prevalence
        except AttributeError:
            pass
        ylabel = 'Prevelance\n'
        percent = True
    elif stat == 'incidence':
        data_sim_getter = operator.attrgetter('incidence_per_capita')
        try:
            data_hist = parameters.incidence
        except AttributeError:
            pass
        ylabel = 'Incidence\n(per 1000 per y)'
        scale = 1e-3
    elif stat == 'drug_coverage':
        data_sim_getter = operator.attrgetter('proportions.treated')
        try:
            data_hist = parameters.drug_coverage
        except AttributeError:
            pass
        ylabel = 'Drug\ncoverage'
        percent = True
    elif stat == 'AIDS':
        data_sim_getter = operator.attrgetter(stat)
        data_hist = None
        ylabel = 'AIDS\n(1000s)'
        scale = 1e3
    elif stat == 'dead':
        data_sim_getter = operator.attrgetter(stat)
        data_hist = None
        ylabel = 'Deaths\n(M)'
        scale = 1e6
    elif stat == 'viral_suppression':
        data_sim_getter = _viral_suppression_getter
        data_hist = None
        ylabel = 'Viral\nsupression'
        percent = True
    else:
        raise ValueError("Unknown stat '{}'".format(stat))

    data_sim = map(data_sim_getter, results.values())
    t_getter = operator.attrgetter('t')
    T = map(t_getter, results.values())
    targets = results.keys()

    if percent:
        scale = 1 / 100

    cp = seaborn.color_palette('Paired', 8)
    ix = [4, 5, 0, 1, 2, 3, 6, 7]
    colors = (cp[i] for i in ix)

    # Plot historical data.
    if data_hist is not None:
        data_hist = data_hist.dropna()
        if len(data_hist) > 0:
            ax.plot(data_hist.index, data_hist / scale,
                    marker = '.', markersize = 10,
                    alpha = 0.7,
                    zorder = 2,
                    color = 'black',
                    label = 'Historical data')

    # Plot simulation data.
    t_max = None
    for (target, t, x) in zip(targets, T, data_sim):
        if x is not None:
            if t_max is None:
                t_max = max(t)
            else:
                t_max = max(t_max, max(t))
            ax.plot(t, x / scale,
                    label = target,
                    color = next(colors),
                    alpha = 0.7,
                    zorder = 1)
            # Make a dotted line connecting the end of the historical data
            # and the begining of the simulation.
            if (data_hist is not None) and (len(data_hist) > 0):
                t_ = numpy.compress(numpy.isfinite(x), t)
                x_ = numpy.compress(numpy.isfinite(x), x)
                t_ = [data_hist.index[-1], t_[0]]
                x_ = [data_hist.iloc[-1], x_[0]]
                ax.plot(t_, numpy.asarray(x_) / scale,
                        color = 'black',
                        linestyle = 'dotted',
                        alpha = 0.7,
                        zorder = 2)

    if t_max is not None:
        # data_start_year = 1990
        data_start_year = 2005
        ax.set_xlim(data_start_year, t_max)
        tick_interval = 5
        a = data_start_year
        b = int(numpy.ceil(t_max))
        ticks = range(a, b, tick_interval)
        if ((b - a) % tick_interval) == 0:
            ticks = list(ticks) + [b]
        ax.set_xticks(ticks)

    ax.grid(True, which = 'both', axis = 'both')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    # One minor tick between major ticks.
    # ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    ax.set_ylabel(ylabel, size = 'medium')


def _plot_country(country, results, fig = None):
    if fig is None:
        fig = pyplot.gcf()

    if country != 'Global':
        parameters = model.parameters.Parameters(country)
    else:
        parameters = None

    attrs = ['infected', 'incidence', 'AIDS', 'dead', 'viral_suppression']
    sharex = None
    for (i, attr) in enumerate(attrs):
        # Use the first axes in this column to share x-axis
        # range, labels, etc.
        ax = fig.add_subplot(len(attrs), 1, i + 1, sharex = sharex)
        if sharex is None:
            sharex = ax
        _plot_sim_cell(ax, parameters, results, attr)
        if not ax.is_last_row():
            for l in ax.get_xticklabels():
                l.set_visible(False)
            ax.xaxis.offsetText.set_visible(False)
        if ax.is_first_row():
            ax.legend(loc = 'upper left', frameon = False)

    # Set title
    fig.text(0.5, 1, country,
             verticalalignment = 'top',
             horizontalalignment = 'center')

    fig.tight_layout()

    return fig


def plot_country(country, fig = None):
    '''
    Compare simulation with historical data.
    '''
    results = model.results.load_modes()
    return _plot_country(country, results[country], fig = fig)


def plot_all_countries(figsize = (8.5, 11)):
    results = model.results.load_modes()
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in results.keys():
            fig = pyplot.figure(figsize = figsize)
            _plot_country(country, results[country], fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)

if __name__ == '__main__':
    # plot_country('South Africa')
    # pyplot.show()

    plot_all_countries()
