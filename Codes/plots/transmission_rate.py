#!/usr/bin/python3
'''
Make a PDF with a page of transmission plots for each country.
'''

import itertools
import os.path
import sys

import joblib
from matplotlib.backends import backend_pdf
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model
from model import transmission_rate

# import seaborn
import seaborn_quiet as seaborn


def plot_transmission_rates(countries, fig = None,
                            quantile_level = 0.01,
                            scale = 0.8,
                            savefig = True):
    if fig is None:
        fig = pyplot.figure(figsize = (8.5, 11))
    ax = fig.add_subplot(1, 1, 1)
    n = len(countries)
    colors = seaborn.color_palette('husl', n)
    for (i, country) in enumerate(countries):
        # Plot from top instead of bottom.
        j = n - 1 - i
        parameters = model.parameters.Parameters(country)
        rv = transmission_rate.estimate(parameters)
        a, b = rv.ppf([quantile_level / 2, 1 - quantile_level / 2])
        x = numpy.linspace(a, b, 101)
        y = rv.pdf(x) / n * scale
        ax.fill_between(x, j + y, j - y,
                        linewidth = 0,
                        facecolor = colors[i],
                        alpha = 0.7)
        ax.scatter(rv.mode, j,
                   marker = '|', s = 30, linewidth = 1,
                   color = 'black')
    ax.set_xlabel('Transmission rate (per year)')
    ax.set_xlim(0, 0.5)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.set_ylim(-1.5, n + 0.5)
    ax.set_yticks(range(n))
    yticklabels = (common.get_country_label(c, short = True)
                   for c in reversed(countries))
    ax.set_yticklabels(yticklabels, size = 6)
    ax.tick_params(axis = 'y', pad = 4)
    ax.grid(False, axis = 'y')
    fig.tight_layout(pad = 0)
    if savefig:
        common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
        common.savefig(fig, '{}.png'.format(common.get_filebase()))
    return fig, ax


def _plot_cell(ax, parameters, targets, results, stat):
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
        data = parameters.incidence_per_capita
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

    # Pop a style to for consistency with other plots.
    style = next(ax._get_lines.prop_cycler)

    # Plot simulation data.
    for (ti, vi, targeti, ci) in zip(t, val, targets, common.colors_paired):
        ax.plot(ti, vi / scale, alpha = 0.7, zorder = 1,
                label = str(targeti), color = ci)
        # Make a dotted line connecting the end of the historical data
        # and the begining of the simulation.
        if len(data_) > 0:
            ti_ = numpy.compress(numpy.isfinite(vi), ti)
            vi_ = numpy.compress(numpy.isfinite(vi), vi)
            x = [data_.index[-1], ti_[0]]
            y = [data_.iloc[-1], vi_[0]]
            ax.plot(x, numpy.asarray(y) / scale,
                    linestyle = 'dotted', color = 'black',
                    zorder = 2)

    historical_data_start_year = 1990
    t_end = max(ti[-1] for ti in t)
    ax.set_xlim(historical_data_start_year, t_end)
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(historical_data_start_year,
                        int(numpy.ceil(t_end)),
                        10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    # One minor tick between major ticks.
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    ax.set_ylabel(ylabel, size = 'medium')


def plot_one(country, fig = None):
    '''
    Plot transmission rate estimate and compare simulation
    with historical data.
    '''
    parameters = model.parameters.Parameters(country)
    parameter_values = parameters.mode()
    transmission_rates_vs_time = transmission_rate.estimate_vs_time(parameters)
    rv = transmission_rate.estimate(parameters)
    targets = model.targets.all_

    if fig is None:
        fig = pyplot.gcf()
    # Layout is 2 columns,
    # 1 big axes in the left column
    # for plotting transmission rates,
    # and nsubplots axes in the right column for plotting
    # simulation vs historical data.
    nsubplots = 3
    axes = []
    ax = fig.add_subplot(1, 2, 1)
    axes.append(ax)
    for i in range(nsubplots):
        # Use the first axes in this column to share x-axis
        # range, labels, etc.
        sharex = axes[1] if i > 0 else None
        ax = fig.add_subplot(nsubplots, 2, 2 * i + 2, sharex = sharex)
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

    axes[0].plot(transmission_rates_vs_time.index,
                 transmission_rates_vs_time,
                 label = 'estimates at each time',
                 marker = '.',
                 markersize = 10)

    # ax.axhline() doesn't automatically use the axes prop_cycler,
    # so we grab the next style from the cycler.
    axes[0].axhline(rv.mode,
                    label = 'mode',
                    alpha = 0.7,
                    **next(axes[0]._get_lines.prop_cycler))

    axes[0].xaxis.set_major_locator(ticker.MaxNLocator(integer = True))
    axes[0].xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    axes[0].yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    axes[0].set_ylabel('Transmission rate (per year)')
    axes[0].legend(loc = 'upper right', frameon = False)

    results = joblib.Parallel(n_jobs = -1)(
        joblib.delayed(model.simulation.Simulation)(parameter_values, target)
        for target in targets)
    _plot_cell(axes[1], parameters, targets, results, 'infected')
    _plot_cell(axes[2], parameters, targets, results, 'prevalence')
    _plot_cell(axes[3], parameters, targets, results, 'incidence')
    # _plot_cell(axes[4], parameters, targets, results, 'drug_coverage')
    axes[1].legend(loc = 'upper left', frameon = False)

    fig.tight_layout()
    return fig


def plot_all():
    countries = common.all_countries
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        fig, ax = plot_transmission_rates(countries, savefig = False)
        pdf.savefig(fig)
        pyplot.close(fig)

        for country in countries:
            print(country)
            fig = pyplot.figure(figsize = (11, 8.5))
            plot_one(country, fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_transmission_rates(common.all_countries)
    pyplot.show()

    # plot_all()
