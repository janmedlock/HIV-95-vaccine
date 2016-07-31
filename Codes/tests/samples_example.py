#!/usr/bin/python3
'''
Example script of accessing results from runs with the samples of
the parameter distributions.
'''

from matplotlib import pyplot
import numpy
import tables

# import seaborn
import sys
sys.path.append('../plots')
import seaborn_quiet as seaborn


if __name__ == '__main__':
    with tables.open_file('../results/sample_stats.h5', mode = 'r') as stats:
        countries = [g._v_name for g in stats.root]
        print('countries =', countries)

        country = 'South Africa'
        cgroup = getattr(stats.root, country)
        targets = [t._v_name for t in cgroup]
        print('targets =', targets)

        target = 'Status Quo'
        ctgroup = getattr(cgroup, target)
        outcomes = [o._v_name for o in ctgroup]
        print('outcomes =', outcomes)

        outcome = 'infected'
        ctogroup = getattr(ctgroup, outcome)
        stats = [s._v_name for s in ctogroup]
        print('stats =', stats)

        stat = 'CI50'
        value = getattr(ctogroup, stat)
        print(stat, '=', value[:])

        zmax = len(stats)
        # I forgot to put 't' in the file...
        t = numpy.linspace(2015, 2035, 20 * 120 + 1)
        # You can also use '.' to access values.
        pyplot.plot(t, ctogroup.median, label = 'median', color = 'black',
                    zorder = zmax)

        CIs = sorted([s for s in stats if s.startswith('CI')])
        colors = seaborn.color_palette()
        for (i, CI) in enumerate(CIs):
            value = getattr(ctogroup, CI)
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
