'''
Make plots of the :mod:`model.simulation` solutions.
'''

import warnings

import numpy
from matplotlib import pyplot

# Silence warnings from matplotlib trigged by seaborn
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

from . import control_rates
from . import proportions
from . import simulation
from . import targets


def plot_solution(t, state, targs, parameters, show = True):
    (fig, ax) = pyplot.subplots(2, 1)

    props = proportions.get_proportions(state)

    target_values = targets.get_target_values(t, targs, parameters)
    controls = control_rates.get_control_rates(t, state, targs, parameters)

    for (i, k) in enumerate(('diagnosed', 'treated', 'suppressed')):
        l = ax[0].plot(t, props[:, i], label = k.capitalize())
        ax[0].plot(t, target_values[:, i],
                   color = l[0].get_color(), linestyle = ':')
    ax[0].legend(loc = 'lower right')

    for (i, k) in enumerate(('diagnosis', 'treatment', 'nonadherance')):
        ax[1].plot(t, controls[:, i], label = '{} rate'.format(k))
    ax[1].legend(loc = 'upper right')


    (fig1, ax1) = pyplot.subplots()

    S, A, U, D, T, V, W, Z = simulation.split_state(state)

    ax1.semilogy(t, S, label = 'S')
    ax1.semilogy(t, A, label = 'A')
    ax1.semilogy(t, U, label = 'U')
    ax1.semilogy(t, D, label = 'D')
    ax1.semilogy(t, T, label = 'T')
    ax1.semilogy(t, V, label = 'V')
    ax1.semilogy(t, W, label = 'W')
    ax1.semilogy(t, Z, label = 'Z')
    ax1.legend(loc = 'upper right')

    (fig2, ax2) = pyplot.subplots()

    N = state.sum(1)
    PLHI = N - S
    diagnosed = PLHI - A - U
    treated = diagnosed - D - W
    suppressed = treated - T
    ax2.plot(t, PLHI, label = 'PLHI')
    ax2.plot(t, diagnosed, label = 'diagnosed')
    ax2.plot(t, treated, label = 'treated')
    ax2.plot(t, suppressed, label = 'suppressed')
    ax2.legend(loc = 'upper right')

    if show:
        pyplot.show()
