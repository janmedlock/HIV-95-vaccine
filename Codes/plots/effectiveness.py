#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Add historical incidence and prevalence to plots.
'''

import itertools
import os.path
import sys

from matplotlib import gridspec
from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


country_label_replacements = {
    'United States of America': 'United States'
}


def plotcell(ax, country, targets, attr,
             confidence_level = 0.9,
             country_label = None, attr_label = None, legend = False):
    scale = 1
    percent = False
    if attr == 'infected':
        attr_str = 'People Living with HIV\n(M)'
        scale = 1e6
    elif attr == 'AIDS':
        attr_str = 'People with AIDS\n(1000s)'
        scale = 1e3
    elif attr == 'incidence_per_capita':
        attr_str = 'HIV Incidence\n(per M people per y)'
        scale = 1e-6
    elif attr == 'prevalence':
        attr_str = 'HIV Prevelance\n'
        percent = True
    else:
        raise ValueError("Unknown attr '{}'!".format(attr))

    if percent:
        scale = 1 / 100

    country_str = country_label_replacements.get(country, country)

    for (i, target) in enumerate(targets):
        t = model.results.data[(country, target, 't')]
        v = model.results.data[(country, target, attr)]

        avg, CI = common.getstats(v, alpha = 1 - confidence_level)
        lines = ax.plot(t, avg / scale,
                        label = common.get_target_label(target),
                        zorder = 2)
        if confidence_level > 0:
            color = lines[0].get_color()
            ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                            color = color,
                            alpha = 0.3)

    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    a = t[0]
    b = t[-1]
    xticks = list(range(int(t[0]), int(t[-1]), 10))
    if ((b - a) % 10) == 0:
        xticks.append(b)
    ax.set_xticks(xticks)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())

    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(attr_str, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(attr_str, size = 'medium')

    if legend:
        ax.legend(loc = 'upper left')


def plot_somecountries(targets = None, ncol = None, transpose_legend = False,
                       **kwargs):
    if targets is None:
        targets = model.targets.all_
    if ncol is None:
        ncol = len(targets)

    fig = pyplot.figure(figsize = (8.5, 11))
    # Legend in tiny bottom row
    gs = gridspec.GridSpec(
        len(common.countries_to_plot) + 1, 4,
        height_ratios = ((1, ) * len(common.countries_to_plot) + (0.1, )))
    for (i, country) in enumerate(common.countries_to_plot):
        attr_label = 'title' if (i == 0) else None

        plotcell(fig.add_subplot(gs[i, 0]),
                 country,
                 targets,
                 'infected',
                 country_label = 'ylabel',
                 attr_label = attr_label,
                 **kwargs)

        plotcell(fig.add_subplot(gs[i, 1]),
                 country,
                 targets,
                 'AIDS',
                 attr_label = attr_label,
                 **kwargs)

        plotcell(fig.add_subplot(gs[i, 2]),
                 country,
                 targets,
                 'incidence_per_capita',
                 attr_label = attr_label,
                 **kwargs)

        plotcell(fig.add_subplot(gs[i, 3]),
                 country,
                 targets,
                 'prevalence',
                 attr_label = attr_label,
                 **kwargs)

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


def plot_somecountries_alltargets(targets = None,
                                  confidence_level = 0,
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
        fig = plot_somecountries(targets,
                                 ncol = ncol,
                                 confidence_level = confidence_level,
                                 **kwargs)
    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))
    return fig


def plot_somecountries_pairedtargets(targets = None,
                                     **kwargs):
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
            fig = plot_somecountries(targets_, **kwargs)
        figs.append(fig)
        filebase_suffix = str(targets_[0]).replace(' ', '_')
        filebase_ = '{}_{}'.format(filebase, filebase_suffix)
        fig.savefig('{}.pdf'.format(filebase_))
        fig.savefig('{}.png'.format(filebase_))

    return figs


def plot_allcountries(targets = None, **kwargs):
    if targets is None:
        targets = model.targets.all_

    countries = ['Global'] + sorted(model.get_country_list())

    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for (i, country) in enumerate(countries):
            fig, axes = pyplot.subplots(4,
                                        figsize = (11, 8.5),
                                        sharex = True,
                                        squeeze = True)

            try:
                plotcell(axes[0],
                         country,
                         targets,
                         'infected',
                         attr_label = 'ylabel',
                         country_label = 'title',
                         legend = True,
                         **kwargs)

                plotcell(axes[1],
                         country,
                         targets,
                         'AIDS',
                         attr_label = 'ylabel',
                         **kwargs)

                plotcell(axes[2],
                         country,
                         targets,
                         'incidence_per_capita',
                         attr_label = 'ylabel',
                         **kwargs)

                plotcell(axes[3],
                         country,
                         targets,
                         'prevalence',
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

    # Remove 'Global' for now.
    common.countries_to_plot = list(common.countries_to_plot)
    if 'Global' in common.countries_to_plot:
        common.countries_to_plot.remove('Global')

    plot_somecountries_alltargets()

    # ixt = [0, 4, 5]  # StatusQuo, UNAIDS95, Vaccine(UNAIDS95)
    # cp = seaborn.color_palette('colorblind')
    # ixc = [2, 5, 1]
    # ixt = [0, 1, 4, 5]  # StatusQuo, Vaccine(StatusQuo), UNAIDS95, Vaccine(UNAIDS95)
    # cp = seaborn.color_palette('Paired', 8)
    # ixc = [4, 5, 0, 1, 2, 3, 6, 7]
    # targets_ = [model.targets.all_[i] for i in ixt]
    # colors = [cp[i] for i in ixc]
    # plot_somecountries_alltargets(targets_,
    #                               confidence_level = 0.5,
    #                               colors = colors,
    #                               transpose_legend = True)

    plot_somecountries_pairedtargets(confidence_level = confidence_level)

    # plot_allcountries(confidence_level = confidence_level)

    pyplot.show()
