#!/usr/bin/python3
'''
Plot new infections.
'''

import collections
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


def baseplot(ax, t, data, ylabel,
             legend = True, xlabel = True, title = None,
             percent = False):
    linestyles = ('dotted', 'solid')
    colors = seaborn.color_palette('husl', len(data) // len(linestyles))
    styles = list(itertools.product(linestyles, colors))
    for (x, style) in zip(data.items(), styles):
        k, v = x
        ls, c = style
        ax.plot(t + 2015, v,
                linestyle = ls,
                color = c,
                label = getlabel(k))
    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    if xlabel:
        ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    if percent:
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))
    if legend:
        ax.legend(loc = 'upper left')
    if title is not None:
        ax.set_title(title)


def new_infections(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.new_infections / 1000
    ylabel = 'New Infections (1000s)'
    baseplot(ax, t, data_, ylabel, **kwargs)


def dead(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.dead / 1000
    ylabel = 'AIDS Deaths (1000s)'
    baseplot(ax, t, data_, ylabel, **kwargs)


def infected(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.infected / 1000
    ylabel = 'People Living with HIV (1000s)'
    baseplot(ax, t, data_, ylabel, **kwargs)


def AIDS(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.AIDS / 1000
    ylabel = 'People with AIDS (1000s)'
    baseplot(ax, t, data_, ylabel, **kwargs)


def prevalence(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.prevalence * 100
    ylabel = 'Prevalence'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())

    t = results[countries[0]][levels[0]].t
    for country in countries:
        fig, axes = pyplot.subplots(3, figsize = (11, 8.5), sharex = True)
        new_infections(axes[0], t, results[country],
                       title = country, xlabel = False)
        infected(axes[1], t, results[country], xlabel = False,
                 legend = False)
        AIDS(axes[2], t, results[country], legend = False)
        fig.tight_layout()
        fig.savefig('{}.pdf'.format(country.replace(' ', '_')))

    pyplot.show()


if __name__ == '__main__':
    _main()
