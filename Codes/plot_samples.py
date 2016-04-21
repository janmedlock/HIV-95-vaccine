#!/usr/bin/python3

import os
import pickle
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


countries_to_plot = (
    # 'Global',
    'India',
    'Nigeria',
    'Rwanda',
    'South Africa',
    'Uganda',
    'United States of America',
)


resultsdir = 'results'

def load_results(country):
    with open(os.path.join(resultsdir, '{}.pkl'.format(country)), 'rb') as fd:
        results = pickle.load(fd)
    return results


def getfield(data, field):
    t = data.t
    retval = {}
    for (obj, k) in ((data.baseline, 'Status Quo'),
                     (data, '90–90–90')):
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

def plotcell(ax, tx,
             ylabel = None, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
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
    if xlabel:
        ax.set_xlabel('Year')
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'medium')
    ax.grid(True, which = 'both', axis = 'both')
    ax.set_xticks([2015, 2025, 2035])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter())
    if legend:
        ax.legend(loc = 'best')
    if title is not None:
        ax.set_title(title, size = 'medium')


def plot_selected():
    fig, axes = pyplot.subplots(len(countries_to_plot), 4,
                                figsize = (8.5, 11),
                                sharex = True,
                                squeeze = False)

    for (i, country) in enumerate(countries_to_plot):
        if country == 'Global':
            data = model.build_global()
        else:
            data = load_results(country)

        if country == 'United States of America':
            ylabel = 'United States'
        else:
            ylabel = country

        plotcell(axes[i, 0], getfield(data, 'infected'),
                 scale = 1e6,
                 xlabel = False, ylabel = ylabel, legend = (i == 0),
                 title = 'People Living with HIV\n(M)' if (i == 0) else None)
        plotcell(axes[i, 1], getfield(data, 'AIDS'),
                 scale = 1e3,
                 xlabel = False, ylabel = False, legend = False,
                 title = 'People with AIDS\n(1000s)' if (i == 0) else None)
        plotcell(axes[i, 2], getfield(data, 'incidence_per_capita'),
                 scale = 1e-6,
                 xlabel = False, ylabel = False, legend = False,
                 title = ('HIV Incidence\n(per M people per y)'
                          if (i == 0) else None))
        plotcell(axes[i, 3], getfield(data, 'prevalence'),
                 percent = True,
                 xlabel = False, ylabel = False, legend = False,
                 title = 'HIV Prevelance\n' if (i == 0) else None)

    fig.tight_layout()

    # fig.savefig('effectiveness.pdf')
    # fig.savefig('effectiveness.png')


if __name__ == '__main__':
    plot_selected()

    pyplot.show()
