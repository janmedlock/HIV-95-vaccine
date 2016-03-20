'''
Make plots.
'''

import warnings

import numpy
from matplotlib import pyplot
from matplotlib import ticker

# Silence warnings from matplotlib trigged by seaborn
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn


def solution(solution, show = True):
    '''
    Plot a :class:`model.simulation.Solution`.
    '''

    (fig0, ax0) = pyplot.subplots(2, 1)

    for (p, t) in zip(solution.proportions.items(),
                      solution.target_values.items()):
        pk, pv = p
        tk, tv = t
        l = ax0[0].plot(solution.t, pv, label = pk)
        ax0[0].plot(solution.t, tv, color = l[0].get_color(),
                    linestyle = ':')
    ax0[0].legend(loc = 'lower right')

    for (k, v) in solution.control_rates.items():
        ax0[1].plot(solution.t, v, label = '{} rate'.format(k))
    ax0[1].legend(loc = 'upper right')

    (fig1, ax1) = pyplot.subplots()

    colors = seaborn.color_palette('husl', len(solution))
    for (i, c) in zip(solution.items(), colors):
        k, v = i
        ax1.semilogy(solution.t, v, color = c, label = k)
    ax1.legend(loc = 'lower right')

    (fig2, ax2) = pyplot.subplots()

    diagnosed = (solution.diagnosed
                 + solution.treated
                 + solution.viral_suppression
                 + solution.AIDS)
    treated =  (solution.treated
                + solution.viral_suppression)
    ax2.plot(solution.t, solution.infected, label = 'PLHIV')
    ax2.plot(solution.t, diagnosed, label = 'diagnosed')
    ax2.plot(solution.t, treated, label = 'treated')
    ax2.plot(solution.t, solution.viral_suppression, label = 'suppressed')
    ax2.legend(loc = 'upper right')

    (fig3, ax3) = pyplot.subplots()

    ax3.plot(solution.t, 100 * solution.prevalence, label = 'prevalence')
    ax3.set_xlabel('time (years)')
    ax3.set_ylabel('Prevalence')
    ax3.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))

    if show:
        pyplot.show()
