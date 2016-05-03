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
            parameter_names = None, ylabels = 'left'):
    outcome_samples = get_outcome_samples(country, outcome, t)

    n = numpy.shape(parameter_samples)[-1]

    if parameter_names is None:
        parameter_names = ['parameter[{}]'.format(i) for i in range(n)]

    rho = stats.prcc(parameter_samples, outcome_samples)

    ix = numpy.argsort(numpy.abs(rho))

    labels = [parameter_names[i] for i in ix]
    c = [colors[l] for l in labels]

    h = range(n)
    patches = ax.barh(h, rho[ix],
                      height = 1, left = 0,
                      align = 'center',
                      color = c,
                      edgecolor = c)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.set_yticks(h)
    ax.set_ylim(- 0.5, n - 0.5)
    ax.set_yticklabels(labels)
    ax.grid(True, which = 'both')
    ax.grid(False, axis = 'y', which = 'both')

    ax.yaxis.set_ticks_position(ylabels)

    return patches


def tornados():
    country = 'Global'
    outcome = 'prevalence'
    times = (10, 20)

    figsize = (8, 5)
    palette = 'Dark2'

    parameter_samples = model.samples.load()
    parameters = model.parameters.Parameters.get_rv_names()   # Get names.
    parameter_names = [parameter_name[p] for p in parameters] # Get fancy names.

    # Order colors by order of prccs for 1st time.
    outcome_samples = get_outcome_samples(country, outcome, times[0])
    rho = stats.prcc(parameter_samples, outcome_samples)
    ix = numpy.argsort(numpy.abs(rho))[ : : -1]
    labels = [parameter_names[i] for i in ix]
    colors_ = seaborn.color_palette(palette, len(parameter_names))
    colors = {l: c for (l, c) in zip(labels, colors_)}

    gs = gridspec.GridSpec(1, len(times))
    fig = pyplot.figure(figsize = figsize)
    sharedax = None
    for (i, t) in enumerate(times):
        ax = fig.add_subplot(gs[0, i],
                             sharex = sharedax)
        sharedax = ax

        if i == 0:
            ylabels = 'left'
        elif i == len(times) - 1:
            ylabels = 'right'
        else:
            ylabels = 'none'
        tornado(ax, country, outcome, t, parameter_samples,
                colors,
                parameter_names = parameter_names,
                ylabels = ylabels)
        ax.set_xlabel('PRCC')
        ax.set_title(t + 2015)

    fig.tight_layout()

    fig.savefig('{}.png'.format(common.get_filebase()))
    fig.savefig('{}.pdf'.format(common.get_filebase()))


if __name__ == '__main__':
    tornados()

    pyplot.show()
