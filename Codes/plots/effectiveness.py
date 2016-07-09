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


alpha = 0.1

# Run each of these and each of these + vaccine.
targets_baseline = [model.targets.StatusQuo(),
                    model.targets.UNAIDS90(),
                    model.targets.UNAIDS95()]
targets = []
for target in targets_baseline:
    targets.extend([target,
                    model.targets.Vaccine(treatment_targets = target)])

# cp = seaborn.color_palette('colorblind')
# colors = (cp[2], cp[0])
# cp = seaborn.color_palette('Dark2')
# colors = (cp[1], cp[0])
colors = seaborn.color_palette('Paired', len(targets))

country_label_replacements = {
    'United States of America': 'United States'
}


def plotcell(ax, country, attr,
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

        avg, CI = common.getstats(v, alpha = alpha)
        ax.plot(t, avg / scale, color = colors[i], label = str(target),
                zorder = 2)
        ax.fill_between(t, CI[0] / scale, CI[1] / scale,
                        color = colors[i],
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


def plot_selected():
    fig = pyplot.figure(figsize = (8.5, 11))

    # Legend in tiny bottom row
    gs = gridspec.GridSpec(
        len(common.countries_to_plot) + 1, 4,
        height_ratios = ((1, ) * len(common.countries_to_plot) + (0.1, )))

    for (i, country) in enumerate(common.countries_to_plot):
        attr_label = 'title' if (i == 0) else None

        plotcell(fig.add_subplot(gs[i, 0]),
                 country,
                 'infected',
                 country_label = 'ylabel',
                 attr_label = attr_label)

        plotcell(fig.add_subplot(gs[i, 1]),
                 country,
                 'AIDS',
                 attr_label = attr_label)

        plotcell(fig.add_subplot(gs[i, 2]),
                 country,
                 'incidence_per_capita',
                 attr_label = attr_label)

        plotcell(fig.add_subplot(gs[i, 3]),
                 country,
                 'prevalence',
                 attr_label = attr_label)

    lines_ = [lines.Line2D([0], [0], color = colors[i])
              for i in range(len(targets))]
    axis = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
    axis.tick_params(labelbottom = False, labelleft = False)
    axis.grid(False)
    labels = list(map(str, targets))
    # Re-order.
    lines_ = lines_[0 : : 2] + lines_[1 : : 2]
    labels = labels[0 : : 2] + labels[1 : : 2]
    axis.legend(lines_, labels,
                loc = 'center',
                # ncol = len(targets),
                ncol = 2,
                frameon = False,
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
    common.countries_to_plot = list(common.countries_to_plot)
    common.countries_to_plot.remove('Global')

    plot_selected()

    # plot_all()

    pyplot.show()
