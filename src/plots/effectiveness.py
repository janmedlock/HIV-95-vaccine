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
import stats
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
               plotevery = 1, scale = None, units = None,
               country_label = None, stat_label = None,
               colors = None, alpha = 0.35,
               jitter = 0.6, space_to_newline = False):
    if colors is None:
        colors = seaborn.color_palette()

    info = common.get_stat_info(stat)

    # Allow scaling across rows in plot_one().
    if scale is not None:
        info.scale = scale
    if units is not None:
        info.units = units
    if (scale is None) or (units is None):
        # Find scale and units.
        data = []
        for target in targets:
            if results[target] is not None:
                v = getattr(results[target], stat)
                # Store the largest one.
                if ci_bar > confidence_level:
                    data.append(stats.confidence_interval(v[:, -1], ci_bar))
                elif confidence_level > 0:
                    data.append(stats.confidence_interval(v[:, : : plotevery],
                                                          confidence_level))
                else:
                    data.append(stats.median(v[:, : : plotevery]))
        if info.scale is None:
            info.autoscale(data)
        if info.units is None:
            info.autounits(data)

    for (i, target) in enumerate(targets):
        if results[target] is not None:
            v = getattr(results[target], stat) / info.scale
            t = common.t[ : : plotevery]
            y = stats.median(v[:, : : plotevery])
            l = ax.plot(t, y,
                        label = common.get_target_label(target),
                        color = colors[i],
                        alpha = alpha0,
                        zorder = 2)

            if confidence_level > 0:
                CI = stats.confidence_interval(v[:, : : plotevery],
                                               confidence_level)
                # Draw borders of CI with high alpha,
                # which is why this is separate from fill_between().
                # lw = l[0].get_linewidth() / 2
                # for j in range(2):
                #     ax.plot(common.t, CI[j],
                #             color = colors[i],
                #             linewidth = lw,
                #             alpha = alpha0,
                #             zorder = 2)
                # Shade interior of CI, with low alpha.
                ax.fill_between(t, CI[0], CI[1],
                                facecolor = colors[i],
                                linewidth = 0,
                                alpha = alpha)

            if ci_bar > 0:
                mid = stats.median(v[:, -1])
                CIB = stats.confidence_interval(v[:, -1], ci_bar)
                yerr = numpy.reshape([mid - CIB[0], CIB[1] - mid], (-1, 1))
                eb = ax.errorbar(common.t[-1] + jitter * (i + 1),
                                 mid, yerr = yerr,
                                 fmt = 'none',  # Don't show midpoint.
                                 ecolor = colors[i],
                                 capsize = 3,
                                 alpha = alpha0)
                # Allow errorbar to draw outside of axes.
                _set_clip_on(eb, False)

    common.format_axes(ax, country, info, country_label, stat_label,
                       space_to_newline = space_to_newline)

    if stat == 'incidence_per_capita':
        ax.set_ylim(bottom = 0)


def _make_legend(fig, **kwargs):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(model.target.all_, colors):
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


def plot_one(country, confidence_level = 0.5, ci_bar = 0.9,
             figsize = (8.5 * 0.7, 6.5), plotevery = 1,
             **kwargs):
    fig = pyplot.figure(figsize = figsize)
    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(model.target.all_) / 2))
    gs = gridspec.GridSpec(nrows, ncols,
                           top = 0.975, bottom = 0.075,
                           left = 0.11, right = 0.98,
                           wspace = 0.2)

    fig.suptitle(country, size = 10, va = 'baseline', x = 0.545)

    results = common.get_country_results(country)
    axes = []
    for (row, stat) in enumerate(common.effectiveness_measures):
        # Get common scale for row.
        info = common.get_stat_info(stat)
        if (info.scale is None) or (info.units is None):
            data = []
            for target in model.target.all_:
                if results[target] is not None:
                    v = getattr(results[target], stat)
                    # Store the largest one.
                    if ci_bar > confidence_level:
                        data.append(stats.confidence_interval(v[:, -1],
                                                              ci_bar))
                    elif confidence_level > 0:
                        data.append(
                            stats.confidence_interval(v[:, : : plotevery],
                                                      confidence_level))
                    else:
                        data.append(stats.median(v[:, : : plotevery]))
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

            targs = model.target.all_[2 * col : 2 * (col + 1)]
            colors = common.colors_paired[2 * col : 2 * (col + 1)]

            if ax.is_first_col():
                stat_label = 'ylabel'
            else:
                stat_label = None

            _plot_cell(ax, results, country, targs, stat,
                       confidence_level,
                       ci_bar = ci_bar,
                       plotevery = plotevery,
                       stat_label = stat_label,
                       colors = colors,
                       scale = info.scale, units = info.units,
                       **kwargs)

            if stat_label == 'ylabel':
                if stat == 'infected':
                    offset = -0.2
                else:
                    offset = -0.25
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
                     loc = (0.12, 0),
                     columnspacing = 3.1)

    return fig


