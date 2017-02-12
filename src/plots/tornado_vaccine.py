#!/usr/bin/python3
'''
Make tornado plots for vaccine scenarios.
'''

import os.path
import sys

from matplotlib import pyplot
from matplotlib import ticker
import numpy
import seaborn

sys.path.append(os.path.dirname(__file__))  # cwd for Sphinx.
import common
import stats
sys.path.append('..')
import model


def _get_args(target):
    i = target.find('(')
    return target[i + 1 : -1].split(', ')


def _get_value(s):
    i = s.find('=')
    x = s[i + 1 : ]
    if x.endswith('%'):
        return float(x[ : -1]) / 100
    elif x.endswith('y'):
        return 0.5 / float(x[ : -1])
    else:
        return float(x)

def get_target_info(baseline, target):
    args_baseline = _get_args(str(baseline))
    args = _get_args(str(target))
    diff = []
    for i in range(len(args)):
        if args[i] != args_baseline[i]:
            x_b = _get_value(args_baseline[i])
            x = _get_value(args[i])
            fancy = args[i].replace('_', ' ').replace('=', ' = ')
            fancy = fancy.replace('time to start', 'start date')
            if fancy.startswith('time to fifty percent'):
                j = fancy.find('=')
                t = float(fancy[j + 2 : -1])
                fancy = 'scale-up = {:g}% y$^{{-1}}$'.format(50 / t)
            j = fancy.find('=')
            pre = fancy[ : j - 1]
            post = fancy[j + 2 : ]
            fancy = post + ' ' + pre
            label = fancy.capitalize()
            return (x_b, x, label)


def sensitivity(results, country, targets, stat, times):
    baseline = targets[1]
    y_b = numpy.asarray(getattr(results[country][str(baseline)], stat))
    y_b = numpy.interp(times, common.t, y_b)
    rho = []
    labels = []
    for t in targets[2 : ]:
        x_b, x, label = get_target_info(baseline, t)
        dx = x - x_b
        labels.append(label)
        y = numpy.asarray(getattr(results[country][str(t)], stat))
        y = numpy.interp(times, common.t, y)
        dy = y - y_b
        # rho.append(dy / dx)
        # rho.append(dy / y_b * x_b / dx)
        rho.append(dy / y_b / dx)
    return (numpy.asarray(rho), labels)


def tornado(ax, results, country, targets, outcome, t, colors):
    rho, labels = sensitivity(results, country, targets, outcome, t)
    n = len(rho)

    ix = numpy.argsort(numpy.abs(rho))
    labels = [labels[i] for i in ix]

    h = range(n)
    patches = ax.barh(h, rho[ix],
                      height = 1, left = 0,
                      align = 'center',
                      color = colors,
                      edgecolor = colors)
    # ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n = 2))
    ax.tick_params(labelsize = pyplot.rcParams['font.size'] + 1)
    ax.tick_params(axis = 'y', pad = 6)

    ax.set_yticks(h)
    ax.set_ylim(- 0.5, n - 0.5)
    ax.set_yticklabels(labels)

    ax.grid(False, axis = 'y', which = 'both')

    return patches


def tornados():
    country = 'Global'
    outcome = 'new_infections'
    targets = model.targets.vaccine_scenarios
    time = 2035

    figsize = (5.95, 6.5)
    palette = 'Dark2'
    colors = seaborn.color_palette(palette)

    with model.results.modes.open_vaccine_scenarios() as results:
        with seaborn.axes_style('whitegrid'):
            fig, ax = pyplot.subplots(1, 1, figsize = figsize)
            seaborn.despine(ax = ax, top = True, bottom = True)
            ax.tick_params(labelsize = pyplot.rcParams['font.size'])
            tornado(ax, results, country, targets, outcome, time, colors)
            ax.set_xlabel('Sensitivity')

    fig.tight_layout(pad = 0)

    # common.savefig(fig, '{}.pdf'.format(common.get_filebase()),
    #                title = 'PRCC')
    # common.savefig(fig, '{}.png'.format(common.get_filebase()),
    #                title = 'PRCC')


if __name__ == '__main__':
    tornados()

    pyplot.show()
