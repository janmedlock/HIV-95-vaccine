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
               country_label = None, attr_label = None, legend = False):
    info = common.get_stat_info(attr)

    CIkey = 'CI{:g}'.format(100 * confidence_level)

    if info.scale is None:
        data = []
        for target in targets:
            try:
                v = results[country][target][attr]
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
            v = results[country][target][attr]
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
                                alpha = 0.3)

    common.format_axes(ax, country, info, country_label, attr_label)

    if legend:
        ax.legend(loc = 'upper left')


def plot_somecountries(results,
                       targets = None, ncol = None, transpose_legend = False,
                       **kwargs):
    if targets is None:
        targets = model.targets.all_
    targets = list(map(str, targets))
    if ncol is None:
        ncol = len(targets)

    fig = pyplot.figure(figsize = (8.5, 7.5))
    # Legend in tiny bottom row
    ncols = len(common.countries_to_plot)
    nrows = len(common.effectiveness_measures) + 1
    legend_height_ratio = 0.1
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
    axes = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
    axes.tick_params(labelbottom = False, labelleft = False)
    axes.grid(False)

    if transpose_legend:
        # Instead of the legend
        # e.g. with len(targets) = 6 and ncol = 3,
        # [[0, 1, 2],
        #  [3, 4, 5]]
        # we want the legend
        # [[0, 2, 4],
        #  [1, 3, 5]]
        # so we reorder both targets and prop_cycler to
        # [0, 2, 4, 1, 3, 5].
        def transpose(x, ncol):
            x = list(x)
            nrow = int(numpy.ceil(len(x) / ncol))
            y = (x[i : : nrow] for i in range(nrow))
            return itertools.chain.from_iterable(y)
        targets_ = transpose(targets, ncol)
        props = (next(axes._get_lines.prop_cycler)
                 for _ in range(len(targets)))
        prop_cycler = transpose(props, ncol)
    else:
        targets_ = targets
        prop_cycler = axes._get_lines.prop_cycler

    # Dummy invisible lines.
    for target in targets_:
        axes.plot(0, 0,
                  label = common.get_target_label(target),
                  visible = False,
                  **next(prop_cycler))
    legend = axes.legend(loc = 'center',
                         ncol = ncol,
                         frameon = False,
                         fontsize = 'medium')
    # Make legend lines visible.
    for line in legend.get_lines():
        line.set_visible(True)

    fig.tight_layout()

    return fig


def plot_somecountries_alltargets(results,
                                  targets = None,
                                  confidence_level = 0.5,
                                  ncol = None,
                                  colors = None,
                                  **kwargs):
    if targets is None:
        targets = model.targets.all_
    if ncol is None:
        ncol = len(targets) // 2
    if colors is None:
        colors = common.colors_paired
    with seaborn.color_palette(colors, len(targets)):
        fig = plot_somecountries(results,
                                 targets,
                                 ncol = ncol,
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


def plot_allcountries(results, targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    countries = ['Global'] + sorted(model.get_country_list())

    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for (i, country) in enumerate(countries):
            fig, axes = pyplot.subplots(4,
                                        figsize = (8,5, 11),
                                        sharex = True,
                                        squeeze = True)

            try:
                for (row, attr) in enumerate(common.effectiveness_measures):
                    country_label = 'title' if (row == 0) else None
                    _plot_cell(axes[row],
                               results,
                               country,
                               targets,
                               attr,
                               country_label = country_label,
                               attr_label = 'ylabel',
                               **kwargs)
            except FileNotFoundError:
                pass
            else:
                fig.tight_layout()
                pdf.savefig(fig)
            finally:
                pyplot.close(fig)


if __name__ == '__main__':
    confidence_level = 0.9

    with model.results.samples.stats.load() as results:
        plot_somecountries_alltargets(results)

        # plot_somecountries_pairedtargets(results,
        #                                  confidence_level = confidence_level)

        # plot_allcountries(results, confidence_level = confidence_level)

    pyplot.show()
