#!/usr/bin/python3
'''
Plot the effectiveness of interventions.

.. todo:: Add historical incidence and prevalence to plots.
'''

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


alpha = 0.5

keys_ordered = ('Status Quo', '90–90–90')

cp = seaborn.color_palette('colorblind')
colors = {'Status Quo': cp[2],
          '90–90–90': cp[0]}
# cp = seaborn.color_palette('Dark2')
# colors = {'Status Quo': cp[1],
#           '90–90–90': cp[0]}

def plotcell(ax, tx,
             scale = 1, percent = False,
             xlabel = None, ylabel = None, title = None, legend = True):
    t, x = tx

    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(max(x) for x in stats.values()) > 1e6:
            scale = 1e6
        else:
            scale = 1e3

    for k in keys_ordered:
        v = x[k]
        avg, CI = common.getstats(v, alpha = alpha)
        ax.plot(t, avg / scale, color = colors[k], label = k,
                zorder = 2)
        ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                        color = colors[k],
                        alpha = 0.3)

    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(data_start_year, int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'medium')
    if title is not None:
        ax.set_title(title, size = 'medium')
    if legend:
        ax.legend(loc = 'upper left')


def plot_selected():
    fig = pyplot.figure(figsize = (8.5, 11))

    # Legend in tiny bottom row
    gs = gridspec.GridSpec(
        len(common.countries_to_plot) + 1, 4,
        height_ratios = ((1, ) * len(common.countries_to_plot) + (0.1, )))

    for (i, country) in enumerate(common.countries_to_plot):
        with model.results.Results(country) as results:
            if country == 'United States of America':
                ylabel = 'United States'
            else:
                ylabel = country

            axis = fig.add_subplot(gs[i, 0])
            plotcell(axis,
                     results.getfield('infected'),
                     scale = 1e6,
                     ylabel = ylabel,
                     legend = False,
                     title = ('People Living with HIV\n(M)'
                              if (i == 0) else None))

            axis = fig.add_subplot(gs[i, 1])
            plotcell(axis,
                     results.getfield('AIDS'),
                     scale = 1e3,
                     legend = False,
                     title = ('People with AIDS\n(1000s)'
                              if (i == 0) else None))

            axis = fig.add_subplot(gs[i, 2])
            plotcell(axis,
                     results.getfield('incidence_per_capita'),
                     scale = 1e-6,
                     legend = False,
                     title = ('HIV Incidence\n(per M people per y)'
                              if (i == 0) else None))

            axis = fig.add_subplot(gs[i, 3])
            plotcell(axis,
                     results.getfield('prevalence'),
                     percent = True,
                     legend = False,
                     title = ('HIV Prevelance\n'
                              if (i == 0) else None))

    lines_ = [lines.Line2D([0], [0], color = colors[k])
              for k in keys_ordered]
    labels = keys_ordered
    axis = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
    axis.tick_params(labelbottom = False, labelleft = False)
    axis.grid(False)
    axis.legend(lines_, labels,
                loc = 'center',
                ncol = len(labels),
                frameon = True,
                fontsize = 'medium')

    fig.tight_layout()

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


def plot_all():
    countries = ['Global'] + sorted(model.get_country_list())

    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for (i, country) in enumerate(countries):
            with model.results.Results(country) as results:
                if country == 'United States of America':
                    title = 'United States'
                else:
                    title = country

                fig, axes = pyplot.subplots(4,
                                            figsize = (11, 8.5),
                                            sharex = True,
                                            squeeze = True)

                try:
                    plotcell(axes[0],
                             results.getfield('infected'),
                             scale = 1e6,
                             ylabel = 'People Living with HIV\n(M)',
                             legend = True,
                             title = title)

                    plotcell(axes[1],
                             results.getfield('AIDS'),
                             scale = 1e3,
                             ylabel = 'People with AIDS\n(1000s)',
                             legend = False)

                    plotcell(axes[2],
                             results.getfield('incidence_per_capita'),
                             scale = 1e-6,
                             ylabel = 'HIV Incidence\n(per M people per y)',
                             legend = False)

                    plotcell(axes[3],
                             results.getfield('prevalence'),
                             percent = True,
                             ylabel = 'HIV Prevelance\n',
                             legend = False)
                except FileNotFoundError:
                    pass
                else:
                    fig.tight_layout()
                    pdf.savefig(fig)
                finally:
                    pyplot.close(fig)


if __name__ == '__main__':
    plot_selected()

    plot_all()

    pyplot.show()
