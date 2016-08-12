#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Try to get Cairo into multi-page PDFs.

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


alpha0 = 0.9


def _plot_cell(ax, results, country, targets, stat,
               confidence_level,
               scale = None, units = None,
               country_label = None, stat_label = None,
               colors = None, alpha = 0.35):
    if colors is None:
        colors = seaborn.color_palette()

    CIkey = 'CI{:g}'.format(100 * confidence_level)

    info = common.get_stat_info(stat)

    # Allow scaling across rows in _plot_one().
    if scale is not None:
        info.scale = scale
    if units is not None:
        info.units = units
    data = []
    for target in targets:
        try:
            v = results[country][str(target)][stat]
        except tables.NoSuchNodeError:
            pass
        else:
            if confidence_level > 0:
                data.append(v[CIkey])
            else:
                data.append(v['median'])
    if info.scale is None:
        info.autoscale(data)
    if info.units is None:
        info.autounits(data)

    for (i, target) in enumerate(targets):
        try:
            v = results[country][str(target)][stat]
        except tables.NoSuchNodeError:
            pass
        else:
            l = ax.plot(common.t, numpy.asarray(v['median']) / info.scale,
                        label = common.get_target_label(target),
                        color = colors[i],
                        alpha = alpha0,
                        zorder = 2)

            if confidence_level > 0:
                CI = v[CIkey]
                # Draw borders of CI with alpha = 1,
                # which is why this is separate from fill_between().
                lw = l[0].get_linewidth() / 2
                for j in range(2):
                    ax.plot(common.t,
                            numpy.asarray(CI[j]) / info.scale,
                            color = colors[i],
                            linewidth = lw,
                            alpha = alpha0,
                            zorder = 2)
                # Shade interior of CI.
                ax.fill_between(common.t,
                                numpy.asarray(CI[0]) / info.scale,
                                numpy.asarray(CI[1]) / info.scale,
                                facecolor = colors[i],
                                linewidth = 0,
                                alpha = alpha)

    common.format_axes(ax, country, info, country_label, stat_label)


def _make_legend(fig, **kwargs):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(model.targets.all_, colors):
        handles.append(lines.Line2D([], [], color = c, alpha = alpha0))
        labels.append(common.get_target_label(t))
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False,
                      **kwargs)


def _plot_one(results, country, confidence_level = 0.5, **kwargs):
    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(model.targets.all_) / 2))
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = (8.5, 11),
                                sharex = 'all', sharey = 'row')

    country_name = common.get_country_label(country)
    fig.suptitle(country_name, size = 15, va = 'center')

    for (row, stat) in enumerate(common.effectiveness_measures):
        # Get common scale for row.
        info = common.get_stat_info(stat)
        data = []
        for target in model.targets.all_:
            try:
                v = results[country][str(target)][stat]
            except tables.NoSuchNodeError:
                pass
            else:
                if confidence_level > 0:
                    CIkey = 'CI{:g}'.format(100 * confidence_level)
                    data.append(v[CIkey])
                else:
                    data.append(v['median'])
        if info.scale is None:
            info.autoscale(data)
        if info.units is None:
            info.autounits(data)

        for col in range(ncols):
            ax = axes[row, col]
            targs = model.targets.all_[2 * col : 2 * (col + 1)]
            colors = common.colors_paired[2 * col : 2 * (col + 1)]

            if (ax.is_first_col() or ax.is_last_col()):
                stat_label = 'ylabel'
            else:
                stat_label = None

            _plot_cell(ax, results, country, targs, stat,
                       confidence_level,
                       stat_label = stat_label,
                       colors = colors,
                       scale = info.scale, units = info.units,
                       **kwargs)

            ax.tick_params(labelsize = 11)
            ax.tick_params(axis = 'x', pad = 8)
            ax.yaxis.get_label().set_size(12)

            if ax.is_last_col():
                ax.yaxis.set_ticks_position('right')
                ax.yaxis.set_label_position('right')
                ax.yaxis.get_label().set_rotation(270)
                ax.yaxis.labelpad = 26
            

    with seaborn.color_palette(common.colors_paired):
        _make_legend(fig, fontsize = 12, columnspacing = 5)

    fig.tight_layout(rect = (0, 0.055, 1, 0.985))

    return fig


def plot_one(country, **kwargs):
    with model.results.samples.stats.open_() as results:
        return _plot_one(results, country, **kwargs)


def plot_all(**kwargs):
    with model.results.samples.stats.open_() as results:
        filename = '{}_all.pdf'.format(common.get_filebase())
        with backend_pdf.PdfPages(filename) as pdf:
            for region_or_country in common.all_regions_and_countries:
                print(region_or_country)
                fig = _plot_one(results, region_or_country, **kwargs)
                pdf.savefig(fig)
                pyplot.close(fig)

    common.pdfoptimize(filename)
    # Use pdftk to add author etc.
    common.pdf_add_info(filename, Author = common.author)


def plot_some(confidence_level = 0, **kwargs):
    with model.results.samples.stats.open_() as results:
        with seaborn.color_palette(common.colors_paired):
            ncols = len(common.countries_to_plot)
            nrows = len(common.effectiveness_measures)
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = (common.width_2column, 4.75),
                                        sharex = 'all', sharey = 'none')
            for (col, country) in enumerate(common.countries_to_plot):
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = axes[row, col]

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, country, model.targets.all_, stat,
                               confidence_level,
                               country_label = country_label,
                               stat_label = stat_label,
                               **kwargs)

            _make_legend(fig)

    fig.tight_layout(h_pad = 0.7, w_pad = 0,
                     rect = (0, 0.04, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_some()
    pyplot.show()

    plot_all()
