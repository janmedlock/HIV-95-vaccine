#!/usr/bin/python3
'''
Example script of accessing results from runs with the samples of
the parameter distributions.
'''

import sys

from matplotlib import pyplot
import numpy

sys.path.append('..')
import model

# import seaborn
sys.path.append('../plots')
import seaborn_quiet as seaborn


if __name__ == '__main__':
    with model.results.samples.stats.load() as results:
        countries = results.keys()
        print('countries =', countries)

        country = 'South Africa'
        cgroup = results[country]
        targets = cgroup.keys()
        print('targets =', targets)

        target = 'Status Quo'
        ctgroup = cgroup[target]
        outcomes = ctgroup.keys()
        print('outcomes =', outcomes)

        outcome = 'infected'
        ctogroup = ctgroup[outcome]
        stats = ctogroup.keys()
        print('stats =', stats)

        stat = 'CI50'
        value = ctogroup[stat]
        print(stat, '=', value[:])

        zmax = len(stats)
        # I forgot to put 't' in the file...
        t = numpy.linspace(2015, 2035, 20 * 120 + 1)
        # You can also use '.' to access values.
        pyplot.plot(t, ctogroup['median'],
                    label = 'median', color = 'black',
                    zorder = zmax)

        CIs = sorted([s for s in stats if s.startswith('CI')])
        colors = seaborn.color_palette()
        for (i, CI) in enumerate(CIs):
            value = ctogroup[CI]
            label = '{}% CI'.format(CI[2 : ])
            pyplot.fill_between(t, value[0], value[1],
                                label = label,
                                facecolor = colors[i],
                                linewidth = 0,
                                zorder = zmax - 1 - i)

        pyplot.ylabel(outcome.replace('_', ' ').title())
        pyplot.title(country)
        pyplot.legend(loc = 'upper left', frameon = False)
        pyplot.show()