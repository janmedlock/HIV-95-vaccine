#!/usr/bin/python3
'''
Calculate PRCCs and make tornado plots.
'''

import os.path
import sys

from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import ticker
import numpy
from scipy import interpolate

sys.path.append(os.path.dirname(__file__))  # cwd for Sphinx.
import common
import stats
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model



def get_outcome_samples(results, country, targets, attr, times):
    t = results[country][targets[0]].t
    x, y =  (numpy.asarray(getattr(results[country][target], attr))
             for target in targets)
    z = x - y
    interp = interpolate.interp1d(t, z, axis = -1)
    outcome_samples = interp(times)
    return outcome_samples


def tornado(ax, results, country, targets, outcome, t, parameter_samples,
            colors, parameter_names = None, ylabels = 'left'):
    outcome_samples = get_outcome_samples(results, country, targets,
                                          outcome, t)

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
    ax.tick_params(axis = 'both', which = 'both',
                   top = False, bottom = False, right = False, left = False)
    ax.grid(True, which = 'both')
    ax.grid(False, axis = 'y', which = 'both')

    ax.yaxis.set_ticks_position(ylabels)

    return patches


def tornados():
    # country = 'Global'
    country = 'South Africa'
    outcome = 'new_infections'
    baseline = model.targets.StatusQuo()
    targets = [baseline, model.targets.Vaccine(treatment_targets = baseline)]
    targets = list(map(str, targets))
    times = (2025, 2035)

    figsize = (8, 6)
    palette = 'Dark2'

    parameter_samples = model.samples.load()
    # Get fancy names.
    parameter_names = common.parameter_names

    with model.results.ResultsCache() as results:
        # Order colors by order of prccs for 1st time.
        outcome_samples = get_outcome_samples(results, country, targets,
                                              outcome, times[0])
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
            tornado(ax, results, country, targets, outcome, t,
                    parameter_samples, colors,
                    parameter_names = parameter_names,
                    ylabels = ylabels)
            ax.set_xlabel('PRCC')
            ax.set_title(t)

    fig.tight_layout()

    fig.savefig('{}.png'.format(common.get_filebase()))
    fig.savefig('{}.pdf'.format(common.get_filebase()))


if __name__ == '__main__':
    tornados()

    pyplot.show()
