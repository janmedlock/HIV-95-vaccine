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


countries_to_plot = ('United States of America',
                     'South Africa',
                     'Rwanda',
                     'Uganda',
                     'India',
                     'Haiti',
                     'Global')

# No-vaccine runs.
kbaseline = ('baseline', 0)
k909090 = ('909090', 0)


def getlabel(country, k):
    label = '{}, '.format(country)
    if k[0] == 'baseline':
        label += 'Status quo'
    elif k[0] == '909090':
        label += '90–90–90'
    else:
        raise ValueError
    if k[1] > 0:
        fmtstr = ' with {:g}% eff vac at {:g}% cov rolled out {:g}–{:g}'
        label += fmtstr.format(100 * k[1],
                               100 * k[2],
                               2015 + k[3],
                               2015 + k[3] + k[4])
    return label


def baseplot(ax, t, data, ylabel, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
    if percent:
        scale = 1 / 100
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
    for country in reversed(countries_to_plot):
        if country == 'Global':
            zorder = 2
        else:
            zorder = 1
        ax.plot(t + 2015, data[country] / scale,
                color = colors[country],
                label = country,
                zorder = zorder)
    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    if xlabel:
        ax.set_xlabel('Year')
    if scale > 1 and not percent:
        if scale == 1e3:
            ylabel += ' (1000s)'
        elif scale == 1e6:
            ylabel += ' (M)'
        else:
            ylabel += ' ({:g})'.format(scale)
    ax.set_ylabel(ylabel)
    if percent:
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))
    if legend:
        ax.legend(loc = 'upper left')
    if title is not None:
        ax.set_title(title)


def difference(data, attrname):
    a, b = (getattr(data[k], attrname) for k in (kbaseline, k909090))
    return a - b

def relative_difference(data, attrname):
    a, b = (getattr(data[k], attrname) for k in (kbaseline, k909090))
    return (a - b) / a

def new_infections(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = relative_difference(v, 'new_infections')
    ylabel = 'Reduction in New Infections'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def dead(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = relative_difference(v, 'dead')
    ylabel = 'Reduction in AIDS Deaths'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def infected(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = relative_difference(v, 'infected')
    ylabel = 'Reduction in People Living with HIV'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def AIDS(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = relative_difference(v, 'AIDS')
    ylabel = 'Reduction in People with AIDS'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def prevalence(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (c, v) in data.items():
        data_[c] = relative_difference(v, 'prevalence')
    ylabel = 'Reduction in Prevalence'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def _main():
    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    fig, axes = pyplot.subplots(3, figsize = (11, 8.5), sharex = True)
    new_infections(axes[0], t, results,
                   xlabel = False, legend = True)
    infected(axes[1], t, results,
             xlabel = False, legend = False)
    AIDS(axes[2], t, results,
         xlabel = True, legend = False)
    fig.tight_layout()
    fig.savefig('effectiveness.pdf')

    pyplot.show()


if __name__ == '__main__':
    _main()
