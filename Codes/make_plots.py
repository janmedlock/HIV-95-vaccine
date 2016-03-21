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


def getlabel(k):
    if k[0] == 'baseline':
        label = 'Status quo'
    elif k[0] == '909090':
        label = '90–90–90'
    else:
        raise ValueError

    if k[1] > 0:
        fmtstr = ' with {:g}% eff vac at {:g}% cov rolled out {:g}–{:g}'
        label += fmtstr.format(100 * k[1],
                               100 * k[2],
                               2015 + k[3],
                               2015 + k[3] + k[4])

    return label


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    linestyles = ('dotted', 'solid')
    colors = seaborn.color_palette('husl', len(levels) // len(linestyles))
    styles = list(itertools.product(linestyles, colors))
    for country in countries:
        r = results[country]
        fig, ax = pyplot.subplots()
        for (level, style) in zip(levels, styles):
            v = r[level]
            ls, c = style
            ax.plot(v.t + 2015,
                    v.new_infections / 1000,
                    # v.dead / 1000,
                    # 100 * v.prevalence,
                    # v.infected / 1000,
                    # v.baseline.AIDS / 1000,
                    linestyle = ls,
                    color = c,
                    label = getlabel(level))

        ax.set_xlim(v.t[0] + 2015, v.t[-1] + 2015)
        ax.set_xlabel('Year')
        ax.set_ylabel('New Infections (1000s)')
        # ax.set_ylabel('AIDS Deaths (1000s)')
        # ax.set_ylabel('Prevalence')
        # ax.set_ylabel('People Living with HIV (1000s)')
        # ax.set_ylabel('People with AIDS (1000s)')
        # ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))
        ax.legend(loc = 'upper left')
        ax.set_title(country)

    pyplot.show()


if __name__ == '__main__':
    _main()
