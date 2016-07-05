#!/usr/bin/python3
'''
Make a PDF with a page of transmission plots for each country.
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

# Here because code to suppress warnings is in common.
import seaborn


def plot_transmission_rates(countries, fig = None,
                            quantile_level = 0.01,
                            scale = 0.8):
    if fig is None:
        fig = pyplot.gcf()
    ax = fig.add_subplot(1, 1, 1)
    n = len(countries)
    colors = seaborn.color_palette('husl', n)
    for (i, country) in enumerate(countries):
        # Plot from top instead of bottom.
        j = n - 1 - i
        print(country)
        parameters = model.Parameters(country)
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
    ax.set_xlim(left = 0)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.set_ylim(-1.5, n + 0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(reversed(countries), fontdict = dict(size = 6))
    ax.grid(False, axis = 'y')
    fig.tight_layout()
    return fig, ax


def _plot_sim_cell(ax, parameters, targets, results, stat):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    percent = False
    if stat == 'infected':
        scale = 1e6
        ylabel = 'Infected\n(M)'
        data = parameters.prevalence * parameters.population
        t = [r.t for r in results]
        val = [r.infected for r in results]
    elif stat == 'prevalence':
        percent = True
        ylabel = 'Prevelance\n'
        data = parameters.prevalence
        t = [r.t for r in results]
        val = [r.prevalence for r in results]
    elif stat == 'incidence':
        scale = 1e-3
        ylabel = 'Incidence\n(per 1000 per y)'
        data = parameters.incidence
        # Compute from simulation results.
        val = []
        for r in results:
            ni = numpy.asarray(r.new_infections)
            n = numpy.asarray(r.alive)
            val.append(numpy.diff(ni) / numpy.diff(r.t) / n[..., 1 :])
        # Need to drop one t value since we have differences above.
        t = [r.t[1 : ] for r in results]
    elif stat == 'drug_coverage':
        percent = True
        ylabel = 'Drug\ncoverage'
        data = parameters.drug_coverage
        t = [r.t for r in results]
        val = [r.proportions.treated for r in results]
    else:
        raise ValueError("Unknown stat '{}'".format(stat))

    if percent:
        scale = 1 / 100

    # Plot historical data.
    data_ = data.dropna()
    if len(data_) > 0:
        ax.plot(data_.index, data_ / scale,
                marker = '.', markersize = 10,
                zorder = 2,
                label = 'data')
    else:
        # Pop a style for consistency with other plots.
        style = next(ax._get_lines.prop_cycler)

    # Pop a style to for consistency with other plots.
    style = next(ax._get_lines.prop_cycler)

    # Plot simulation data.
    for (ti, vi, targeti) in zip(t, val, targets):
        ax.plot(ti, vi / scale, alpha = 0.7, zorder = 1,
                label = targeti.__name__)
        # Make a dotted line connecting the end of the historical data
        # and the begining of the simulation.
        if len(data_) > 0:
            x = [data_.index[-1], ti[0]]
            y = [data_.iloc[-1], vi[0]]
            ax.plot(x, numpy.asarray(y) / scale,
                    linestyle = 'dotted', color = 'black',
                    zorder = 2)

    data_start_year = 1990
    t_end = max(ti[-1] for ti in t)
    ax.set_xlim(data_start_year, t_end)
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(data_start_year, int(numpy.ceil(t_end)), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    # One minor tick between major ticks.
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    ax.set_ylabel(ylabel, size = 'medium')


def plot_country(country,
                 targets = (model.TargetsStatusQuo,
                            model.Targets909090,
                            model.Targets959595,
                            model.TargetsVaccine),
                 fig = None):
    '''
    Plot transmission rate estimate and compare simulation
    with historical data.
    '''
    parameters = model.Parameters(country)
    parameter_values = parameters.mode()
    transmission_rates_vs_time = transmission_rate.estimate_vs_time(parameters)
    rv = transmission_rate.estimate(parameters)

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
        joblib.delayed(model.Simulation)(parameter_values, target)
        for target in targets)
    _plot_sim_cell(axes[1], parameters, targets, results, 'infected')
    _plot_sim_cell(axes[2], parameters, targets, results, 'prevalence')
    _plot_sim_cell(axes[3], parameters, targets, results, 'incidence')
    # _plot_sim_cell(axes[4], parameters, targets, results, 'drug_coverage')
    axes[1].legend(loc = 'upper left', frameon = False)

    fig.tight_layout()
    return fig


def plot_all_countries():
    countries = model.get_country_list('IncidencePrevalence')
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        fig = pyplot.figure(figsize = (8.5, 11))
        _, ax = plot_transmission_rates(countries, fig = fig)
        pdf.savefig(fig)
        pyplot.close(fig)

        for country in countries:
            print(country)
            fig = pyplot.figure(figsize = (11, 8.5))
            plot_country(country, fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    # plot_country('South Africa')
    # countries = model.get_country_list('IncidencePrevalence')
    # plot_transmission_rates(countries)
    # pyplot.show()

    plot_all_countries()