def plot_some(confidence_level = 0, ci_bar = 0, **kwargs):
    with seaborn.color_palette(common.colors_paired):
        ncols = len(common.countries_to_plot)
        nrows = len(common.effectiveness_measures)
        fig, axes = pyplot.subplots(nrows, ncols,
                                    figsize = (common.width_1_5column, 4),
                                    sharex = 'all', sharey = 'none')
        for (col, country) in enumerate(common.countries_to_plot):
            results = common.get_country_results(country)
            for (row, stat) in enumerate(common.effectiveness_measures):
                ax = axes[row, col]

                stat_label = 'ylabel' if ax.is_first_col() else None
                country_label = 'title' if ax.is_first_row() else None

                _plot_cell(ax, results, country, model.target.all_, stat,
                           confidence_level,
                           ci_bar = ci_bar,
                           country_label = country_label,
                           stat_label = stat_label,
                           space_to_newline = True,
                           **kwargs)

                ax.xaxis.set_tick_params(labelsize = 4.5)
                ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 4))

                if stat_label is not None:
                    if stat == 'new_infections':
                        ax.yaxis.labelpad -= 2
                    elif stat == 'infected':
                        ax.yaxis.labelpad -= 5
                    elif stat == 'dead':
                        ax.yaxis.labelpad -= 5

        _make_legend(fig)

    # Tweak.
    axes[0, 0].yaxis.set_major_locator(ticker.MultipleLocator(10))
    axes[0, 0].set_ylim(top = 50)
    axes[0, 1].set_ylim(top = 1000)
    axes[0, 2].yaxis.set_major_locator(ticker.MultipleLocator(50))
    axes[0, 3].yaxis.set_major_locator(ticker.MultipleLocator(2))
    axes[0, 3].set_ylim(top = 10)
    axes[0, 4].yaxis.set_major_locator(ticker.MultipleLocator(100))
    axes[0, 4].set_ylim(top = 400)
    axes[0, 5].yaxis.set_major_locator(ticker.MultipleLocator(250))
    axes[0, 5].set_ylim(top = 750)
    axes[1, 0].yaxis.set_major_locator(ticker.MultipleLocator(100))
    axes[1, 1].set_ylim(top = 100)
    axes[1, 2].yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    axes[1, 3].yaxis.set_major_locator(ticker.MultipleLocator(5))
    axes[1, 4].yaxis.set_major_locator(ticker.MultipleLocator(10))
    axes[1, 5].yaxis.set_major_locator(ticker.MultipleLocator(50))
    axes[1, 5].set_ylim(top = 250)
    axes[2, 0].set_ylim(bottom = 25, top = 45)
    axes[2, 1].yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    axes[2, 1].set_ylim(bottom = 0.5)
    axes[2, 2].yaxis.set_major_locator(ticker.MultipleLocator(25))
    axes[2, 2].set_ylim(bottom = 150)
    axes[2, 3].yaxis.set_major_locator(ticker.MultipleLocator(1))
    axes[2, 3].set_ylim(bottom = 4, top = 7)
    axes[2, 5].yaxis.set_major_locator(ticker.MultipleLocator(50))
    axes[3, 0].yaxis.set_major_locator(ticker.MultipleLocator(25))
    axes[3, 0].set_ylim(top = 125)
    axes[3, 2].yaxis.set_major_locator(ticker.MultipleLocator(25))
    axes[3, 2].set_ylim(top = 100)
    axes[3, 3].set_ylim(top = 8)
    axes[3, 4].yaxis.set_major_locator(ticker.MultipleLocator(50))
    axes[3, 5].yaxis.set_major_locator(ticker.MultipleLocator(200))

    fig.tight_layout(h_pad = 0.7, w_pad = 0,
                     rect = (0, 0.05, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    # plot_one('South Africa')
    plot_some()
    pyplot.show()
