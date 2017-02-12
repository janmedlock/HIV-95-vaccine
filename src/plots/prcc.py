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
import seaborn

sys.path.append(os.path.dirname(__file__))  # cwd for Sphinx.
import common
import stats
sys.path.append('..')
import model


def get_outcome_samples(results, country, targets, stat, times):
    x, y =  (numpy.asarray(getattr(results[country][str(target)], stat))
             for target in targets)
    z = x - y
    interp = interpolate.interp1d(common.t, z, axis = -1)
    outcome_samples = interp(times)
    return outcome_samples


def tornado(ax, results, country, targets, outcome, t, parameter_samples,
            colors, parameter_names = None, errorbars = False):
    outcome_samples = get_outcome_samples(results, country, targets,
                                          outcome, t)

    n = numpy.shape(parameter_samples)[-1]

    if parameter_names is None:
        parameter_names = ['parameter[{}]'.format(i) for i in range(n)]

    rho = stats.prcc(parameter_samples, outcome_samples)
    CI = stats.prcc_CI(rho, len(outcome_samples))
    xerr = numpy.row_stack((rho - CI[:, 0], CI[:, 1] - rho))

    ix = numpy.argsort(numpy.abs(rho))

    labels = [parameter_names[i] for i in ix]
    c = [colors[l] for l in labels]

    h = range(n)
    if errorbars:
        kwds = dict(xerr = xerr[:, ix],
                    error_kw = dict(ecolor = 'black',
                                    elinewidth = 1.5,
                                    capthick = 1.5,
                                    capsize = 5,
                                    alpha = 0.9))
    else:
        kwds = dict()

    patches = ax.barh(h, rho[ix],
                      height = 1, left = 0,
                      align = 'center',
                      color = c,
                      edgecolor = c,
                      **kwds)

    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:g}'))
    # ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.tick_params(labelsize = pyplot.rcParams['font.size'] + 1)
    ax.tick_params(axis = 'y', pad = 35)

    ax.set_yticks(h)
    ax.set_ylim(- 0.5, n - 0.5)
    ax.set_yticklabels(labels, horizontalalignment = 'center')

    ax.grid(False, axis = 'y', which = 'both')

    return patches


def tornados():
    country = 'Global'
    outcome = 'new_infections'
    targets = [
        [model.target.StatusQuo(),
         model.target.UNAIDS95()],
        [model.target.StatusQuo(),
         model.target.Vaccine(treatment_targets = model.target.StatusQuo())]]
    titles = ['95–95–95', 'Vaccine']
    targets = [[str(x) for x in t] for t in targets]
    time = 2035

    figsize = (8.5 * 0.7, 6.5)
    palette = 'Dark2'

    parameter_samples = model.samples.load()
    # Get fancy names.
    parameter_names = common.parameter_names

    with model.results.samples.h5.open_() as results:
        # Order colors by order of prccs for 1st time.
        outcome_samples = get_outcome_samples(results, country, targets[0],
                                              outcome, time)
        rho = stats.prcc(parameter_samples, outcome_samples)
        ix = numpy.argsort(numpy.abs(rho))[ : : -1]
        labels = [parameter_names[i] for i in ix]
        colors_ = seaborn.color_palette(palette, len(parameter_names))
        colors = {l: c for (l, c) in zip(labels, colors_)}

        nrows = 1
        ncols = len(targets)
        with seaborn.axes_style('whitegrid'):
            fig, axes = pyplot.subplots(nrows, ncols,
                                        figsize = figsize,
                                        sharex = 'all')

            if isinstance(axes, pyplot.Axes):
                axes = [axes]

            for (ax, targets_, title) in zip(axes, targets, titles):
                seaborn.despine(ax = ax, top = True, bottom = True)
                ax.tick_params(labelsize = pyplot.rcParams['font.size'])
                tornado(ax, results, country, targets_, outcome, time,
                        parameter_samples, colors,
                        parameter_names = parameter_names)
                ax.set_xlabel('PRCC')
                # Make x-axis limits symmetric.
                # xmin, xmax = ax.get_xlim()
                # xabs = max(abs(xmin), abs(xmax))
                xabs = 1
                ax.set_xlim(- xabs, xabs)
                ax.set_title(title)

    fig.tight_layout(h_pad = 0, w_pad = 1)

    common.savefig(fig, '{}.pdf'.format(common.get_filebase()), title = 'PRCC')
    common.savefig(fig, '{}.pgf'.format(common.get_filebase()), title = 'PRCC')
    common.savefig(fig, '{}.png'.format(common.get_filebase()), title = 'PRCC')


if __name__ == '__main__':
    tornados()

    pyplot.show()
