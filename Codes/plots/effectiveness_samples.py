#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Add historical incidence and prevalence to plots.
'''

import itertools
import operator
import os.path
import sys

from matplotlib import gridspec
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


def _plot_cell(ax, results, country, targets, attr,
               confidence_level = 0.9,
               country_label = None, attr_label = None):
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
                            zorder = 2)

            if confidence_level > 0:
                CI = v[CIkey]
                color = lines[0].get_color()
                ax.fill_between(common.t,
                                numpy.asarray(CI[0]) / info.scale,
                                numpy.asarray(CI[1]) / info.scale,
                                color = color,
                                alpha = 0.4)

    common.format_axes(ax, country, info, country_label, attr_label)


def plot_somecountries(results, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    fig = pyplot.figure(figsize = (8.5, 7.5))
    # Legend in tiny bottom row
    ncols = len(common.countries_to_plot)
    nrows = len(common.effectiveness_measures) + 1
    legend_height_ratio = 0.3
    gs = gridspec.GridSpec(nrows, ncols,
                           height_ratios = ((1, ) * (nrows - 1)
                                            + (legend_height_ratio, )))
    for (col, country) in enumerate(common.countries_to_plot):
        attr_label = 'ylabel' if (col == 0) else None
        for (row, attr) in enumerate(common.effectiveness_measures):
            ax = fig.add_subplot(gs[row, col])
            country_label = 'title' if (row == 0) else None
            _plot_cell(ax, results, country, targets, attr,
                       country_label = country_label,
                       attr_label = attr_label,
                       **kwargs)
            if row != nrows - 2:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)

    # Make legend at bottom.
    ax = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
    _make_legend(ax, targets, usefigure = True)

    fig.tight_layout()

    return fig


def plot_somecountries_alltargets(results,
                                  targets = None,
                                  confidence_level = 0,
                                  colors = None,
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


def _make_legend(ax, targets, usefigure = False):
    ax.tick_params(labelbottom = False, labelleft = False)
    ax.grid(False)

    # Make legend at bottom.
    handles = []
    labels = []

    colors = seaborn.color_palette()
    for (t, c) in zip(targets, colors):
        handles.append(lines.Line2D([], [], color = c))
        labels.append(common.get_target_label(t))

    if usefigure:
        obj = ax.get_figure()
        loc = 'lower center'
    else:
        obj = ax
        loc = 'center'

    return obj.legend(handles, labels,
                      loc = loc,
                      ncol = len(labels) // 2,
                      frameon = False,
                      fontsize = 11,
                      numpoints = 1)


def plot_country(results, country, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    fig = pyplot.figure(figsize = (8.5, 11))
    country_str = common.country_label_replacements.get(country, country)
    fig.suptitle(country_str, size = 'medium')

    nrows = len(common.effectiveness_measures) + 2
    ncols = int(numpy.ceil(len(targets) / 2))
    title_height_ratio = 0.02
    legend_height_ratio = 0.2
    gs = gridspec.GridSpec(nrows, ncols,
                           height_ratios = ((title_height_ratio, )
                                            + (1, ) * (nrows - 2)
                                            + (legend_height_ratio, )))

    colors = common.colors_paired
    for (row, attr) in enumerate(common.effectiveness_measures):
        sharey = None
        for (col, ind) in enumerate(range(0, 2 * ncols, 2)):
            targs = targets[ind : ind + 2]
            colors_ = colors[ind : ind + 2]
            attr_label = 'ylabel' if (col == 0) else None
            with seaborn.color_palette(colors_):
                ax = fig.add_subplot(gs[row + 1, col], sharey = sharey)
                sharey = ax
                _plot_cell(ax, results, country, targs, attr,
                           attr_label = attr_label,
                           **kwargs)
            if row != nrows - 3:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)
            if col != 0:
                for l in ax.get_yticklabels():
                    l.set_visible(False)
                ax.yaxis.offsetText.set_visible(False)

    # Make legend at bottom.
    for (col, ind) in enumerate(range(0, 2 * ncols, 2)):
        targs = targets[ind : ind + 2]
        colors_ = colors[ind : ind + 2]
        with seaborn.color_palette(colors_):
            ax = fig.add_subplot(gs[-1, col], axis_bgcolor = 'none')
            _make_legend(ax, targs)

    fig.tight_layout()

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

        plot_somecountries_alltargets(results, confidence_level = 0.5)

        # plot_somecountries_pairedtargets(results,
        #                                  confidence_level = confidence_level)

        # plot_allcountries(results, confidence_level = confidence_level)

    pyplot.show()
