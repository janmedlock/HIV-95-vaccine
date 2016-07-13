#!/usr/bin/python3
'''
Make a PDF with a page of simulation plots for each country.

.. todo:: Add 'Global' to plot_all_countries().

.. todo:: Merge with :mod:`point_estimates/effectiveness.py`.
'''

import collections
import itertools
import operator
import os.path
import sys

import joblib
import matplotlib
from matplotlib.backends import backend_pdf
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

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
        data = parameters.prevalence * parameters.population
        val = map(operator.attrgetter(stat), results.values())
    elif stat == 'prevalence':
        percent = True
        ylabel = 'Prevelance\n'
        data = parameters.prevalence
        val = map(operator.attrgetter(stat), results.values())
    elif stat == 'incidence':
        scale = 1e-3
        ylabel = 'Incidence\n(per 1000 per y)'
        data = parameters.incidence
        val = map(operator.attrgetter('incidence_per_capita'), results.values())
    elif stat == 'drug_coverage':
        percent = True
        ylabel = 'Drug\ncoverage'
        data = parameters.drug_coverage
        val = map(operator.attrgetter('proportions.treated'), results.values())
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    t = map(operator.attrgetter('t'), results.values())

    if percent:
        scale = 1 / 100

    cp = seaborn.color_palette('Paired', 8)
    ix = [4, 5, 0, 1, 2, 3]
    colors = [cp[i] for i in ix]
    styles = itertools.cycle(matplotlib.cycler(color = colors))

    # Plot historical data.
    data_ = data.dropna()
    if len(data_) > 0:
        ax.plot(data_.index, data_ / scale,
                marker = '.', markersize = 10,
                alpha = 0.7,
                zorder = 2,
                color = 'black',
                label = 'data')

    # Plot simulation data.
    t_max = None
    for (t_, v, target) in zip(t, val, results.keys()):
        if t_max is None:
            t_max = max(t_)
        else:
            t_max = max(max(t_), t_max)
        ax.plot(t_, v / scale, alpha = 0.7, zorder = 1,
                label = str(target),
                **next(styles))
        # Make a dotted line connecting the end of the historical data
        # and the begining of the simulation.
        if len(data_) > 0:
            t__ = numpy.compress(numpy.isfinite(v), t_)
            v__ = numpy.compress(numpy.isfinite(v), v)
            x = [data_.index[-1], t__[0]]
            y = [data_.iloc[-1], v__[0]]
            ax.plot(x, numpy.asarray(y) / scale,
                    linestyle = 'dotted', color = 'black',
                    alpha = 0.7,
                    zorder = 2)

    if t_max is not None:
        data_start_year = 1990
        ax.set_xlim(data_start_year, t_max)
        # Make ticks every 10 years.
        a = data_start_year
        b = int(numpy.ceil(t_max))
        ticks = range(a, b, 10)
        if ((b - a) % 10) = 0:
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


def get_simulation_results(parameters, targets = None):
    if targets is None:
        targets = model.targets.all_

    try:
        parameter_values = parameters.mode()
    except AssertionError:
        return {}
    else:
        results = joblib.Parallel(n_jobs = -1)(
            joblib.delayed(model.simulation.Simulation)(parameter_values,
                                                        target)
            for target in targets)
        return dict(zip(targets, results))


def plot_country(country, targets = None, fig = None):
    '''
    Compare simulation with historical data.
    '''
    parameters = model.parameters.Parameters(country)
    results = get_simulation_results(parameters, targets = targets)
    return _plot_country(parameters, results, fig = fig)


def plot_all_countries(targets = None):
    countries = model.datasheet.get_country_list()
    filename = '{}.pdf'.format(common.get_filebase())
    parameters = {}
    results = collections.defaultdict(dict)
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            p = model.parameters.Parameters(country)
            r = get_simulation_results(p, targets = targets)
            parameters[country] = p
            for (target, val) in r.items():
                results[target][country] = val
            fig = pyplot.figure(figsize = (8.5, 11))
            _plot_country(p, r, fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)
            break

    ###
    ### Make model.global_ objects with parameters and results[target]
    ###


if __name__ == '__main__':
    # plot_country('South Africa')
    # pyplot.show()

    plot_all_countries()
