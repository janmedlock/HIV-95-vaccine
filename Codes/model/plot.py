'''
Make plots.
'''

from matplotlib import pyplot
from matplotlib import ticker

# import seaborn
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../plots'))
import seaborn_quiet as seaborn

from . import ODEs
from . import simulation


def simulation_(sim, show = True):
    '''
    Plot a :class:`model.simulation.Simulation`.
    '''

    (fig0, ax0) = pyplot.subplots(2, 1)

    for n in sim.proportions.dtype.names:
        pv = getattr(sim.proportions, n)
        tv = getattr(sim.target_values, n)
        l = ax0[0].plot(simulation.t, pv, label = n)
        ax0[0].plot(simulation.t, tv, color = l[0].get_color(),
                    linestyle = ':')
    ax0[0].legend(loc = 'lower right')

    for n in sim.control_rates.dtype.names:
        v = getattr(sim.control_rates, n)
        ax0[1].plot(simulation.t, v, label = '{} rate'.format(n))
    ax0[1].legend(loc = 'upper right')

    (fig1, ax1) = pyplot.subplots()

    colors = seaborn.color_palette('husl', len(ODEs.variables))
    for (n, c) in zip(ODEs.variables, colors):
        v = getattr(sim, n)
        ax1.semilogy(simulation.t, v, color = c, label = n)
    ax1.legend(loc = 'lower right')

    (fig2, ax2) = pyplot.subplots()

    diagnosed = (sim.diagnosed
                 + sim.treated
                 + sim.viral_suppression
                 + sim.AIDS)
    treated =  (sim.treated
                + sim.viral_suppression)
    ax2.plot(simulation.t, sim.infected, label = 'PLHIV')
    ax2.plot(simulation.t, diagnosed, label = 'diagnosed')
    ax2.plot(simulation.t, treated, label = 'treated')
    ax2.plot(simulation.t, sim.viral_suppression, label = 'suppressed')
    ax2.legend(loc = 'upper right')

    (fig3, ax3) = pyplot.subplots()

    ax3.plot(simulation.t, 100 * sim.prevalence, label = 'prevalence')
    ax3.set_xlabel('time (years)')
    ax3.set_ylabel('Prevalence')
    ax3.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))

    if show:
        pyplot.show()
