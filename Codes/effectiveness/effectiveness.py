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
                     'Australia',
                     'Brazil',
                     'Cambodia',
                     'China',
                     'France',
                     'Haiti',
                     'India',
                     'Malaysia',
                     'Netherlands',
                     'Nigeria',
                     'Rwanda',
                     'South Africa',
                     'Thailand',
                     'Uganda',
                     'United Kingdom',
                     'United States of America')

# No-vaccine runs.
kbaseline = ('baseline', 0)
k909090 = ('909090', 0)


def getlabel(k):
    if k[0] == 'baseline':
        label = 'Status quo'
    elif k[0] == '909090':
        label = '90–90–90'
    else:
        raise ValueError
    return label


def baseplot(ax, t, data, ylabel, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
    if percent:
        scale = 1 / 100
    for k in (kbaseline, k909090):
        ax.plot(t + 2015, data[k] / scale,
                label = getlabel(k))
    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    if xlabel:
        ax.set_xlabel('Year')
    if scale != 1 and not percent:
        if scale == 1e3:
            ylabel += ' (1000s)'
        elif scale == 1e6:
            ylabel += ' (M)'
        elif scale == 1e-3:
            ylabel += ' per 1000'
        elif scale == 1e-6:
            ylabel += ' per M'
        else:
            ylabel += ' ({:g})'.format(scale)
    ax.set_ylabel(ylabel)
    if percent:
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%g%%'))
    if legend:
        ax.legend(loc = 'upper left')
    if title is not None:
        ax.set_title(title)


def getattr_(data, attrname, t = None):
    if attrname == 'incidence':
        retval = {}
        for k in (kbaseline, k909090):
            ni = getattr(data[k], 'new_infections')
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        return retval
    elif attrname == 'incidence_per_capita':
        retval = {}
        for k in (kbaseline, k909090):
            ni = getattr(data[k], 'new_infections')
            n = getattr(data[k], 'alive')
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[1 :]
        return retval
    elif attrname.endswith('_per_capita'):
        attrname_ = attrname.replace('_per_capita', '')
        return {k: getattr(data[k], attrname_) / getattr(data[k], 'alive')
                for k in (kbaseline, k909090)}
    else:
        return {k: getattr(data[k], attrname) for k in (kbaseline, k909090)}


def counts(data, attrname, t = None):
    return getattr_(data, attrname, t)


def difference(data, attrname):
    a, b = getattr_(data, attrname)
    return a - b


def relative_difference(data, attrname):
    a, b = getattr_(data, attrname)
    return (a - b) / a


def new_infections(ax, t, data, **kwargs):
    data_ = counts(data, 'new_infections')
    ylabel = 'New Infections'
    baseplot(ax, t, data_, ylabel, scale = 1e6, **kwargs)


def incidence(ax, t, data, **kwargs):
    data_ = counts(data, 'incidence_per_capita', t)
    ylabel = 'Annual Incidence'
    baseplot(ax, t[1 : ], data_, ylabel, scale = 1 / 1e6, **kwargs)


def dead(ax, t, data, **kwargs):
    data_ = counts(data, 'dead')
    ylabel = 'AIDS Deaths'
    baseplot(ax, t, data_, ylabel, **kwargs)


def infected(ax, t, data, **kwargs):
    data_ = counts(data, 'infected')
    ylabel = 'People Living with HIV'
    baseplot(ax, t, data_, ylabel, scale = 1e6, **kwargs)


def AIDS(ax, t, data, **kwargs):
    data_ = counts(data, 'AIDS')
    ylabel = 'People with AIDS'
    baseplot(ax, t, data_, ylabel, scale = 1e6, **kwargs)


def AIDS_per_capita(ax, t, data, **kwargs):
    data_ = counts(data, 'AIDS_per_capita')
    ylabel = 'AIDS per capita'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def prevalence(ax, t, data, **kwargs):
    data_ = counts(data, 'prevalence')
    ylabel = 'Prevalence'
    baseplot(ax, t, data_, ylabel, percent = True, **kwargs)


def _main():
    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    for (i, country) in enumerate(countries_to_plot):
        fig, axes = pyplot.subplots(3, 2,
                                    figsize = (11, 8.5), sharex = True)
        data = results[country]
        new_infections(axes[0, 0], t, data,
                       xlabel = False, legend = True)
        incidence(axes[0, 1], t, data,
                  xlabel = False, legend = False)
        infected(axes[1, 0], t, data,
                 xlabel = False, legend = False)
        prevalence(axes[1, 1], t, data,
                   xlabel = False, legend = False)
        AIDS(axes[2, 0], t, data,
             xlabel = True, legend = False)
        AIDS_per_capita(axes[2, 1], t, data,
                        xlabel = True, legend = False)

        fig.tight_layout()

        if country == 'United States of America':
            country = 'United States'
        country_ = country.replace(' ', '_')
        fig.savefig('effectiveness_{}.pdf'.format(country_))
        fig.savefig('effectiveness_{}.png'.format(country_))

    pyplot.show()


if __name__ == '__main__':
    _main()
