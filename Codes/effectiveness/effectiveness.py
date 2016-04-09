#!/usr/bin/python3
'''
Make 2-d plots of incidence, prevalence, etc.
'''

import collections
import itertools
import pickle
import sys
import warnings

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
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
        ax.plot(t + 2015, data[k] / scale,
                label = getlabel(k))
    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    if xlabel:
        ax.set_xlabel('Year')
    if (ylabel is not None) and (scale > 1) and (not percent):
        if scale == 1e3:
            ylabel += '\n(1000s)'
        elif scale == 1e6:
            ylabel += '\n(M)'
        else:
            ylabel += '\n({:g})'.format(scale)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 7))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())
    if legend:
        # ax.legend(loc = 'upper left')
        ax.legend(loc = 'best')
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


def new_infections(ax, t, data, ylabel = True, scale = 1e6, **kwargs):
    data_ = counts(data, 'new_infections')
    if ylabel:
        ylabel = 'New Infections'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, scale = scale, **kwargs)


def incidence(ax, t, data, ylabel = True, scale = 1 / 1e6, **kwargs):
    data_ = counts(data, 'incidence_per_capita', t)
    if ylabel:
        ylabel = 'HIV Incidence\n(per M people per y)'
    else:
        ylabel = None
    baseplot(ax, t[1 : ], data_, ylabel = ylabel, scale = scale, **kwargs)


def dead(ax, t, data, ylabel = True, **kwargs):
    data_ = counts(data, 'dead')
    if ylabel:
        ylabel = 'AIDS Deaths'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, **kwargs)


def infected(ax, t, data, ylabel = True, scale = 'auto', **kwargs):
    data_ = counts(data, 'infected')
    if ylabel:
        ylabel = 'People Living with HIV'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, scale = scale, **kwargs)


def AIDS(ax, t, data, ylabel = True, scale = 'auto', **kwargs):
    data_ = counts(data, 'AIDS')
    if ylabel:
        ylabel = 'People with AIDS'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, scale = scale, **kwargs)


def AIDS_per_capita(ax, t, data, ylabel = True, **kwargs):
    data_ = counts(data, 'AIDS_per_capita')
    if ylabel:
        ylabel = 'AIDS per capita'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, percent = True, **kwargs)


def prevalence(ax, t, data, ylabel = True, **kwargs):
    data_ = counts(data, 'prevalence')
    if ylabel:
        ylabel = 'HIV Prevalence'
    else:
        ylabel = None
    baseplot(ax, t, data_, ylabel = ylabel, percent = True, **kwargs)


def plot_selected(results):
    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][k909090].t
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    fig, axes = pyplot.subplots(4, len(countries_to_plot),
                                figsize = (20, 8.5), sharex = True)
    for (i, country) in enumerate(countries_to_plot):
        data = results[country]
        if country == 'United States of America':
            country = 'United States'
        ylabel = (i == 0)
        infected(axes[0, i], t, data,
                 scale = 1e6,
                 xlabel = False, ylabel = ylabel,
                 legend = (i == 0),
                 title = country)
        AIDS(axes[1, i], t, data,
             scale = 1e3,
             xlabel = False, ylabel = ylabel, legend = False)
        incidence(axes[2, i], t, data,
                  xlabel = False, ylabel = ylabel, legend = False)
        prevalence(axes[3, i], t, data,
                   xlabel = (i == len(countries_to_plot) // 2),
                   ylabel = ylabel, legend = False)

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

    pdf = backend_pdf.PdfPages('effectiveness_all.pdf')
    for (i, country) in enumerate(['Global'] + countries):
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
        # country_ = country.replace(' ', '_')
        # fig.savefig('effectiveness.pdf')
        # fig.savefig('effectiveness.png')
    pdf.close()


if __name__ == '__main__':
    results = pickle.load(open('../909090.pkl', 'rb'))

    plot_selected(results)
    # plot_all(results)

    # pyplot.show()
