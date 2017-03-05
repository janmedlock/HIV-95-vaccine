#!/usr/bin/python3
'''
Plot the effectiveness of interventions.
'''

import os.path
import sys

from matplotlib import gridspec
from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
import numpy
import seaborn

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
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
               jitter = 0.6, plotevery = 1,
               space_to_newline = False):
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

    common.format_axes(ax, country, info, country_label, stat_label,
                       space_to_newline = space_to_newline)


def _make_legend(fig, **kwargs):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(model.targets.all_, colors):
        handles.append(lines.Line2D([], [], color = c, alpha = alpha0))
        labels.append(common.get_target_label(t))
    if 'loc' not in kwargs:
        kwargs['loc'] = 'lower center'
    if 'ncol' not in kwargs:
        kwargs['ncol'] = len(labels) // 2
    if 'frameon' not in kwargs:
        kwargs['frameon'] = False
    return fig.legend(handles, labels,
                      **kwargs)


def _plot_one(results, country, confidence_level = 0.5, ci_bar = 0.9,
              figsize = (8.5 * 0.7, 6.5),
              **kwargs):
    fig = pyplot.figure(figsize = figsize)
    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(model.targets.all_) / 2))
    gs = gridspec.GridSpec(nrows, ncols,
                           top = 0.975, bottom = 0.075,
                           left = 0.09, right = 0.98,
                           wspace = 0.15)

    fig.suptitle(country, size = 10, va = 'baseline', x = 0.535)

    CIkey = 'CI{:g}'.format(100 * confidence_level)
    CIBkey = 'CI{:g}'.format(100 * ci_bar)

    axes = []
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

        axes.append([])
        for col in range(ncols):
            if row == 0:
                sharex = None
            else:
                sharex = axes[0][col]
            if col == 0:
                sharey = None
            else:
                sharey = axes[row][0]

            ax = fig.add_subplot(gs[row, col],
                                 sharex = sharex,
                                 sharey = sharey)
            axes[row].append(ax)

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

            if stat_label == 'ylabel':
                if stat == 'infected':
                    offset = -0.165
                else:
                    offset = -0.2
                ax.yaxis.set_label_coords(offset, 0.5)

            if not ax.is_last_row():
                for label in ax.get_xticklabels():
                    label.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)

            if not ax.is_first_col():
                for label in ax.get_yticklabels():
                    label.set_visible(False)
                ax.yaxis.offsetText.set_visible(False)

    with seaborn.color_palette(common.colors_paired):
        _make_legend(fig,
                     loc = (0.132, 0),
                     columnspacing = 6.8)

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
                               space_to_newline = True,
                               **kwargs)

                    ax.xaxis.set_tick_params(labelsize = 5)
                    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 4))

                    if stat_label is not None:
                        if stat == 'new_infections':
                            ax.yaxis.labelpad -= 2
                        elif stat == 'infected':
                            ax.yaxis.labelpad -= 6
                        elif stat == 'dead':
                            ax.yaxis.labelpad -= 5

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
