#!/usr/bin/python3
'''
Plot new infections.
'''

import collections.abc
import itertools
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


def sortlevels(s):
    s_ = s.split('+')
    if s_[0] == 'baseline':
        retval = 1 * 1000
    elif s_[0] == '909090':
        retval = 2 * 1000
    else:
        raise ValueError
    if len(s_) > 1:
        s__ = s_[1].split('-')
        retval += (float(s__[0]) / 100 + 1) * 100
        retval += 10 - float(s__[1])
    return retval


def getlabel(s):
    s_ = s.split('+')
    if s_[0] == 'baseline':
        label = 'Status quo'
    elif s_[0] == '909090':
        label = '90–90–90'
    else:
        raise ValueError
    if len(s_) > 1:
        s__ = s_[1].split('-')
        label += ' with {}% vac starting {:g}'.format(
            s__[0], float(s__[1]) + 2015)
    return label


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = sorted(results.keys())
    levels = sorted(results[countries[0]], key = sortlevels)
    colors = seaborn.color_palette('husl', len(levels))
    for country in countries:
        r = results[country]
        fig, ax = pyplot.subplots()
        for (level, color) in zip(levels, colors):
            v = r[level]
            ax.plot(v.t + 2015, v.new_infections / 1000,
                    color = color,
                    label = getlabel(level))

        ax.set_xlim(v.t[0] + 2015, v.t[-1] + 2015)
        ax.set_xlabel('Year')
        ax.set_ylabel('New Infections (1000s)')
        ax.legend(loc = 'upper left')
        ax.set_title(country)
        break

    # fig.savefig('new_infections.pdf')

    pyplot.show()


if __name__ == '__main__':
    _main()
