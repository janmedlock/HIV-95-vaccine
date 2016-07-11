#!/usr/bin/python3
'''
Make 2-d plots of incidence, prevalence, etc.
'''

import collections
import itertools
import sys

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy

sys.path.append('../..')
import model
from model import picklefile


countries_to_plot = ('Global',
                     'India',
                     'Nigeria',
                     'Rwanda',
                     'South Africa',
                     'Uganda',
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


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'


def baseplot(ax, t, data, ylabel = None, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(data[kbaseline]) > 1e6:
            scale = 1e6
        else:
            scale = 1e3
    for k in (kbaseline, k909090):
        ax.plot(t, data[k] / scale, label = getlabel(k))
    ax.set_xlim(t[0], t[-1])
    if xlabel:
        ax.set_xlabel('Year')
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'medium')
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(data_start_year, int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())
    if legend:
        # ax.legend(loc = 'upper left')
        ax.legend(loc = 'best')
    if title is not None:
        ax.set_title(title, size = 'medium')


def getattr_(data, attrname, t = None):
    return {k: getattr(data[k], attrname) for k in (kbaseline, k909090)}


def counts(data, attrname, t = None):
    return getattr_(data, attrname, t)


def difference(data, attrname):
    a, b = getattr_(data, attrname)
    return a - b


def relative_difference(data, attrname):
    a, b = getattr_(data, attrname)
    return (a - b) / a


def new_infections(ax, t, data, scale = 1e6, **kwargs):
    data_ = counts(data, 'new_infections')
    baseplot(ax, t, data_, scale = scale, **kwargs)


def incidence(ax, t, data, scale = 1 / 1e6, **kwargs):
    data_ = counts(data, 'incidence_per_capita', t)
    baseplot(ax, t[1 : ], data_, scale = scale, **kwargs)


def dead(ax, t, data, scale = 'auto', **kwargs):
    data_ = counts(data, 'dead')
    baseplot(ax, t, data_, **kwargs)


def infected(ax, t, data, scale = 'auto', **kwargs):
    data_ = counts(data, 'infected')
    baseplot(ax, t, data_, scale = scale, **kwargs)


def AIDS(ax, t, data, scale = 'auto', **kwargs):
    data_ = counts(data, 'AIDS')
    baseplot(ax, t, data_, scale = scale, **kwargs)


def AIDS_per_capita(ax, t, data, **kwargs):
    data_ = counts(data, 'AIDS_per_capita')
    baseplot(ax, t, data_, percent = True, **kwargs)


def prevalence(ax, t, data, **kwargs):
    data_ = counts(data, 'prevalence')
    baseplot(ax, t, data_, percent = True, **kwargs)


def plot_selected(results):
    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    fig, axes = pyplot.subplots(len(countries_to_plot), 4,
                                figsize = (8.5, 11),
                                sharex = True)
    for (i, country) in enumerate(countries_to_plot):
        data = results[country]
        if country == 'United States of America':
            country = 'United States'
        xlabel = False # (i == len(countries_to_plot) - 1)
        if i == 0:
            titles = ['People Living with HIV\n(M)',
                      'People with AIDS\n(1000s)',
                      'HIV Incidence\n(per M people per y)',
                      'HIV Prevelance\n']
        else:
            titles = [None, None, None, None]
        infected(axes[i, 0], t, data,
                 scale = 1e6,
                 xlabel = xlabel, ylabel = country,
                 legend = (i == 0),
                 title = titles[0])
        AIDS(axes[i, 1], t, data,
             scale = 1e3,
             xlabel = xlabel, legend = False,
             title = titles[1])
        incidence(axes[i, 2], t, data,
                  xlabel = xlabel, legend = False,
                  title = titles[2])
        prevalence(axes[i, 3], t, data,
                   xlabel = xlabel, legend = False,
                   title = titles[3])

    fig.tight_layout()

    fig.savefig('effectiveness.pdf')
    fig.savefig('effectiveness.png')
    

def plot_all(results):
    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries:
        r = model.build_global(results)
        results['Global'] = r

    with backend_pdf.PdfPages('effectiveness_all.pdf') as pdf:
        country_list = ['Global'] + sorted(countries)
        for (i, country) in enumerate(country_list):
            fig, axes = pyplot.subplots(4,
                                        figsize = (11, 8.5), sharex = True)
            data = results[country]
            if country == 'United States of America':
                country = 'United States'
            infected(axes[0], t, data,
                     xlabel = False, legend = True,
                     title = country)
            AIDS(axes[1], t, data,
                 xlabel = False, legend = False)
            incidence(axes[2], t, data,
                      xlabel = False, legend = False)
            prevalence(axes[3], t, data,
                       xlabel = True, legend = False)

            fig.tight_layout()

            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    results = picklefile.load('../909090.pkl')

    plot_selected(results)
    plot_all(results)

    # pyplot.show()
