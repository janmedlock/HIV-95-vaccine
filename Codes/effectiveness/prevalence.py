#!/usr/bin/python3
'''
Plot new infections.
'''

import collections
import itertools
import pickle
import sys
import warnings

from matplotlib import pyplot
from matplotlib import ticker
import numpy

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

sys.path.append('..')

import model


countries_to_plot = ('Global',
                     'Haiti',
                     'India',
                     'Rwanda',
                     'South Africa',
                     'Uganda',
                     'United States of America')

# No-vaccine runs.
kbaseline = ('baseline', 0)
k909090 = ('909090', 0)


def getlabel(country, k = None):
    if country == 'United States of America':
        c = 'United States'
    else:
        c = country
    label = '{}'.format(c)
    if k is not None:
        if k[0] == 'baseline':
            label += ', Status quo'
        elif k[0] == '909090':
            label += ', 90–90–90'
        else:
            raise ValueError
        if k[1] > 0:
            fmtstr = ' with {:g}% eff vac at {:g}% cov rolled out {:g}–{:g}'
            label += fmtstr.format(100 * k[1],
                                   100 * k[2],
                                   2015 + k[3],
                                   2015 + k[3] + k[4])
    return label


def prevalence(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = v[k909090].prevalence
    ylabel = 'Prevalence'

    if 'Global' in countries_to_plot:
        ncolors = len(countries_to_plot) - 1
    else:
        ncolors = len(countries_to_plot)
    colors_ = iter(seaborn.color_palette('Set2', ncolors))
    colors = {}
    for c in countries_to_plot:
        if c == 'Global':
            colors[c] = 'black'
        else:
            colors[c] = next(colors_)

    N = len(countries_to_plot)
    order = numpy.arange(2 * numpy.ceil(N / 2), dtype = int)
    order = order.reshape(2, -1).T.flatten()[ : N]
    for i in order:
        country = countries_to_plot[i]
        if country == 'Global':
            zorder = 2
        else:
            zorder = 1
        ax.semilogy(t + 2015,
                    100 * data[country][k909090].prevalence,
                    color = colors[country],
                    label = getlabel(country),
                    linestyle = 'solid',
                    zorder = zorder)
        ax.semilogy(t + 2015,
                    100 * data[country][kbaseline].prevalence,
                    color = colors[country],
                    linestyle = 'dashed',
                    zorder = zorder)
    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))
    ax.legend(loc = 'lower center',
              ncol = (len(countries_to_plot) + 1) // 2)

    ax.yaxis.set_major_locator(ticker.LogLocator(10, [1, 2, 5]))
    ax.set_ylim(0.15, 25)


def _main():
    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    fig, ax = pyplot.subplots()
    prevalence(ax, t, results)
        
    fig.tight_layout()

    kwds = dict(fontsize = 'large', fontweight = 'bold',
                ha = 'left', va = 'top')

    fig.savefig('prevalence.pdf')
    fig.savefig('prevalence.png')

    pyplot.show()


if __name__ == '__main__':
    _main()
