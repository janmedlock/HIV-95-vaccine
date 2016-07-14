#!/usr/bin/python3
'''
Plot efficacy plots.
'''

import collections
import itertools
import sys

from matplotlib import pyplot
from matplotlib import ticker
import numpy

sys.path.append('..')
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('../..')
import model
from model import picklefile


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
                               k[3],
                               k[4])
    return label


def baseplot(ax, t, data, ylabel, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
    linestyles = ('dotted', 'solid')
    colors = seaborn.color_palette('Set2', len(data) // len(linestyles))
    styles = list(itertools.product(linestyles, colors))
    for (x, style) in zip(data.items(), styles):
        k, v = x
        ls, c = style
        ax.plot(t, v / scale,
                linestyle = ls,
                color = c,
                label = getlabel(k))
    ax.set_xlim(t[0], t[-1])
    if xlabel:
        ax.set_xlabel('Year')
    if scale > 1:
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


def new_infections(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.new_infections
    ylabel = 'New Infections'
    baseplot(ax, t, data_, ylabel, **kwargs)


def dead(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.dead
    ylabel = 'AIDS Deaths'
    baseplot(ax, t, data_, ylabel, **kwargs)


def infected(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.infected
    ylabel = 'People Living with HIV'
    baseplot(ax, t, data_, ylabel, **kwargs)


def AIDS(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.AIDS
    ylabel = 'People with AIDS'
    baseplot(ax, t, data_, ylabel, **kwargs)


def prevalence(ax, t, data, **kwargs):
    data_ = collections.OrderedDict()
    for (k, v) in data.items():
        data_[k] = v.prevalence * 100
    ylabel = 'Prevalence'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def _main():
    countries_to_plot = ('United States of America',
                         'South Africa',
                         'Rwanda',
                         'Uganda',
                         'India',
                         'Haiti',
                         'Global')

    results = picklefile.load('../909090.pkl')

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][levels[0]].t
    for country in countries_to_plot:
        fig, axes = pyplot.subplots(3, figsize = (11, 8.5), sharex = True)
        if country == 'Global':
            data = model.build_global(results)
            scale = 1e6
        else:
            data = results[country]
            scale = 1e3
        title = country
        new_infections(axes[0], t, data, scale = scale,
                       title = title, xlabel = False)
        infected(axes[1], t, data, scale = scale,
                 xlabel = False, legend = False)
        AIDS(axes[2], t, data, scale = scale,
             legend = False)
        fig.tight_layout()
        fig.savefig('{}.pdf'.format(country.replace(' ', '_')))

    pyplot.show()


if __name__ == '__main__':
    _main()
