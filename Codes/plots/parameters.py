#!/usr/bin/python3
'''
Calculate PRCCs.
'''

import os.path
import sys

from matplotlib import pyplot
from matplotlib import ticker
import numpy
from scipy import interpolate
from scipy import stats
import seaborn

sys.path.append('..')
import model


country = 'Global'
stat = 'prevalence'
t = 20

parameter_order = (
    'coital_acts_per_year',
    'death_years_lost_by_suppression',
    'progression_rate_acute',
    'suppression_rate',
    'transmission_per_coital_act_acute',
    'transmission_per_coital_act_unsuppressed',
    'transmission_per_coital_act_reduction_by_suppression'
)

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


def rankdata(X):
    if numpy.ndim(X) == 0:
        raise ValueError('Need at least 1-D data.')
    elif numpy.ndim(X) == 1:
        return (stats.rankdata(X) - 1) / (len(X) - 1)
    else:
        return numpy.stack([rankdata(X[..., i])
                            for i in range(numpy.shape(X)[-1])],
                           axis = -1)
        

def cc(X, y, use_ranks = True):
    if use_ranks:
        result = (stats.spearmanr(y, x) for x in X.T)
    else:
        result = (stats.pearsonr(y, x) for x in X.T)
    rho, p = zip(*result)
    return rho, p


def get_residuals(Z, b):
    # Add a column of ones for intercept term.
    A = numpy.column_stack((numpy.ones_like(Z[..., 0]), Z))
    result = numpy.linalg.lstsq(A, b)
    coefs = result[0]
    # residuals = b - A @ coefs  # Stupid Sphinx bug.
    residuals = b - numpy.dot(A, coefs)
    return residuals


def pcc(X, y, use_ranks = True):
    n = numpy.shape(X)[-1]

    if use_ranks:
        X = rankdata(X)
        y = rankdata(y)

    rho = numpy.empty(n)
    for i in range(n):
        # Separate ith column from other columns.
        mask = numpy.array([j == i for j in range(n)])
        x = numpy.squeeze(X[..., mask])
        Z = X[..., ~mask]
        x_res = get_residuals(Z, x)
        y_res = get_residuals(Z, y)
        rho[i], _ = stats.pearsonr(x_res, y_res)
    return rho


def plot_ranks(X, y, parameter_names = None, alpha = 0.7, size = 2):
    m = numpy.shape(X)[0]
    n = numpy.shape(X)[-1]

    X = rankdata(X)
    y = rankdata(y)

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

        x_res = get_residuals(Z, x)
        y_res = get_residuals(Z, y)

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

    return (fig, axes)


def plot_samples(X, y, parameter_names = None, alpha = 0.7, size = 2):
    m = numpy.shape(X)[0]
    n = numpy.shape(X)[-1]

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

        x_res = get_residuals(Z, x)
        y_res = get_residuals(Z, y)

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

    return (fig, axes)


if __name__ == '__main__':
    parameter_samples = model.samples.load()
    parameters = model.parameters.Parameters.get_rv_names()

    # Order
    ix = [parameter_order.index(n) for n in parameters]
    parameter_samples = parameter_samples[:, ix]
    parameters = [parameters[i] for i in ix]

    outcome_samples = get_outcome_samples(country, stat, t)

    # rho, p = cc(parameter_samples, outcome_samples, use_ranks = True)
    # print('\nRCCs:')
    # for (rho_, p_, n) in zip(rho, p, parameters):
    #     print('{}: rho = {} (p = {})'.format(n, rho_, p_))

    # rho = pcc(parameter_samples, outcome_samples, use_ranks = True)
    # print('\nPRCCs:')
    # for (rho_, n) in zip(rho, parameters):
    #     print('{}: rho = {}'.format(n, rho_))
    
    parameter_names = [parameter_name[p] for p in parameters]

    fig, axes = plot_samples(parameter_samples, outcome_samples,
                             parameter_names = parameter_names)
    m.savefig('{}.pdf'.format(os.path.splitext(__file__)))
    m.savefig('{}.png'.format(os.path.splitext(__file__)))

    fig, axes = plot_ranks(parameter_samples, outcome_samples,
                           parameter_names = parameter_names)
    m.savefig('{}_rank.pdf'.format(os.path.splitext(__file__)))
    m.savefig('{}_rank.png'.format(os.path.splitext(__file__)))

    pyplot.show()
