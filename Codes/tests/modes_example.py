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
    with model.results.load_modes() as results:

        # The data look like results[country][target].attr

        countries = list(results.keys())
        print('countries =', countries)

        country = 'South Africa'
        targets = list(results[country].keys())
        print('targets =', targets)

        target = targets[5]
        # Drop private attrs, i.e. ones that start with '_'.
        attrs = [a for a in dir(results[country][target])
                 if not a.startswith('_')]
        print('attrs =', attrs)

        # You can pick them out using results[country][target].attr.
        # (You need '[:]' or '.read()' at the end to get the actual values.)
        print('prevalence =', results[country][target].prevalence[:])

        # Or you can use getattr() if you have attr in a string:
        # (Again, you need '[:]' or '.read()' at the end to get the
        # actual values.)
        attr = 'infected'
        print(attr, '=', getattr(results[country][target], attr)[:])

        t = results[country][target].t
        x = getattr(results[country][target], attr)
        pyplot.plot(t, x, label = country)
        pyplot.ylabel(attr.capitalize())
        pyplot.legend(loc = 'upper right', frameon = False)
        pyplot.show()
