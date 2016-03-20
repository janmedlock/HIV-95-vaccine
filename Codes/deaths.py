#!/usr/bin/python3
'''
Plot AIDS deaths.
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

    fig, axes = pyplot.subplots(len(countries),
                                sharex = True)
    for (c, ax) in zip(countries, axes):
        r = results[c]
        for (k, l) in (
                ('baseline', 'Status quo'),
                ('909090', '90–90–90'),
                ('909090+50-10', '90–90–90 + 50% vaccination starting in 2025'),
                ('909090+50-5', '90–90–90 + 50% vaccination starting in 2020')):
        s = r[k]
        ax.plot(s.t + 2015,
                s.dead / 1000,
                label = l)

        ax.set_xlim(s.t[0] + 2015, s.t[-1] + 2015)

        ax.set_xlabel('Year')
        ax.set_ylabel('AIDS Deaths (1000s)')
        ax.legend(ncol = 2, loc = 'upper left')

        ax.set_title(c)

    fig.savefig('deaths.pdf')

    pyplot.show()


if __name__ == '__main__':
    _main()
