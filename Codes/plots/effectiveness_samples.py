#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Add historical incidence and prevalence to plots.
'''

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


def _plot_cell(ax, results, country, targets, attr,
               confidence_level = 0.9,
               country_label = None, attr_label = None,
               colors = None, alpha = 0.35):
    if colors is None:
        colors = seaborn.color_palette()

    info = common.get_stat_info(attr)

    CIkey = 'CI{:g}'.format(100 * confidence_level)

    if info.scale is None:
        data = []
        for target in targets:
            try:
                v = results[country][str(target)][attr]
            except tables.NoSuchNodeError:
                pass
            else:
                if confidence_level > 0:
                    data.append(v[CIkey])
                else:
                    data.append(v['median'])
        info.autoscale(data)

    for (i, target) in enumerate(targets):
        try:
            v = results[country][str(target)][attr]
        except tables.NoSuchNodeError:
            pass
        else:
            lines = ax.plot(common.t,
                            numpy.asarray(v['median']) / info.scale,
                            label = common.get_target_label(target),
                            color = colors[i],
                            zorder = 2)

            if confidence_level > 0:
                CI = v[CIkey]
                ax.fill_between(common.t,
                                numpy.asarray(CI[0]) / info.scale,
                                numpy.asarray(CI[1]) / info.scale,
                                color = colors[i],
                                alpha = alpha)

    common.format_axes(ax, country, info, country_label, attr_label)


def plot_somecountries(results, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    ncols = len(common.countries_to_plot)
    nrows = len(common.effectiveness_measures)
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = (8.5, 7.5),
                                sharex = 'all', sharey = 'none')
    for (col, country) in enumerate(common.countries_to_plot):
        for (row, attr) in enumerate(common.effectiveness_measures):
            ax = axes[row, col]

            attr_label = 'ylabel' if ax.is_first_col() else None
            country_label = 'title' if ax.is_first_row() else None

            _plot_cell(ax, results, country, targets, attr,
                       country_label = country_label,
                       attr_label = attr_label,
                       **kwargs)

    _make_legend(fig, targets)

    fig.tight_layout(rect = (0, 0.07, 1, 1))

    return fig


def plot_somecountries_alltargets(results, targets = None,
                                  confidence_level = 0, colors = None,
                                  **kwargs):
    if targets is None:
        targets = model.targets.all_
    if colors is None:
        colors = common.colors_paired
    with seaborn.color_palette(colors, len(targets)):
        fig = plot_somecountries(results,
                                 targets,
                                 confidence_level = confidence_level,
                                 **kwargs)
    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))
    return fig


def plot_somecountries_pairedtargets(results, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    cp = seaborn.color_palette('colorblind')
    ix = [2, 0, 3, 1, 4, 5]
    # cp = seaborn.color_palette('Dark2')
    # ix = [1, 0, 3, 2, 5, 4]
    colors = [cp[i] for i in ix]

    filebase = common.get_filebase()
    figs = []
    for i in range(len(targets) // 2):
        targets_ = targets[2 * i : 2 * i + 2]
        with seaborn.color_palette(colors):
            fig = plot_somecountries(results, targets_, **kwargs)
        figs.append(fig)
        filebase_suffix = str(targets_[0]).replace(' ', '_')
        filebase_ = '{}_{}'.format(filebase, filebase_suffix)
        fig.savefig('{}.pdf'.format(filebase_))
        fig.savefig('{}.png'.format(filebase_))

    return figs


def _make_legend(fig, targets):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(targets, colors):
        handles.append(lines.Line2D([], [], color = c))
        labels.append(common.get_target_label(t))
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


def plot_country(results, country, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(targets) / 2))
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = (8.5, 11),
                                sharex = 'all', sharey = 'row')

    country_str = common.country_label_replacements.get(country, country)
    fig.suptitle(country_str, size = 'large', va = 'center')

    colors = common.colors_paired
    for (row, attr) in enumerate(common.effectiveness_measures):
        for col in range(ncols):
            ax = axes[row, col]
            targs = targets[2 * col : 2 * (col + 1)]
            colors_ = colors[2 * col : 2 * (col + 1)]

            if (ax.is_first_col() or ax.is_last_col()):
                attr_label = 'ylabel'
            else:
                attr_label = None

            _plot_cell(ax, results, country, targs, attr,
                       attr_label = attr_label,
                       colors = colors_,
                       **kwargs)

            if ax.is_last_col():
                ax.yaxis.set_ticks_position('right')
                ax.yaxis.set_label_position('right')
                ax.yaxis.get_label().set_rotation(270)

    # Make legend at bottom.
    with seaborn.color_palette(colors):
        _make_legend(fig, targets)

    fig.tight_layout(rect = (0, 0.055, 1, 0.985))

    return fig


def plot_allcountries(results, **kwargs):
    # countries = ['Global'] + sorted(model.datasheet.get_country_list())
    countries = sorted(model.datasheet.get_country_list())
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            try:
                fig = plot_country(results, country, **kwargs)
            except FileNotFoundError:
                print('\tfailed')
            else:
                pdf.savefig(fig)
            finally:
                pyplot.close(fig)


if __name__ == '__main__':
    confidence_level = 0.95

    with model.results.samples.stats.load() as results:
        # plot_country(results, 'South Africa',
        #              confidence_level = confidence_level)

        plot_somecountries_alltargets(results)

        # plot_somecountries_pairedtargets(results,
        #                                  confidence_level = confidence_level)

        plot_allcountries(results, confidence_level = confidence_level)

    pyplot.show()
