#!/usr/bin/python3

import os
import pickle
import warnings

import joblib
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


countries_to_plot = (
    # 'Global',
    'India',
    'Nigeria',
    'Rwanda',
    'South Africa',
    'Uganda',
    'United States of America',
)


class Results:
    resultsdir = 'results'

    def __init__(self, country):
        self._country = country
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        pass

    def _load_data(self):
        print('Loading data for {}...'.format(self._country)
        if self._country == 'Global':
            self._data = model.build_global()
        else:
            path = os.path.join(self.resultsdir,
                                '{}.pkl'.format(self._country))
            with open(path, 'rb') as fd:
                self._data = pickle.load(fd)

    def __getattr__(self, key):
        if self._data is None:
            self._load_data()
        return getattr(self._data, key)


@joblib.Memory(cachedir = '_joblib').cache(ignore = ['results'])
def getfield(country, field, results):
    t = results.t
    retval = {}
    for (obj, k) in ((results.baseline, 'Status Quo'),
                     (results, '90–90–90')):
        if field == 'incidence':
            ni = numpy.vstack(obj.new_infections)
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        elif field == 'incidence_per_capita':
            ni = numpy.vstack(obj.new_infections)
            n = numpy.vstack(obj.alive)
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
        elif field.endswith('_per_capita'):
            field_ = field.replace('_per_capita', '')
            x = numpy.vstack(getattr(obj, field_))
            n = numpy.vstack(obj.alive)
            retval[k] = x / n
        else:
            retval[k] = getattr(obj, field)
    if field.startswith('incidence'):
        t = t[1 : ]
    return (t, retval)


def getstats(x):
    avg = numpy.median(x, axis = 0)
    CIlevel = 0.5
    CI = numpy.percentile(x,
                          [100 * CIlevel / 2, 100 * (1 - CIlevel / 2)],
                          axis = 0)
    # avg = numpy.mean(x, axis = 0)
    # std = numpy.std(x, axis = 0, ddof = 1)
    # CI = [avg + std, avg - std]
    return (avg, CI)


def getpercentiles(x):
    p = numpy.linspace(0, 100, 101)
    q = numpy.percentile(x, p, axis = 0)
    C = numpy.outer(2 * numpy.abs(p / 100 - 0.5),
                    numpy.ones(numpy.shape(x)[1]))
    return (q, C)


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'

cp = seaborn.color_palette('colorblind')
colors = {'Status Quo': cp[2],
          '90–90–90': cp[0]}
# cp = seaborn.color_palette('Dark2')
# colors = {'Status Quo': cp[1],
#           '90–90–90': cp[0]}

def plotcell(ax, tx,
             scale = 1, percent = False,
             xlabel = None, ylabel = None, title = None, legend = True):
    t, x = tx

    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(max(x) for x in stats.values()) > 1e6:
            scale = 1e6
        else:
            scale = 1e3

    for k in ('Status Quo', '90–90–90'):
        v = x[k]
        avg, CI = getstats(v)
        ax.plot(t + 2015, avg / scale, color = colors[k], label = k,
                zorder = 2)
        ax.fill_between(t + 2015, CI[0] / scale, CI[1] / scale,
                        color = colors[k],
                        alpha = 0.3)
        # q, C = getpercentiles(v)
        # ax.pcolormesh(t + 2015, q / scale, C,
        #               cmap = cmaps[k], alpha = 0.5)

    ax.set_xlim(t[0] + 2015, t[-1] + 2015)
    ax.grid(True, which = 'both', axis = 'both')
    ax.set_xticks([2015, 2025, 2035])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'medium')
    if title is not None:
        ax.set_title(title, size = 'medium')
    if legend:
        ax.legend(loc = 'best')


def plot_selected():
    fig, axes = pyplot.subplots(len(countries_to_plot), 4,
                                figsize = (8.5, 11),
                                sharex = True,
                                squeeze = False)

    for (i, country) in enumerate(countries_to_plot):
        with Results(country) as results:
            if country == 'United States of America':
                ylabel = 'United States'
            else:
                ylabel = country

            plotcell(axes[i, 0],
                     getfield(country, 'infected', results),
                     scale = 1e6,
                     ylabel = ylabel, legend = (i == 0),
                     title = ('People Living with HIV\n(M)'
                              if (i == 0) else None))

            plotcell(axes[i, 1],
                     getfield(country, 'AIDS', results),
                     scale = 1e3,
                     legend = False,
                     title = ('People with AIDS\n(1000s)'
                              if (i == 0) else None))

            plotcell(axes[i, 2],
                     getfield(country, 'incidence_per_capita', results),
                     scale = 1e-6,
                     legend = False,
                     title = ('HIV Incidence\n(per M people per y)'
                              if (i == 0) else None))

            plotcell(axes[i, 3],
                     getfield(country, 'prevalence', results),
                     percent = True,
                     legend = False,
                     title = ('HIV Prevelance\n'
                              if (i == 0) else None))

    fig.tight_layout()

    fig.savefig('effectiveness.pdf')
    fig.savefig('effectiveness.png')


if __name__ == '__main__':
    plot_selected()

    pyplot.show()
