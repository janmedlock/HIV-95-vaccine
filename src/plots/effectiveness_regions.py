#!/usr/bin/python3
'''
Plot the effectiveness of interventions by region.
'''

import itertools
import os.path
import sys

from matplotlib import pyplot
from matplotlib import patches
from matplotlib import ticker
import numpy
import pandas
import seaborn
import tables

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


effectiveness_measures = ['new_infections', 'infected']

regions = model.regions.all_
if 'Global' in regions:
    regions.remove('Global')

targets = model.target.all_

region_labels = {
    'Global': 'Global',
    'Asia Pacific': 'Asia\n& The\nPacific',
    'Caribbean': 'The\nCarribean',
    'East and Southern Africa': 'Eastern &\nSouthern\nAfrica',
    'Eastern Europe and Central Asia': 'Eastern\nEurope &\nCentral Asia',
    'Latin America': 'Latin\nAmerica',
    'Middle East and North Africa': 'Middle\nEast &\nNorth Africa',
    'North America': 'North\nAmerica',
    'West and Central Africa': 'West &\nCentral\nAfrica',
    'Western Europe': 'Western &\nCentral\nEurope'
}


def _plot_stat(ax, results, regions, stat, confidence_level, **kwargs):
    CIkey = 'CI{:g}'.format(100 * confidence_level)

    info = common.get_stat_info(stat)

    idx = ['median', 'CIlower', 'CIupper']
    data = pandas.Panel(items = regions,
                        major_axis = targets,
                        minor_axis = idx,
                        dtype = float)
    for region, target in itertools.product(regions, targets):
        try:
            v = results[region][target][stat]
        except tables.NoSuchNodeError:
            pass
        else:
            # At the end time.
            data.loc[region, target, 'median'] = v['median'][..., -1]
            data.loc[region, target, ['CIlower', 'CIupper']] = v[CIkey][..., -1]

    if info.scale is None:
        info.autoscale(data.max().max())

    colors = seaborn.color_palette()

    pad = 0.2
    width = (1 - pad) / len(targets)
    for (i, target) in enumerate(targets):
        median = data.loc[:, target, 'median'].values
        CI = data.loc[:, target, ['CIlower', 'CIupper']].values
        left = numpy.arange(len(regions)) + i * width + pad / 2
        height = median / info.scale
        yerr = numpy.row_stack((median - CI[0], CI[1] - median)) / info.scale
        for region in regions:
            ax.bar(left, height, width, yerr = yerr,
                   linewidth = 0,
                   color = colors[i],
                   error_kw = dict(ecolor = 'black',
                                   elinewidth = 1,
                                   capthick = 1,
                                   capsize = 2,
                                   alpha = 0.1))

    ax.set_xticks(numpy.arange(len(regions)) + 0.5)
    ax.set_xticklabels([region_labels[r] for r in regions],
                       size = pyplot.rcParams['font.size'] - 1)

    ax.grid(False, which = 'both', axis = 'x')
    seaborn.despine(ax = ax, right = True, left = True)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(base = 5))
    ax.yaxis.set_major_formatter(common.UnitsFormatter(info.units))
    # One minor tick between major ticks.
    # ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    label = info.label.replace('\n', ' ')
    ax.set_ylabel(label,
                  va = 'baseline', ha = 'center',
                  labelpad = 5)


def _make_legend(fig):
    colors = seaborn.color_palette()
    handles = []
    labels = []
    for (t, c) in zip(targets, colors):
        handles.append(patches.Patch(color = c))
        labels.append(common.get_target_label(t))
    return fig.legend(handles, labels,
                      loc = 'lower center',
                      ncol = len(labels) // 2,
                      frameon = False)


def plot(confidence_level = 0.5, **kwargs):
    global targets
    targets = [str(t) for t in targets]

    with model.results.samples.stats.open_() as results:
        # Sort regions by first target, first stat.
        data = pandas.Series(index = regions,
                             dtype = float)
        for region in regions:
            try:
                v = results[region][targets[0]][effectiveness_measures[0]]
            except tables.NoSuchNodeError:
                pass
            else:
                # At the end time.
                data[region] = v['median'][..., -1]
        regions_sorted = data.sort_values(ascending = False).index

        nrows = len(effectiveness_measures)
        ncols = 1
        with seaborn.color_palette(common.colors_paired):
            with seaborn.axes_style('darkgrid'):
                fig, axes = pyplot.subplots(nrows, ncols,
                                            figsize = (common.width_1_5column,
                                                       4),
                                            sharex = 'col', sharey = 'none')
                for (ax, stat) in zip(axes, effectiveness_measures):
                    _plot_stat(ax, results, regions_sorted, stat,
                               confidence_level, **kwargs)
                    ax.tick_params(axis = 'x', pad = 11)
                    labels = ax.get_xticklabels()
                    ax.set_xticklabels(labels, verticalalignment = 'center')

                    seaborn.despine(ax = ax, bottom = True, left = True)
                _make_legend(fig)

    fig.tight_layout(h_pad = 1, w_pad = 0,
                     rect = (0, 0.06, 1, 1))

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))

    return fig


if __name__ == '__main__':
    plot()
    pyplot.show()
