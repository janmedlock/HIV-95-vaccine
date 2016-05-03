#!/usr/bin/python3
'''
Calculate PRCCs.
'''

import os.path
import sys

from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import ticker
import numpy
from scipy import interpolate

sys.path.append(os.path.dirname(__file__))  # cwd for Sphinx.
sys.path.append('..')
import common
import model
import stats

import seaborn


parameter_name = dict(
    coital_acts_per_year = 'annual\nsex\nacts',
    death_years_lost_by_suppression = 'life-years lost:\non suppression',
    progression_rate_acute = 'acute\nprogression\nrate',
    suppression_rate = 'suppression\nrate',
    transmission_per_coital_act_acute = 'transmission\nper coital act:\nacute',
    transmission_per_coital_act_unsuppressed \
        = 'transmission\nper coital act:\nunsuppressed',
    transmission_per_coital_act_reduction_by_suppression \
        = 'transmission\nper coital act:\nreduction by\nsuppression'
)


def get_outcome_samples(country, stat, t):
    with model.results.Results(country) as results:
        t_, x = results.getfield('prevalence')
    y = x['Status Quo'] - x['90–90–90']
    interp = interpolate.interp1d(t_, y, axis = -1)
    outcome_samples = interp(t)
    return outcome_samples


def tornado(ax, country, outcome, t, parameter_samples, colors,
            parameter_names = None):
    outcome_samples = get_outcome_samples(country, outcome, t)

    n = numpy.shape(parameter_samples)[-1]

    if parameter_names is None:
        parameter_names = ['parameter[{}]'.format(i) for i in range(n)]

    rho = stats.prcc(parameter_samples, outcome_samples)

    ix = numpy.argsort(numpy.abs(rho))

    c = [colors[parameter_names[i]] for i in ix]

    patches = ax.barh(range(n), rho[ix],
                      height = 1, left = 0,
                      align = 'center',
                    color = c,
                      edgecolor = c)
    # ax.set_ylim(0.5, n + 0.5)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.yaxis.set_major_locator(ticker.NullLocator())
    ax.grid(True, which = 'both')

    return patches


if __name__ == '__main__':
    country = 'Global'
    outcomes = (
        ('infected', 'People Living with HIV'),
        ('AIDS', 'People with AIDS'),
        ('incidence_per_capita', 'HIV Incidence'),
        ('prevalence', 'HIV Prevelance'))
    times = (10, 20)

    parameter_samples = model.samples.load()

    # Get names.
    parameters = model.parameters.Parameters.get_rv_names()  
    parameter_names = [parameter_name[p] for p in parameters]

    # # Order parameters by abs(prcc).
    # rho = stats.prcc(parameter_samples, outcome_samples)
    # ix = numpy.argsort(numpy.abs(rho))[ : : -1]
    # parameter_samples = parameter_samples[:, ix]
    # parameters = [parameters[i] for i in ix]
    # parameter_names = [parameter_names[i] for i in ix]

    # Order colors by order of prccs in top left.
    outcome_samples = get_outcome_samples(country, outcomes[0], times[0])
    rho = stats.prcc(parameter_samples, outcome_samples)
    ix = numpy.argsort(numpy.abs(rho))[ : : -1]
    labels = [parameter_names[i] for i in ix]
    colors_ = seaborn.color_palette('Dark2', len(parameter_names))
    colors = {l: c for (l, c) in zip(labels, colors_)}

    nrow = len(times)
    ncol = len(outcomes) + 1
    legend_width = 0.7
    gs = gridspec.GridSpec(nrow, ncol,
                           width_ratios = [1] * (ncol - 1) + [legend_width])
    fig = pyplot.figure(figsize = (11, 8.5))
    sharedax = None
    for (i, t) in enumerate(times):
        for (j, x) in enumerate(outcomes):
            outcome, title = x
            ax = fig.add_subplot(gs[i, j],
                                 sharex = sharedax, sharey = sharedax)
            sharedax = ax
            patches_ = tornado(ax, country, outcome, t, parameter_samples,
                               colors,
                               parameter_names = parameter_names)
            if i == 0:
                ax.set_title(title)
            if i != nrow - 1:
                for l in ax.get_xticklabels():
                    l.set_visible(False)
                ax.xaxis.offsetText.set_visible(False)
            if j == 0:
                ax.set_ylabel(t + 2015)
            if j != 0:
                for l in ax.get_yticklabels():
                    l.set_visible(False)
                ax.yaxis.offsetText.set_visible(False)

            # Save for legend.
            if i == 0 and j == 0:
                patches = patches_

    fig.legend(patches[ : : -1], labels,
               loc = 'center right',
               labelspacing = 1,
               handleheight = 5)

    fig.tight_layout()

    fig.savefig('{}.png'.format(common.get_filebase()))
    fig.savefig('{}.pdf'.format(common.get_filebase()))

    pyplot.show()
