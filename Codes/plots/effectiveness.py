#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Add historical incidence and prevalence to plots.
'''

import os.path
import sys

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
               confidence_level,
               scale = None, units = None,
               country_label = None, attr_label = None,
               colors = None, alpha = 0.35):
    if colors is None:
        colors = seaborn.color_palette()

    info = common.get_stat_info(attr)

    CIkey = 'CI{:g}'.format(100 * confidence_level)

    if scale is not None:
        info.scale = scale
        if units is None:
            units = ''
        info.units = units

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
            ax.plot(common.t, numpy.asarray(v['median']) / info.scale,
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


def plot_somecountries(results, confidence_level = 0, **kwargs):
    with seaborn.color_palette(common.colors_paired):
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

                _plot_cell(ax, results, country, model.targets.all_, attr,
                           confidence_level,
                           country_label = country_label,
                           attr_label = attr_label,
                           **kwargs)

        common.make_legend(fig, model.targets.all_)

    fig.tight_layout(rect = (0, 0.07, 1, 1))

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))

    return fig


def plot_country(results, country, confidence_level = 0.95, **kwargs):
    nrows = len(common.effectiveness_measures)
    ncols = int(numpy.ceil(len(model.targets.all_) / 2))
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = (8.5, 11),
                                sharex = 'all', sharey = 'row')

    country_str = common.country_label_replacements.get(country, country)
    fig.suptitle(country_str, size = 'large', va = 'center')

    for (row, attr) in enumerate(common.effectiveness_measures):
        # Get common scale for row.
        info = common.get_stat_info(attr)
        if info.scale is None:
            data = []
            for target in model.targets.all_:
                try:
                    v = results[country][str(target)][attr]
                except tables.NoSuchNodeError:
                    pass
                else:
                    if confidence_level > 0:
                        CIkey = 'CI{:g}'.format(100 * confidence_level)
                        data.append(v[CIkey])
                    else:
                        data.append(v['median'])
            info.autoscale(data)

        for col in range(ncols):
            ax = axes[row, col]
            targs = model.targets.all_[2 * col : 2 * (col + 1)]
            colors = common.colors_paired[2 * col : 2 * (col + 1)]

            if (ax.is_first_col() or ax.is_last_col()):
                attr_label = 'ylabel'
            else:
                attr_label = None

            _plot_cell(ax, results, country, targs, attr,
                       confidence_level,
                       attr_label = attr_label,
                       colors = colors,
                       scale = info.scale, units = info.units,
                       **kwargs)

            if ax.is_last_col():
                ax.yaxis.set_ticks_position('right')
                ax.yaxis.set_label_position('right')
                ax.yaxis.get_label().set_rotation(270)

    with seaborn.color_palette(common.colors_paired):
        common.make_legend(fig, model.targets.all_)

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
    with model.results.samples.stats.load() as results:
        # plot_country(results, 'South Africa')

        plot_somecountries(results)

        pyplot.show()

        plot_allcountries(results)
