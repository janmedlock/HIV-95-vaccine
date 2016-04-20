#!/usr/bin/python3

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
    # 'India',
    'Nigeria',
    # 'Rwanda',
    'South Africa',
    'Uganda',
    'United States of America')

resultsfile = 'results.pkl'


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


class PercentFormatter(ticker.ScalarFormatter):
    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '%%$'
        elif self._useMathText:
            self.format = self.format[: -2] + '%%}$'
        else:
            self.format += '%%'


def baseplot(ax, t, stats, ylabel = None, scale = 1,
             legend = True, xlabel = True, title = None,
             percent = False):
    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(max(x) for x in stats.values()) > 1e6:
            scale = 1e6
        else:
            scale = 1e3
    for (k, v) in stats.items():
        avg, CI = v
        p = ax.plot(t + 2015, avg / scale, label = k,
                    linewidth = 2, zorder = 2)
        ax.fill_between(t + 2015, CI[0] / scale, CI[1] / scale,
                        color = p[0].get_color(),
                        alpha = 0.3)
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
        # ax.legend(loc = 'upper left')
        ax.legend(loc = 'best')
    if title is not None:
        ax.set_title(title, size = 'medium')


def getattr_(data, attrname):
    t = data.t
    retval = {}
    for (obj, k) in ((data.baseline, 'Status Quo'),
                     (data, '90–90–90')):
        if attrname == 'incidence':
            ni = numpy.vstack(obj.new_infections)
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        elif attrname == 'incidence_per_capita':
            ni = numpy.vstack(obj.new_infections)
            n = numpy.vstack(obj.alive)
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
        elif attrname.endswith('_per_capita'):
            attrname_ = attrname.replace('_per_capita', '')
            x = numpy.vstack(getattr(obj, attrname_))
            n = numpy.vstack(obj.alive)
            retval[k] = x / n
        else:
            retval[k] = getattr(obj, attrname)
    if attrname.startswith('incidence'):
        t = t[1 : ]
    return (t, retval)


def counts(data, attrname):
    t, x = getattr_(data, attrname)
    return (t, {k: getstats(v) for (k, v) in x.items()})


def difference(data, attrname):
    t, x = getattr_(data, attrname)
    diff = x['Status Quo'] - x['90–90–90']
    return (t, getstats(diff))


def relative_difference(data, attrname):
    t, x = getattr_(data, attrname)
    reldiff = (x['Status Quo'] - x['90–90–90']) / x['Status Quo']
    return (t, getstats(reldiff))


def infected(ax, data, scale = 'auto', **kwargs):
    t, stats = counts(data, 'infected')
    baseplot(ax, t, stats, scale = scale, **kwargs)


def AIDS(ax, data, scale = 'auto', **kwargs):
    t, stats = counts(data, 'AIDS')
    baseplot(ax, t, stats, scale = scale, **kwargs)


def incidence(ax, data, scale = 1 / 1e6, **kwargs):
    t, stats = counts(data, 'incidence_per_capita')
    baseplot(ax, t, stats, scale = scale, **kwargs)


def prevalence(ax, data, **kwargs):
    t, stats = counts(data, 'prevalence')
    baseplot(ax, t, stats, percent = True, **kwargs)


def plot_selected(results):
    if 'Global' in countries_to_plot:
        r = model.build_global(results)
        results['Global'] = r

    fig, axes = pyplot.subplots(len(countries_to_plot), 4,
                                figsize = (8.5, 11),
                                sharex = True)
    for (i, country) in enumerate(countries_to_plot):
        try:
            data = results[country]
        except KeyError:
            pass
        else:
            if country == 'United States of America':
                country = 'United States'
            if i == 0:
                titles = ['People Living with HIV\n(M)',
                          'People with AIDS\n(1000s)',
                          'HIV Incidence\n(per M people per y)',
                          'HIV Prevelance\n']
            else:
                titles = [None, None, None, None]
            infected(axes[i, 0], data,
                     scale = 1e6,
                     xlabel = False, ylabel = country,
                     legend = (i == 0),
                     title = titles[0])
            AIDS(axes[i, 1], data,
                 scale = 1e3,
                 xlabel = False, legend = False,
                 title = titles[1])
            incidence(axes[i, 2], data,
                      xlabel = False, legend = False,
                      title = titles[2])
            prevalence(axes[i, 3], data,
                       xlabel = False, legend = False,
                       title = titles[3])

    fig.tight_layout()

    # fig.savefig('effectiveness.pdf')
    # fig.savefig('effectiveness.png')


if __name__ == '__main__':
    with open(resultsfile, 'rb') as fd:
        results = pickle.load(fd)

    plot_selected(results)

    pylab.show()
