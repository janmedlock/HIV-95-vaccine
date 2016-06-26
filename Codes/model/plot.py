'''
Make plots.
'''

from matplotlib import pyplot
from matplotlib import ticker

# Silence warnings from matplotlib trigged by seaborn.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import seaborn


def simulation(sim, show = True):
    '''
    Plot a :class:`model.simulation.Simulation`.
    '''

    (fig0, ax0) = pyplot.subplots(2, 1)

    for (p, t) in zip(sim.proportions.items(),
                      sim.target_values.items()):
        pk, pv = p
        tk, tv = t
        l = ax0[0].plot(sim.t, pv, label = pk)
        ax0[0].plot(sim.t, tv, color = l[0].get_color(),
                    linestyle = ':')
    ax0[0].legend(loc = 'lower right')

    for (k, v) in sim.control_rates.items():
        ax0[1].plot(sim.t, v, label = '{} rate'.format(k))
    ax0[1].legend(loc = 'upper right')

    (fig1, ax1) = pyplot.subplots()

    colors = seaborn.color_palette('husl', len(sim))
    for (i, c) in zip(sim.items(), colors):
        k, v = i
        ax1.semilogy(sim.t, v, color = c, label = k)
    ax1.legend(loc = 'lower right')

    (fig2, ax2) = pyplot.subplots()

    diagnosed = (sim.diagnosed
                 + sim.treated
                 + sim.viral_suppression
                 + sim.AIDS)
    treated =  (sim.treated
                + sim.viral_suppression)
    ax2.plot(sim.t, sim.infected, label = 'PLHIV')
    ax2.plot(sim.t, diagnosed, label = 'diagnosed')
    ax2.plot(sim.t, treated, label = 'treated')
    ax2.plot(sim.t, sim.viral_suppression, label = 'suppressed')
    ax2.legend(loc = 'upper right')

    (fig3, ax3) = pyplot.subplots()

    ax3.plot(sim.t, 100 * sim.prevalence, label = 'prevalence')
    ax3.set_xlabel('time (years)')
    ax3.set_ylabel('Prevalence')
    ax3.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))

    if show:
        pyplot.show()
