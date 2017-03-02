#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make plots for sensitivity to vaccine parameters.
'''

import operator
import os.path
import sys

from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy
import tables

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


ix = [0, 1, 2, 3, 5, 9]
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
            fancy = args[i].replace('_', ' ').replace('=', ' = ')
            fancy = fancy.replace('time to start', 'start date')
            if fancy.startswith('time to fifty percent'):
                i = fancy.find('=')
                t = float(fancy[i + 2 : -1])
                fancy = 'scale-up = {:g}% y$^{{-1}}$'.format(50 / t)
            i = fancy.find('=')
            pre = fancy[ : i - 1]
            post = fancy[i + 2 : ]
            fancy = post + ' ' + pre
            diff.append(fancy.capitalize())
    retval = ', '.join(diff)
    if retval == '':
        return 'Baseline'
    else:
        return retval


def _get_targets(treatment_target):
    return [str(t) for t in model.targets.vaccine_scenarios
            if hasattr(t, '_treatment_targets')
            and (str(t._treatment_targets) == str(treatment_target))]


def _get_kwds(label):
    if label == 'Baseline':
        return dict(zorder = 2,
                    alpha = 1,
                    linestyle = 'dotted')
    else:
        return dict(zorder = 1,
                    alpha = 0.9,
                    linestyle = 'solid')


def _plot_cell(ax, results, country, treatment_target, stat,
               country_label = None,
               country_label_short = True,
               stat_label = 'ylabel',
               space_to_newline = True):
    '''
    Plot one axes of  figure.
    '''
    info = common.get_stat_info(stat)

    targets = _get_targets(treatment_target)

    data = []
    for target in targets:
        try:
            v = getattr(results[country][str(target)], stat)
        except tables.NoSuchNodeError:
            pass
        else:
            data.append(v)
    if info.scale is None:
        info.autoscale(data)
    if info.units is None:
        info.autounits(data)

    # Plot simulation data.
    for target in targets:
        try:
            v = getattr(results[country][str(target)], stat)
        except tables.NoSuchNodeError:
            pass
        else:
            label = get_target_label(treatment_target, target)
            ax.plot(common.t, numpy.asarray(v) / info.scale,
                    label = label,
                    **_get_kwds(label))

    common.format_axes(ax, country, info, country_label, stat_label,
                       country_label_short = country_label_short,
                       space_to_newline = space_to_newline)


def _make_legend(fig, treatment_target):
    targets = _get_targets(treatment_target)
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(targets, colors):
        label = get_target_label(treatment_target, t)
        handles.append(lines.Line2D([], [],
                                    color = c,
                                    **_get_kwds(label)))
        labels.append(label)
        if label == 'Baseline':
            # Blank spacer.
            handles.append(lines.Line2D([], [],
                                        linewidth = 0))
            labels.append(' ')

    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = int(numpy.ceil(len(labels) / 2)),
                      frameon = False)


def _plot_one(results, country, treatment_target):
    with seaborn.color_palette(colors):
        nrows = len(common.effectiveness_measures)
        ncols = 1
        fig, axes = pyplot.subplots(nrows, ncols,
                                    figsize = (8.5, 11),
                                    sharex = 'all', sharey = 'none')
        for (row, stat) in enumerate(common.effectiveness_measures):
            ax = axes[row]
            country_label = 'title' if ax.is_first_row() else None
            _plot_cell(ax, results, country, treatment_target, stat,
                       country_label = country_label,
                       country_label_short = False)

        _make_legend(fig, treatment_target)

    fig.tight_layout(rect = (0, 0.055, 1, 1))

    return fig


def plot_one(country, treatment_target = model.targets.StatusQuo()):
    with model.results.modes.open_vaccine_scenarios() as results:
        return _plot_one(results, country, treatment_target)


def plot_all(treatment_target = model.targets.StatusQuo()):
    with model.results.modes.open_vaccine_scenarios() as results:
        regions_and_countries = results.keys()
        # Put regions first.
        regions = []
        for region in model.regions.all_:
            if region in regions_and_countries:
                regions.append(region)
                regions_and_countries.remove(region)
        # countries needs to be sorted by the name on graph.
        countries = sorted(regions_and_countries,
                           key = common.country_sort_key)
        regions_and_countries = regions + countries

        filename = '{}_all.pdf'.format(common.get_filebase())
        with backend_pdf.PdfPages(filename) as pdf:
            for region_or_country in regions_and_countries:
                print(region_or_country)
                fig = _plot_one(results, region_or_country, treatment_target)
                pdf.savefig(fig)
                pyplot.close(fig)


def plot_some(treatment_target = model.targets.StatusQuo()):
    with model.results.modes.open_vaccine_scenarios() as results:
        with seaborn.color_palette(colors):
            ncols = len(common.countries_to_plot)
            nrows = len(common.effectiveness_measures)
            legend_height_ratio = 0.35
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = (common.width_1_5column, 4),
                                        sharex = 'all', sharey = 'none')
            for (col, country) in enumerate(common.countries_to_plot):
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = axes[row, col]

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, country, treatment_target, stat,
                               country_label = country_label,
                               stat_label = stat_label,
                               space_to_newline = True)

                    ax.xaxis.set_tick_params(labelsize = 4.5)
                    # ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))

                    if stat_label is not None:
                        if stat == 'new_infections':
                            ax.yaxis.labelpad -= 2
                        elif stat == 'infected':
                            ax.yaxis.labelpad -= 6
                        elif stat == 'dead':
                            ax.yaxis.labelpad -= 5

            _make_legend(fig, treatment_target)

    fig.tight_layout(h_pad = 0.7, w_pad = 0,
                     rect = (0, 0.06, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_some()
    pyplot.show()

    # plot_all()
