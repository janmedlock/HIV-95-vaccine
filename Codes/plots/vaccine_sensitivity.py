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
from matplotlib.backends import backend_pdf
import numpy
import tables

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


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


def _get_targets(treatment_target):
    return [str(t) for t in model.targets.vaccine_sensitivity
            if str(t._treatment_targets) == str(treatment_target)]


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
               stat_label = 'ylabel'):
    '''
    Plot one axes of  figure.
    '''
    info = common.get_stat_info(stat)

    targets = _get_targets(treatment_target)

    if info.scale is None:
        data = []
        for target in targets:
            try:
                v = getattr(results[country][str(target)], stat)
            except tables.NoSuchNodeError:
                pass
            else:
                data.append(v)
        info.autoscale(data)

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

    common.format_axes(ax, country, info, country_label, stat_label)


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
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


def _plot_country(results, country, treatment_target):
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
                       country_label = country_label)

        _make_legend(fig, treatment_target)

    fig.tight_layout(rect = (0, 0.055, 1, 1))

    return fig


def plot_country(country, treatment_target):
    with model.results.modes.load_vaccine_sensitivity() as results:
        return _plot_country(results, country, treatment_target)


def plot_allcountries(treatment_target):
    with model.results.modes.load_vaccine_sensitivity() as results:
        regions_and_countries = results.keys()
        # Put regions first.
        regions = []
        for region in model.regions.all_:
            if region in regions_and_countries:
                regions.append(region)
                regions_and_countries.remove(region)
        countries = sorted(regions_and_countries)
        regions_and_countries = regions + countries

        filename = '{}_all.pdf'.format(common.get_filebase())
        with backend_pdf.PdfPages(filename) as pdf:
            for region_or_country in regions_and_countries:
                print(region_or_country)
                fig = _plot_country(results, region_or_country,
                                    treatment_target)
                pdf.savefig(fig)
                pyplot.close(fig)


def plot_somecountries(treatment_target):
    with model.results.modes.load_vaccine_sensitivity() as results:
        with seaborn.color_palette(colors):
            ncols = len(common.countries_to_plot)
            nrows = len(common.effectiveness_measures)
            legend_height_ratio = 0.35
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = (8.5, 7.5),
                                        sharex = 'all', sharey = 'none')
            for (col, country) in enumerate(common.countries_to_plot):
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = axes[row, col]

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, country, treatment_target, stat,
                               country_label = country_label,
                               stat_label = stat_label)

            _make_legend(fig, treatment_target)

    fig.tight_layout()

    fig.tight_layout(rect = (0, 0.07, 1, 1))

    suffix = str(treatment_target).replace(' ', '_')
    fig.savefig('{}_{}.pdf'.format(common.get_filebase(), suffix))
    fig.savefig('{}_{}.png'.format(common.get_filebase(), suffix))

    return fig


if __name__ == '__main__':
    # plot_country('South Africa',
    #              model.targets.vaccine_sensitivity_baselines[0])
    for treatment_target in model.targets.vaccine_sensitivity_baselines:
        plot_somecountries(treatment_target)
    pyplot.show()

    # plot_allcountries(model.targets.vaccine_sensitivity_baselines[0])
