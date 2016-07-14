#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.

.. todo:: Add 'Global' to plot_all_countries().

.. todo:: Merge with :mod:`point_estimates/effectiveness.py`.
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


def _plot_sim_cell(ax, parameters, results, stat):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    percent = False
    if stat == 'infected':
        scale = 1e6
        ylabel = 'Infected\n(M)'
        data_hist = parameters.prevalence * parameters.population
        data_sim_getter = operator.attrgetter(stat)
    elif stat == 'prevalence':
        percent = True
        ylabel = 'Prevelance\n'
        data_hist = parameters.prevalence
        data_sim_getter = operator.attrgetter(stat)
    elif stat == 'incidence':
        scale = 1e-3
        ylabel = 'Incidence\n(per 1000 per y)'
        data_hist = parameters.incidence
        data_sim_getter = operator.attrgetter('incidence_per_capita')
    elif stat == 'drug_coverage':
        percent = True
        ylabel = 'Drug\ncoverage'
        data_hist = parameters.drug_coverage
        data_sim_getter = operator.attrgetter('proportions.treated')
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
        if len(data_hist) > 0:
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
        data_start_year = 1990
        ax.set_xlim(data_start_year, t_max)
        # Make ticks every 10 years.
        a = data_start_year
        b = int(numpy.ceil(t_max))
        ticks = range(a, b, 10)
        if ((b - a) % 10) == 0:
            ticks = list(ticks) + [b]
        ax.set_xticks(ticks)

    ax.grid(True, which = 'both', axis = 'both')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    # One minor tick between major ticks.
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    ax.set_ylabel(ylabel, size = 'medium')


def _plot_country(parameters, results, fig = None):
    if fig is None:
        fig = pyplot.gcf()

    nsubplots = 3
    axes = []
    for i in range(nsubplots):
        # Use the first axes in this column to share x-axis
        # range, labels, etc.
        sharex = axes[0] if i > 0 else None
        ax = fig.add_subplot(nsubplots, 1, i + 1, sharex = sharex)
        axes.append(ax)
    # Turn off x-axis labels on non-bottom subplots.
    if nsubplots > 1:
        for ax in axes:
            if not ax.is_last_row():
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)

    # Set title
    fig.text(0.5, 1, parameters.country,
             verticalalignment = 'top',
             horizontalalignment = 'center')

    _plot_sim_cell(axes[0], parameters, results, 'infected')
    _plot_sim_cell(axes[1], parameters, results, 'prevalence')
    _plot_sim_cell(axes[2], parameters, results, 'incidence')
    # _plot_sim_cell(axes[3], parameters, results, 'drug_coverage')

    axes[0].legend(loc = 'upper left', frameon = False)

    fig.tight_layout()

    return fig


def plot_country(country, fig = None):
    '''
    Compare simulation with historical data.
    '''
    results = model.results.load_modes()
    parameters = model.parameters.Parameters(country)
    return _plot_country(parameters, results[country], fig = fig)


def plot_all_countries():
    results = model.results.load_modes()
    countries = results.keys()
    filename = '{}.pdf'.format(common.get_filebase())
    # Store results_[target][country] for building a Global version.
    results_ = collections.OrderedDict()
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            parameters = model.parameters.Parameters(country)
            fig = pyplot.figure(figsize = (8.5, 11))
            _plot_country(parameters, results[country], fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)
            for (target, val) in results[country].items():
                if target not in results_:
                    results_[target] = collections.OrderedDict()
                results_[target][country] = val

    ###
    ### Make model.global_ object with results_[target]
    ###

    return results_


if __name__ == '__main__':
    # plot_country('South Africa')
    # pyplot.show()

    results = plot_all_countries()
