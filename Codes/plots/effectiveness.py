#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make simulation plots.
'''

import collections
import itertools
import operator
import os.path
import sys

from matplotlib import gridspec
from matplotlib import lines as mlines
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

# import seaborn
import seaborn_quiet as seaborn


attrs_to_plot = ['infected', 'incidence', 'AIDS', 'dead']

targets_baselines = [model.targets.StatusQuo(),
                     model.targets.UNAIDS90(),
                     model.targets.UNAIDS95()]
targets = []
for t in targets_baselines:
    targets.extend([t, model.targets.Vaccine(treatment_targets = t)])
targets = [str(t) for t in targets]


# data_start_year = 1990
data_start_year = 2005

data_hist_style = dict(marker = '.',
                       markersize = 10,
                       alpha = 0.7,
                       color = 'black')


country_label_replacements = {
    'United States of America': 'United States'
}


def _get_plot_info(parameters, results, stat):
    data_hist = None
    scale = None
    percent = False
    data_sim_getter = operator.attrgetter(stat)

    if stat == 'infected':
        data_hist = parameters.prevalence * parameters.population
        label = 'PLHIV'
    elif stat == 'prevalence':
        data_hist = parameters.prevalence
        label = 'Prevelance\n'
        percent = True
    elif stat == 'incidence':
        data_sim_getter = operator.attrgetter('incidence_per_capita')
        data_hist = parameters.incidence
        label = 'Incidence\n(per M per y)'
        scale = 1e-6
        unit = ''
    elif stat == 'drug_coverage':
        data_sim_getter = operator.attrgetter('proportions.treated')
        data_hist = parameters.drug_coverage
        label = 'ART\nCoverage'
        percent = True
    elif stat == 'AIDS':
        data_hist = None
        label = 'AIDS'
    elif stat == 'dead':
        data_hist = None
        label = 'HIV-Related\nDeaths'
    elif stat == 'viral_suppression':
        data_sim_getter = common.viral_suppression_getter
        data_hist = None
        label = 'Viral\nSupression'
        percent = True
    elif stat == 'new_infections':
        data_hist = None
        label = 'New Infections'
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    
    data_sim = []
    for targ in targets:
        try:
            x = data_sim_getter(results[targ])
        except (KeyError, AttributeError):
            x = None
        data_sim.append(x)

    t = list(results.values())[0].t

    if percent:
        scale = 1 / 100
        unit = '%%'
    elif scale is None:
        vmax = numpy.max(data_sim)
        if vmax > 1e6:
            scale = 1e6
            unit = 'M'
        elif vmax > 1e3:
            scale = 1e3
            unit = 'k'
        else:
            scale = 1
            unit = ''

    return (data_hist, data_sim, t, label, scale, unit)


def _plot_cell(ax, country, parameters, results, stat,
               plot_hist = True,
               country_label = None,
               attr_label = 'ylabel'):
    '''
    Plot one axes of simulation and historical data figure.
    '''
    (data_hist, data_sim, t, label, scale, unit) = _get_plot_info(
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
            ax.plot(t, numpy.asarray(x) / scale,
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
                        label = None,
                        alpha = 0.7,
                        zorder = 2)
        else:
            # Pop a style.
            next(ax._get_lines.prop_cycler)

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
    ax.yaxis.set_major_formatter(common.UnitsFormatter(unit))

    country_str = country_label_replacements.get(country, country)
    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(label, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(label, size = 'medium')


def _make_legend(ax, plot_hist = True):
    ax.tick_params(labelbottom = False, labelleft = False)
    ax.grid(False)

    # Make legend at bottom.
    handles = []
    labels = []

    if plot_hist:
        handles.append(mlines.Line2D([], [], **data_hist_style))
        labels.append('Historical data')

        # Blank spacer.
        handles.append(mlines.Line2D([], [], linewidth = 0))
        labels.append(' ')

    colors = seaborn.color_palette()
    for (t, c) in zip(targets, colors):
        handles.append(mlines.Line2D([], [], color = c))
        labels.append(common.get_target_label(t))

    fig = ax.get_figure()
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


class GlobalParameters:
    def __init__(self):
        with pandas.ExcelFile(model.datasheet.datapath) as wb:
            pi = model.datasheet.IncidencePrevalence.get_country_data('Global',
                                                                      wb = wb)
            pop = model.datasheet.Population.get_country_data('Global',
                                                              wb = wb)
            self.prevalence = pi.prevalence
            self.incidence = pi.incidence
            self.population = pop
            self.drug_coverage = None


def _plot_country(country, results):
    fig = pyplot.figure(figsize = (8.5, 11))

    if country != 'Global':
        parameters = model.parameters.Parameters(country)
    else:
        parameters = GlobalParameters()

    nrows = len(attrs_to_plot) + 1
    ncols = 1
    legend_height_ratio = 0.2
    gs = gridspec.GridSpec(nrows, ncols,
                           height_ratios = ((1, ) * (nrows - 1)
                                            + (legend_height_ratio, )))
    with seaborn.color_palette(common.colors_paired):
        for (row, attr) in enumerate(attrs_to_plot):
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
    with model.results.load_modes() as results:
        return _plot_country(country, results[country])


def plot_some_countries():
    with model.results.load_modes() as results:
        fig = pyplot.figure(figsize = (8.5, 7.5))
        # Legend in tiny bottom row
        ncols = len(common.countries_to_plot)
        nrows = len(attrs_to_plot) + 1
        legend_height_ratio = 0.35
        gs = gridspec.GridSpec(nrows, ncols,
                               height_ratios = ((1, ) * (nrows - 1)
                                                + (legend_height_ratio, )))
        with seaborn.color_palette(common.colors_paired):
            for (col, country) in enumerate(common.countries_to_plot):
                if country != 'Global':
                    parameters = model.parameters.Parameters(country)
                else:
                    parameters = GlobalParameters()
                attr_label = 'ylabel' if (col == 0) else None
                for (row, attr) in enumerate(attrs_to_plot):
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
        with model.results.load_modes() as results:
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
    plot_some_countries()
    pyplot.show()

    plot_all_countries()
