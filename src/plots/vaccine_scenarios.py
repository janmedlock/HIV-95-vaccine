#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
make plots for sensitivity to vaccine parameters.
'''

import os.path
import sys

from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy
import seaborn

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


ix = [0, 1, 2, 3, 5, 9]
colors = ['black'] + [common.colors_paired[i] for i in ix]


def _get_args(target):
    i = target.find('(')
    return target[i + 1 : -1].split(', ')


def get_target_label(treatment_target, target):
    baseline = model.target.Vaccine(treatment_target = treatment_target)
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
    return [str(t) for t in model.target.vaccine_scenarios
            if hasattr(t, '_treatment_target')
            and (str(t._treatment_target) == str(treatment_target))]


def _get_kwds(label):
    if label == 'Baseline':
        return dict(zorder = 2,
                    alpha = 1,
                    linestyle = 'dotted')
    else:
        return dict(zorder = 1,
                    alpha = 0.9,
                    linestyle = 'solid')


def _plot_cell(ax, results, country, targets, stat, treatment_target,
               country_label = None,
               country_short_name = True,
               stat_label = 'ylabel',
               space_to_newline = True):
    '''
    Plot one axes of  figure.
    '''
    info = common.get_stat_info(stat)

    data = []
    for target in targets:
        r = results[target]
        if r is None:
            v = None
        else:
            v = getattr(r, stat)
        data.append(v)
    if info.scale is None:
        info.autoscale(data)
    if info.units is None:
        info.autounits(data)

    # Plot simulation data.
    for target in targets:
        r = results[target]
        if r is None:
            # Pop a style.
            next(ax._get_lines.prop_cycler)
        else:
            v = getattr(r, stat)
            label = get_target_label(treatment_target, target)
            ax.plot(common.t, v / info.scale,
                    label = label,
                    **_get_kwds(label))

    common.format_axes(ax, country, info, country_label, stat_label,
                       country_short_name = country_short_name,
                       space_to_newline = space_to_newline)


def _make_legend(fig, targets, treatment_target):
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


def plot_one(country, treatment_target = model.target.StatusQuo()):
    with seaborn.color_palette(colors):
        nrows = len(common.effectiveness_measures)
        ncols = 1
        fig, axes = pyplot.subplots(nrows, ncols,
                                    figsize = (8.5, 11),
                                    sharex = 'all', sharey = 'none')

        targets = _get_targets(treatment_target)
        results = common.get_country_results(country,
                                             targets = targets,
                                             parameters_type = 'mode')
        for (row, stat) in enumerate(common.effectiveness_measures):
            ax = axes[row]
            country_label = 'title' if ax.is_first_row() else None
            _plot_cell(ax, results, country, targets, stat, treatment_target,
                       country_label = country_label,
                       country_short_name = False)

        _make_legend(fig, targets, treatment_target)

    fig.tight_layout(rect = (0, 0.055, 1, 1))

    return fig


def plot_all(treatment_target = model.target.StatusQuo()):
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for region_or_country in common.all_regions_and_countries:
            print(region_or_country)
            fig = plot_one(region_or_country, treatment_target)
            pdf.savefig(fig)
            pyplot.close(fig)


def plot_some(treatment_target = model.target.StatusQuo()):
    targets = _get_targets(treatment_target)
    with seaborn.color_palette(colors):
        ncols = len(common.countries_to_plot)
        nrows = len(common.effectiveness_measures)
        legend_height_ratio = 0.35
        fig, axes = pyplot.subplots(nrows, ncols,
                                    figsize = (common.width_1_5column, 4),
                                    sharex = 'all', sharey = 'none')
        for (col, country) in enumerate(common.countries_to_plot):
            results = common.get_country_results(country,
                                                 targets = targets,
                                                 parameters_type = 'mode')
            for (row, stat) in enumerate(common.effectiveness_measures):
                ax = axes[row, col]

                stat_label = 'ylabel' if ax.is_first_col() else None
                country_label = 'title' if ax.is_first_row() else None

                _plot_cell(ax, results, country, targets,
                           stat, treatment_target,
                           country_label = country_label,
                           stat_label = stat_label,
                           space_to_newline = True)

                ax.xaxis.set_tick_params(labelsize = 4.5)
                ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 4))

                if stat_label is not None:
                    if stat == 'new_infections':
                        ax.yaxis.labelpad -= 2
                    elif stat == 'infected':
                        ax.yaxis.labelpad -= 5
                    elif stat == 'dead':
                        ax.yaxis.labelpad -= 5

        _make_legend(fig, targets, treatment_target)

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


