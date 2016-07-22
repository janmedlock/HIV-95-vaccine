#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make plots for sensitivity to vaccine parameters.
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

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

# import seaborn
import seaborn_quiet as seaborn


attrs_to_plot = ['infected', 'prevalence', 'incidence', 'AIDS', 'dead']

country_label_replacements = {
    'United States of America': 'United States'
}


ix = [2, 3, 4, 5, 9, 7]
colors = ['black'] + [common.colors_paired[i] for i in ix]

def _get_args(target):
    i = target.find('(')
    return target[i + 1 : -1].split(', ')


def get_target_label(treatment_target, target):
    baseline = model.targets.Vaccine(treatment_targets = treatment_target)
    args_baseline = _get_args(str(baseline))
    args = _get_args(target)
    diff = []
    for i in range(len(args)):
        if args[i] != args_baseline[i]:
            fancy = args[i].replace('_', ' ').replace('=', ' = ').capitalize()
            diff.append(fancy)
    retval = ', '.join(diff)
    if retval == '':
        return 'Baseline'
    else:
        return retval


def _viral_suppression_getter(results):
    return results.viral_suppression / results.infected


def _get_targets(treatment_target):
    return [str(t) for t in model.targets.vaccine_sensitivity_all
            if str(t._treatment_targets) == str(treatment_target)]


def _get_plot_info(treatment_target, parameters, results, stat):
    scale = 1
    percent = False

    if stat == 'infected':
        data_sim_getter = operator.attrgetter(stat)
        label = 'PLHIV\n(M)'
        scale = 1e6
    elif stat == 'prevalence':
        data_sim_getter = operator.attrgetter(stat)
        label = 'Prevelance\n'
        percent = True
    elif stat == 'incidence':
        data_sim_getter = operator.attrgetter('incidence_per_capita')
        label = 'Incidence\n(per M per y)'
        scale = 1e-6
    elif stat == 'drug_coverage':
        data_sim_getter = operator.attrgetter('proportions.treated')
        label = 'ART\nCoverage'
        percent = True
    elif stat == 'AIDS':
        data_sim_getter = operator.attrgetter(stat)
        label = 'AIDS\n(1000s)'
        scale = 1e3
    elif stat == 'dead':
        data_sim_getter = operator.attrgetter(stat)
        label = 'Deaths\n(M)'
        scale = 1e6
    elif stat == 'viral_suppression':
        data_sim_getter = _viral_suppression_getter
        label = 'Viral\nSupression'
        percent = True
    else:
        raise ValueError("Unknown stat '{}'".format(stat))
    
    if percent:
        scale = 1 / 100

    targets = _get_targets(treatment_target)

    data_sim = map(data_sim_getter, (results[t] for t in targets))

    t = list(results.values())[0].t

    return (data_sim, t, targets, label, scale, percent)


def _get_kwds(label):
    if label == 'Baseline':
        return dict(zorder = 2,
                    alpha = 1,
                    linestyle = 'dotted')
    else:
        return dict(zorder = 1,
                    alpha = 0.9,
                    linestyle = 'solid')


def _plot_cell(ax, country, treatment_target, parameters, results, stat,
               country_label = None,
               attr_label = 'ylabel'):
    '''
    Plot one axes of  figure.
    '''
    (data_sim, t, targets, label, scale, percent) = _get_plot_info(
        treatment_target, parameters, results, stat)

    # Plot simulation data.
    for (target, x) in zip(targets, data_sim):
        if x is not None:
            tlabel = get_target_label(treatment_target, target)
            ax.plot(t, x / scale,
                    label = tlabel,
                    **_get_kwds(tlabel))

    tick_interval = 10
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


def _make_legend(ax, treatment_target):
    ax.tick_params(labelbottom = False, labelleft = False)
    ax.grid(False)

    # Make legend at bottom.
    handles = []
    labels = []

    targets = _get_targets(treatment_target)
    colors = seaborn.color_palette()
    for (t, c) in zip(targets, colors):
        label = get_target_label(treatment_target, t)
        handles.append(mlines.Line2D([], [],
                                     color = c,
                                     **_get_kwds(label)))
        labels.append(label)
        if label == 'Baseline':
            # Blank spacer.
            handles.append(mlines.Line2D([], [],
                                         linewidth = 0))
            labels.append(' ')


    fig = ax.get_figure()
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


def _plot_country(country, treatment_target, results):
    fig = pyplot.figure(figsize = (8.5, 11))

    if country != 'Global':
        parameters = model.parameters.Parameters(country)
    else:
        parameters = None

    gs = gridspec.GridSpec(
        len(attrs_to_plot) + 1, 1,
        height_ratios = ((1, ) * len(attrs_to_plot) + (0.2, )))
    with seaborn.color_palette(colors):
        for (i, attr) in enumerate(attrs_to_plot):
            ax = fig.add_subplot(gs[i, 0])
            country_label = 'title' if (i == 0) else None
            _plot_cell(ax, country, treatment_target,
                       parameters, results, attr,
                       country_label = country_label)
            if i != len(attrs_to_plot) - 1:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)
        # Make legend at bottom.
        ax = fig.add_subplot(gs[-1, 0], axis_bgcolor = 'none')
        targets = results.keys()
        _make_legend(ax, treatment_target)

    fig.tight_layout()

    return fig


def plot_country(country, treatment_target):
    results = model.results.load_vaccine_sensitivity()
    return _plot_country(country, treatment_target, results[country])


def plot_all_countries(treatment_target):
    results = model.results.load_vaccine_sensitivity()
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in results.keys():
            fig = _plot_country(country, treatment_target, results[country])
            pdf.savefig(fig)
            pyplot.close(fig)


def plot_some_countries(treatment_target):
    results = model.results.load_vaccine_sensitivity()

    fig = pyplot.figure(figsize = (8.5, 7.5))
    # Legend in tiny bottom row
    ncols = len(common.countries_to_plot)
    nrows = len(attrs_to_plot) + 1
    gs = gridspec.GridSpec(nrows, ncols,
                           height_ratios = ((1, ) * (nrows - 1) + (0.35, )))
    with seaborn.color_palette(colors):
        for (col, country) in enumerate(common.countries_to_plot):
            if country != 'Global':
                parameters = model.parameters.Parameters(country)
            else:
                parameters = None
            attr_label = 'ylabel' if (col == 0) else None
            for (row, attr) in enumerate(attrs_to_plot):
                ax = fig.add_subplot(gs[row, col])
                country_label = 'title' if (row == 0) else None
                _plot_cell(ax, country, treatment_target,
                           parameters, results[country], attr,
                           country_label = country_label,
                           attr_label = attr_label)
                if row != nrows - 1:
                    for l in ax.get_xticklabels():
                        l.set_visible(False)
                    ax.xaxis.offsetText.set_visible(False)

        ax = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
        targets = results[country].keys()
        _make_legend(ax, treatment_target)

    fig.tight_layout()

    suffix = str(treatment_target).replace(' ', '_')
    fig.savefig('{}_{}.pdf'.format(common.get_filebase(), suffix))
    fig.savefig('{}_{}.png'.format(common.get_filebase(), suffix))
    return fig


if __name__ == '__main__':
    # plot_country('South Africa',
    #              model.targets.vaccine_sensitivity_baselines[0])
    for treatment_target in model.targets.vaccine_sensitivity_baselines:
        plot_some_countries(treatment_target)

    pyplot.show()

    # plot_all_countries(model.targets.vaccine_sensitivity_baselines[0])
