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
    country = 'South Africa'
    target = model.target.StatusQuo()

    # Replace 'mode' with 'samples' (or remove)
    # to load results from the samples.
    results = model.results.load(country, target, 'mode')

    print('prevalence =', results.prevalence)

    # You can programmatically get different statistics using getattr.
    stat = 'infected'
    print(stat, '=', getattr(results, stat))

    t = model.simulation.t
    x = getattr(results, stat)
    pyplot.plot(t, x, label = country)
    pyplot.ylabel(stat.capitalize())
    pyplot.legend(loc = 'upper left', frameon = False)
    pyplot.show()
