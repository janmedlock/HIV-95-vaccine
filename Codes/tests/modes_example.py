#!/usr/bin/python3
'''
Example script of accessing results from runs with the modes of
the parameter distributions.
'''

import sys

from matplotlib import pyplot

sys.path.append('..')
import model

# import seaborn
sys.path.append('../plots')
import seaborn_quiet as seaborn


if __name__ == '__main__':
    with model.results.modes.load() as results:

        # The data look like results[country][target][stat]

        countries = results.keys()
        print('countries =', countries)

        country = 'South Africa'
        targets = results[country].keys()
        print('targets =', targets)

        target = targets[5]
        stats = results[country][target].keys()
        print('stats =', stats)

        # You need '[:]' or '.read()' at the end to get the actual values.
        print('prevalence =', results[country][target]['prevalence'][:])

        # Again, you need '[:]' or '.read()' at the end to get the
        # actual values.
        stat = 'infected'
        print(stat, '=', results[country][target][stat][:])

        t = results[country][target]['t']
        x = results[country][target][stat]
        pyplot.plot(t, x, label = country)
        pyplot.ylabel(stat.capitalize())
        pyplot.legend(loc = 'upper right', frameon = False)
        pyplot.show()
