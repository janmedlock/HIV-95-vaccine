#!/usr/bin/python3
'''
Calculate PRCCs.

.. todo:: Update :class:`model.results.Results` to :data:`model.results.data`.
          See :mod:`~.plots.effectiveness`.
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


def plot_ranks(X, y, parameter_names = None, alpha = 0.7, size = 2,
               colors = None):
    m = numpy.shape(X)[0]
    n = numpy.shape(X)[-1]

    X = (stats.rankdata(X) - 1) / (m - 1)
    y = (stats.rankdata(y) - 1) / (m - 1)

    if colors is None:
        colors = seaborn.color_palette('Dark2', n)

    fig, axes = pyplot.subplots(n, 2,
                                sharex = 'col',
                                sharey = 'col',
                                figsize = (5.5, 11))
    maxlim = 0
    for (i, ax) in enumerate(axes):
        mask = numpy.array([j == i for j in range(n)])
        x = numpy.squeeze(X[..., mask])
        Z = X[..., ~mask]

        ax[0].scatter(x, y, color = colors[i], s = size, alpha = alpha)

        x_res = stats.get_residuals(Z, x)
        y_res = stats.get_residuals(Z, y)

        ax[1].scatter(x_res, y_res, color = colors[i], s = size, alpha = alpha)

        if i == n - 1:
            ax[0].set_xlabel('rank\nparameter value')
            ax[1].set_xlabel('residual rank\n parameter value')

        if i == n // 2:
            ax[0].set_ylabel('rank\nprevalence reduction')
            ax[1].set_ylabel('residual rank\nprevalence reduction')

        ax[1].yaxis.set_ticks_position('right')
        ax[1].yaxis.set_label_position('right')
        ax[1].yaxis.set_tick_params(pad = 20)
        for tick in ax[1].yaxis.get_major_ticks():
            tick.label2.set_horizontalalignment('right')

        for axis in (ax[0].xaxis, ax[0].yaxis):
            axis.set_ticks([0, 0.5, 1])
        for axis in (ax[1].xaxis, ax[1].yaxis):
            axis.set_major_locator(ticker.MaxNLocator(nbins = 6))

        for ax_ in (ax[0], ax[1]):
            for axis in (ax_.xaxis, ax_.yaxis):
                axis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
            ax_.grid(True, which = 'both')

        ax[0].set_aspect('equal', adjustable = 'box-forced', anchor = 'W')
        ax[1].set_aspect('equal', adjustable = 'box-forced', anchor = 'E')

        maxlim = max(maxlim,
                     numpy.max((numpy.abs(ax[1].get_xlim()),
                                numpy.abs(ax[1].get_ylim()))))
        for ax_ in (ax[0], ax[1]):
            ax_.autoscale_view('tight')
    
    axes[0, 1].set_xlim(-maxlim, maxlim)
    axes[0, 1].set_ylim(-maxlim, maxlim)

    fig.tight_layout()

    sps = axes[0, 0].get_subplotspec() 
    gs = sps.get_gridspec()
    bottoms, tops, lefts, rights = gs.get_grid_positions(fig)
    if parameter_names is not None:
        for i in range(n):
            fig.text(0.5, (bottoms[i] + tops[i]) / 2,
                     parameter_names[i],
                     horizontalalignment = 'center',
                     verticalalignment = 'center')

    fig.savefig('{}_rank.png'.format(common.get_filebase()))
    fig.savefig('{}_rank.pdf'.format(common.get_filebase()))


def plot_samples(X, y, parameter_names = None, alpha = 0.7, size = 2,
                 colors = None):
    m = numpy.shape(X)[0]
    n = numpy.shape(X)[-1]

    if colors is None:
        colors = seaborn.color_palette('Dark2', n)

    fig, axes = pyplot.subplots(n, 2,
                                sharey = 'col',
                                figsize = (6, 11))
    for (i, ax) in enumerate(axes):
        sharey = None

        mask = numpy.array([j == i for j in range(n)])
        x = numpy.squeeze(X[..., mask])
        Z = X[..., ~mask]

        ax[0].scatter(x, y, color = colors[i], s = size, alpha = alpha)

        x_res = stats.get_residuals(Z, x)
        y_res = stats.get_residuals(Z, y)

        ax[1].scatter(x_res, y_res, color = colors[i], s = size, alpha = alpha)

        if i == n - 1:
            ax[0].set_xlabel('parameter value')
            ax[1].set_xlabel('residual\nparameter value')
        if i == n // 2:
            ax[0].set_ylabel('prevalence reduction')
            ax[1].set_ylabel('residual\nprevalence reduction')

        ax[1].yaxis.set_ticks_position('right')
        ax[1].yaxis.set_label_position('right')
        ax[1].yaxis.set_tick_params(pad = 30)
        for tick in ax[1].yaxis.get_major_ticks():
            tick.label2.set_horizontalalignment('right')

        for ax_ in (ax[0], ax[1]):
            ax_.xaxis.set_major_locator(ticker.MaxNLocator(nbins = 4))
            ax_.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))

        for ax_ in (ax[0], ax[1]):
            for axis in (ax_.xaxis, ax_.yaxis):
                axis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
            ax_.grid(True, which = 'both')

        for ax_ in (ax[0], ax[1]):
            ax_.autoscale_view('tight')
    
    fig.tight_layout(w_pad = 8)

    sps = axes[0, 0].get_subplotspec() 
    gs = sps.get_gridspec()
    bottoms, tops, lefts, rights = gs.get_grid_positions(fig)
    if parameter_names is not None:
        for i in range(n):
            fig.text(0.49, (bottoms[i] + tops[i]) / 2,
                     parameter_names[i],
                     horizontalalignment = 'center',
                     verticalalignment = 'center')

    fig.savefig('{}.png'.format(common.get_filebase()))
    fig.savefig('{}.pdf'.format(common.get_filebase()))


def tornado(X, y, parameter_names = None, colors = None):
    n = numpy.shape(X)[-1]

    if parameter_names is None:
        parameter_names = ['parameter[{}]'.format(i) for i in range(n)]

    rho = stats.prcc(parameter_samples, outcome_samples)

    fig, ax = pyplot.subplots()
    h = range(n, 0, - 1)
    ax.barh(h, rho,
            height = 1, left = 0,
            align = 'center',
            color = colors,
            edgecolor = colors)
    ax.set_xlabel('PRCC')
    ax.set_ylim(0.5, n + 0.5)
    ax.set_yticks(h)
    ax.set_yticklabels(parameter_names,
                       horizontalalignment = 'center')
    ax.yaxis.set_tick_params(pad = 35)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.grid(True, which = 'both')
    ax.yaxis.grid(False)

    fig.tight_layout()

    fig.savefig('{}_tornado.png'.format(common.get_filebase()))
    fig.savefig('{}_tornado.pdf'.format(common.get_filebase()))


if __name__ == '__main__':
    country = 'Global'
    stat = 'prevalence'
    t = 20

    parameter_samples = model.samples.load()
    outcome_samples = get_outcome_samples(country, stat, t)

    # Get names.
    parameters = model.parameters.Parameters.get_rv_names()
    parameter_names = [parameter_name[p] for p in parameters]

    # Order parameters by abs(prcc).
    rho = stats.prcc(parameter_samples, outcome_samples)
    ix = numpy.argsort(numpy.abs(rho))[ : : -1]
    parameter_samples = parameter_samples[:, ix]
    parameters = [parameters[i] for i in ix]
    parameter_names = [parameter_names[i] for i in ix]

    colors = seaborn.color_palette('Dark2', len(parameter_names))

    plot_samples(parameter_samples, outcome_samples,
                 parameter_names = parameter_names,
                 colors = colors)

    plot_ranks(parameter_samples, outcome_samples,
               parameter_names = parameter_names,
               colors = colors)

    # tornado(parameter_samples, outcome_samples,
    #         parameter_names = parameter_names,
    #         colors = colors)

    pyplot.show()
