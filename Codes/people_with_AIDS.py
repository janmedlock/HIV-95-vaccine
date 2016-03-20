#!/usr/bin/python3
'''
Plot people with AIDS.
'''

import pickle
import warnings

from matplotlib import pyplot
from matplotlib import ticker

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn


countries = ('United States of America',
             'South Africa',
             'Rwanda',
             'Uganda',
             'India',
             'Haiti')


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    colors = seaborn.color_palette('husl', len(countries))

    fig, ax = pyplot.subplots()
    for (c, x) in zip(countries, colors):
        r = results[c]
        ax.plot(r.t + 2015,
                r.AIDS / 1000,
                color = x, linestyle = 'solid',
                label = '{}, 90–90–90'.format(c))

    for (c, x) in zip(countries, colors):
        r = results[c]
        ax.plot(r.baseline.t + 2015,
                r.baseline.AIDS / 1000,
                color = x, linestyle = 'dotted',
                label = '{}, status quo'.format(c))

    ax.set_xlim(r.t[0] + 2015,
                r.t[-1] + 2015)

    ax.set_xlabel('Year')
    ax.set_ylabel('People with AIDS (1000s)')
    ax.legend(ncol = 2, loc = 'upper left')

    fig.savefig('people_with_AIDS.pdf')

    pyplot.show()


if __name__ == '__main__':
    _main()
