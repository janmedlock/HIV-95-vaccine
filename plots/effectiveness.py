#!/usr/bin/python3
'''
Plot the effectiveness of interventions.
'''

import os.path
import sys

from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import tables

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


alpha0 = 0.9


def _set_clip_on(obj, val):
    if obj is not None:
        try:
            obj.set_clip_on(val)
        except AttributeError:
            for x in obj:
                _set_clip_on(x, val)


def _plot_cell(ax, results, country, targets, stat,
               confidence_level, ci_bar,
               scale = None, units = None,
               country_label = None, stat_label = None,
               colors = None, alpha = 0.35,
               jitter = 0.6, plotevery = 1):
    if colors is None:
        colors = seaborn.color_palette()

    CIkey = 'CI{:g}'.format(100 * confidence_level)
    CIBkey = 'CI{:g}'.format(100 * ci_bar)

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
            # Store the largest one.
            if ci_bar > 0:
                data.append(v[CIBkey])
            elif confidence_level > 0:
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
            t = common.t[ : : plotevery]
            y = numpy.asarray(v['median'])[ : : plotevery] / info.scale
            l = ax.plot(t, y,
                        label = common.get_target_label(target),
                        color = colors[i],
                        alpha = alpha0,
                        zorder = 2)

            if confidence_level > 0:
                CI = v[CIkey]
                # Draw borders of CI with high alpha,
                # which is why this is separate from fill_between().
                # lw = l[0].get_linewidth() / 2
                # for j in range(2):
                #     ax.plot(common.t,
                #             numpy.asarray(CI[j]) / info.scale,
                #             color = colors[i],
                #             linewidth = lw,
                #             alpha = alpha0,
                #             zorder = 2)
                # Shade interior of CI, with low alpha.
                y1 = numpy.asarray(CI[0])[ : : plotevery] / info.scale
                y2 = numpy.asarray(CI[1])[ : : plotevery] / info.scale
                ax.fill_between(t, y1, y2,
                                facecolor = colors[i],
                                linewidth = 0,
                                alpha = alpha)

            if ci_bar > 0:
                mid = v['median'][-1]
                CIB = v[CIBkey][:, -1]
                yerr = [mid - CIB[0], CIB[1] - mid]
                eb = ax.errorbar(common.t[-1] + jitter * (i + 1),
                                 mid / info.scale,
                                 yerr = (numpy.reshape(yerr, (-1, 1))
                                         / info.scale),
                                 fmt = 'none',  # Don't show midpoint.
                                 ecolor = colors[i],
                                 capsize = 3,
                                 alpha = alpha0)
                # Allow errorbar to draw outside of axes.
                _set_clip_on(eb, False)

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


def _plot_one(results, country, confidence_level = 0.5, ci_bar = 0.9,
              figsize = (8.5 * 0.7, 6.5), **kwargs):
    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(model.targets.all_) / 2))
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = figsize,
                                sharex = 'all', sharey = 'row')

    country_name = common.get_country_label(country)
    fig.suptitle(country_name, size = 10, va = 'center')

    CIkey = 'CI{:g}'.format(100 * confidence_level)
    CIBkey = 'CI{:g}'.format(100 * ci_bar)

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
                # Store the largest one.
                if ci_bar > 0:
                    data.append(v[CIBkey])
                elif confidence_level > 0:
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

            if ax.is_first_col():
                stat_label = 'ylabel'
            else:
                stat_label = None

            _plot_cell(ax, results, country, targs, stat,
                       confidence_level,
                       ci_bar = ci_bar,
                       stat_label = stat_label,
                       colors = colors,
                       scale = info.scale, units = info.units,
                       **kwargs)

    with seaborn.color_palette(common.colors_paired):
        _make_legend(fig)

    fig.tight_layout(rect = (0, 0.055, 1, 0.985))

    return fig


def plot_one(country, **kwargs):
    with model.results.samples.stats.open_() as results:
        return _plot_one(results, country, **kwargs)


def plot_some(confidence_level = 0, ci_bar = 0, **kwargs):
    with model.results.samples.stats.open_() as results:
        with seaborn.color_palette(common.colors_paired):
            ncols = len(common.countries_to_plot)
            nrows = len(common.effectiveness_measures)
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = (common.width_1_5column, 4),
                                        sharex = 'all', sharey = 'none')
            for (col, country) in enumerate(common.countries_to_plot):
                for (row, stat) in enumerate(common.effectiveness_measures):
                    ax = axes[row, col]

                    stat_label = 'ylabel' if ax.is_first_col() else None
                    country_label = 'title' if ax.is_first_row() else None

                    _plot_cell(ax, results, country, model.targets.all_, stat,
                               confidence_level,
                               ci_bar = ci_bar,
                               country_label = country_label,
                               stat_label = stat_label,
                               **kwargs)

                    ax.xaxis.set_tick_params(labelsize = 5)
                    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 4))
                    if country_label is not None:
                        t = ax.set_title(ax.get_title().replace(' ', '\n'),
                                         va = 'center')
                        t.set_y(1.07)

            _make_legend(fig)

    fig.tight_layout(h_pad = 0.7, w_pad = 0,
                     rect = (0, 0.05, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_some()
    pyplot.show()
