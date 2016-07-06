#!/usr/bin/python3
'''
Make a PDF with a page of simulation plots for each country.
'''

import itertools
import sys

import joblib
from matplotlib.backends import backend_pdf
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

sys.path.append('..')
import model
from model import transmission_rate
sys.path.append('../plots')
import common

# import seaborn
import seaborn_quiet as seaborn


def _plot_sim_cell(ax, parameters, targets, results, stat):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    percent = False
    if stat == 'infected':
        scale = 1e6
        ylabel = 'Infected\n(M)'
        data = parameters.prevalence * parameters.population
        val = [r.infected for r in results]
    elif stat == 'prevalence':
        percent = True
        ylabel = 'Prevelance\n'
        data = parameters.prevalence
        val = [r.prevalence for r in results]
    elif stat == 'incidence':
        scale = 1e-3
        ylabel = 'Incidence\n(per 1000 per y)'
        data = parameters.incidence
        # Compute from simulation results.
        val = [r.incidence_per_capita for r in results]
    elif stat == 'drug_coverage':
        percent = True
        ylabel = 'Drug\ncoverage'
        data = parameters.drug_coverage
        val = [r.proportions.treated for r in results]
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    t = [r.t for r in results]

    if percent:
        scale = 1 / 100

    colors = iter(seaborn.color_palette('husl', len(targets)))

    # Plot historical data.
    data_ = data.dropna()
    if len(data_) > 0:
        ax.plot(data_.index, data_ / scale,
                marker = '.', markersize = 10,
                zorder = 2,
                color = 'black',
                label = 'data')
    else:
        # Pop a style for consistency with other plots.
        style = next(ax._get_lines.prop_cycler)

    # Plot simulation data.
    for (ti, vi, targeti) in zip(t, val, targets):
        ax.plot(ti, vi / scale, alpha = 0.7, zorder = 1,
                color = next(colors),
                label = str(targeti))
        # Make a dotted line connecting the end of the historical data
        # and the begining of the simulation.
        if len(data_) > 0:
            x = [data_.index[-1], ti[0]]
            y = [data_.iloc[-1], vi[0]]
            ax.plot(x, numpy.asarray(y) / scale,
                    linestyle = 'dotted', color = 'black',
                    zorder = 2)

    data_start_year = 1990
    if len(t) > 0:
        t_end = max(ti[-1] for ti in t)
        ax.set_xlim(data_start_year, t_end)
        # Every 10 years.
        ax.set_xticks(range(data_start_year, int(numpy.ceil(t_end)), 10))
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


def plot_country(country, targets, fig = None):
    '''
    Compare simulation with historical data.
    '''
    parameters = model.Parameters(country)

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
    fig.text(0.5, 1, country,
             verticalalignment = 'top',
             horizontalalignment = 'center')

    try:
        parameter_values = parameters.mode()
    except AssertionError:
        results = []
    else:
        results = joblib.Parallel(n_jobs = -1)(
            joblib.delayed(model.Simulation)(parameter_values, target)
            for target in targets)

    _plot_sim_cell(axes[0], parameters, targets, results, 'infected')
    _plot_sim_cell(axes[1], parameters, targets, results, 'prevalence')
    _plot_sim_cell(axes[2], parameters, targets, results, 'incidence')
    # _plot_sim_cell(axes[3], parameters, targets, results, 'drug_coverage')

    axes[0].legend(loc = 'upper left', frameon = False)

    fig.tight_layout()

    return fig


def plot_all_countries(targets):
    countries = model.get_country_list()
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            fig = pyplot.figure(figsize = (8.5, 11))
            plot_country(country, targets, fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    targets = [model.Targets959595()] + model.AllVaccineTargets

    # plot_country('South Africa', targets)
    # pyplot.show()

    plot_all_countries(targets)
