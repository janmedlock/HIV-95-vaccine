#!/usr/bin/python3
'''
Calculate PRCCs and make tornado plots.

.. todo:: Clean up similarity with sensitivity.py.
'''

import os.path
import sys

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


def get_outcome_samples(country, targets, stat, times):
    results = (model.results.samples.open_(country, target)
               for target in targets)
    x, y =  (numpy.asarray(getattr(r, stat)) for r in results)
    z = x - y
    interp = interpolate.interp1d(common.t, z, axis = -1)
    outcome_samples = interp(times)
    return outcome_samples


def tornado(ax, country, targets, outcome, t, parameter_samples,
            colors, parameter_names = None, ylabels = 'left'):
    outcome_samples = get_outcome_samples(country, targets,
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
    country = 'Global'
    outcome = 'new_infections'
    baseline = model.targets.StatusQuo()
    targets = [baseline, model.targets.Vaccine(treatment_targets = baseline)]
    targets = list(map(str, targets))
    # times = (2025, 2035)
    times = (2035, )

    figsize = (5, 6)
    palette = 'Dark2'

    parameter_samples = model.samples.load()
    # Get fancy names.
    parameter_names = common.parameter_names

    # Order colors by order of prccs for 1st time.
    outcome_samples = get_outcome_samples(country, targets,
                                          outcome, times[0])
    rho = stats.prcc(parameter_samples, outcome_samples)
    ix = numpy.argsort(numpy.abs(rho))[ : : -1]
    labels = [parameter_names[i] for i in ix]
    colors_ = seaborn.color_palette(palette, len(parameter_names))
    colors = {l: c for (l, c) in zip(labels, colors_)}

    nrows = 1
    ncols = len(times)
    fig, axes = pyplot.subplots(nrows, ncols,
                                figsize = figsize,
                                sharex = 'all')

    if isinstance(axes, pyplot.Axes):
        axes = [axes]

    for (ax, t) in zip(axes, times):
        if ax.is_first_col():
            ylabels = 'left'
        elif ax.is_last_col():
            ylabels = 'right'
        else:
            ylabels = 'none'
        tornado(ax, country, targets, outcome, t,
                parameter_samples, colors,
                parameter_names = parameter_names,
                ylabels = ylabels)
        ax.set_xlabel('PRCC')
        # Make x-axis limits symmetric.
        xmin, xmax = ax.get_xlim()
        xabs = max(abs(xmin), abs(xmax))
        ax.set_xlim(- xabs, xabs)
        # ax.set_title(t)

    fig.tight_layout()

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(fig, '{}.png'.format(common.get_filebase()))


if __name__ == '__main__':
    tornados()

    pyplot.show()
