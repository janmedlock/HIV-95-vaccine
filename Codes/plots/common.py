'''
Common plotting settings etc.
'''

import collections
import copy
import inspect
import operator
import os.path
import sys

import matplotlib
from matplotlib import cm
from matplotlib import colors as mcolors
from matplotlib import ticker
import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('..')
import model


countries_to_plot = ('Global',
                     'India',
                     'Rwanda',
                     'South Africa',
                     'United States of America')


country_label_replacements = {
    'United States of America': 'United States'
}


effectiveness_measures = ['infected', 'incidence_per_capita', 'AIDS', 'dead']


t = numpy.linspace(2015, 2035, 20 * 120 +1)


# historical_data_start_year = 1990
historical_data_start_year = 2005

historical_data_style = dict(marker = '.',
                             markersize = 10,
                             alpha = 0.7,
                             color = 'black')


_parameter_names_map = dict(
    coital_acts_per_year = 'annual\nsex\nacts',
    death_years_lost_by_suppression = 'life-years lost:\non suppression',
    progression_rate_acute = 'acute\nprogression\nrate',
    suppression_rate = 'suppression\nrate',
    transmission_rate_quantile = 'transmission\nrate',
    transmission_per_coital_act_acute = 'transmission\nper coital act:\nacute',
    transmission_per_coital_act_unsuppressed \
        = 'transmission\nper coital act:\nunsuppressed',
    transmission_per_coital_act_reduction_by_suppression \
        = 'transmission\nper coital act:\nreduction by\nsuppression'
)

parameter_names = [_parameter_names_map[p]
                   for p in model.parameters.Parameters.get_rv_names()]


matplotlib.rc('axes.grid', which = 'both')  # major & minor


def get_filebase():
    stack = inspect.stack()
    caller = stack[1]
    filebase, _ = os.path.splitext(caller.filename)
    return filebase


def getstats(x, alpha = 0.05):
    y = numpy.asarray(x).copy()

    # Set columns with NaNs to 0.
    ix = numpy.any(numpy.isnan(y), axis = 0)
    y[..., ix] = 0

    avg = numpy.median(y, axis = 0)
    CI = numpy.percentile(y,
                          [100 * alpha / 2, 100 * (1 - alpha / 2)],
                          axis = 0)
    # avg = numpy.mean(y, axis = 0)
    # std = numpy.std(y, axis = 0, ddof = 1)
    # CI = numpy.vstack((avg - std, avg + std))

    # Set the columns where y has NaNs to NaN.
    avg[..., ix] = numpy.nan
    CI[..., ix] = numpy.nan

    return (avg, CI)


def getpercentiles(x):
    p = numpy.linspace(0, 100, 101)
    # Plot the points near 50% last, so they show up clearest.
    # This gives [0, 100, 1, 99, 2, 98, ..., 48, 52, 49, 51, 50].
    M = len(p) // 2
    p_ = numpy.column_stack((p[ : M], p[-1 : -(M + 1) : -1]))
    p_ = p_.flatten()
    if len(p) % 2 == 1:
        p_ = numpy.hstack((p_, p[M]))
    q = numpy.percentile(x, p_, axis = 0)
    C = numpy.outer(p_, numpy.ones(numpy.shape(x)[1]))
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


class UnitsFormatter(ticker.ScalarFormatter):
    def __init__(self, units):
        self.units = units
        super().__init__()

    def _set_format(self, vmin, vmax):
        super()._set_format(vmin, vmax)
        if self._usetex:
            self.format = self.format[: -1] + '{}$'.format(self.units)
        elif self._useMathText:
            self.format = self.format[: -2] + '{}}}$'.format(self.units)
        else:
            self.format += self.units


def cmap_reflected(cmap_base):
    if cmap_base.endswith('_r'):
        cmap_base_r = cmap_base[ : -2]
    else:
        cmap_base_r = cmap_base + '_r'
    cmaps = (cmap_base_r, cmap_base)
    cmaps_ = [cm.get_cmap(c) for c in cmaps]
    def cfunc(k):
        def f(x):
            return numpy.where(x < 0.5,
                               cmaps_[0]._segmentdata[k](2 * x),
                               cmaps_[1]._segmentdata[k](2 * (x - 0.5)))
        return f
    cdict = {k: cfunc(k) for k in ('red', 'green', 'blue')}
    return mcolors.LinearSegmentedColormap(cmap_base + '_reflected', cdict)


_cmap_percentile_base = 'cubehelix'
cmap_percentile = cmap_reflected(_cmap_percentile_base)


def cmap_scaled(cmap_base, vmin = 0, vmax = 1, N = 256):
    cmap = cm.get_cmap(cmap_base)
    pts = numpy.linspace(vmin, vmax, N)
    colors = cmap(pts)
    return mcolors.LinearSegmentedColormap.from_list(cmap_base + '_scaled',
                                                     colors)


_cp = seaborn.color_palette('Paired', 12)
_ix = [4, 5, 0, 1, 2, 3, 6, 7, 8, 9, 10, 11]
colors_paired = [_cp[i] for i in _ix]


def get_target_label(target):
    retval = str(target)
    i = retval.find('(')
    if i != -1:
        retval = retval[ : i]
    return retval


class StatInfoEntry:
    def __init__(self, **kwargs):
        # Defaults
        self.percent = False
        self.scale = None
        self.units = ''
        for (k, v) in kwargs.items():
            setattr(self, k, v)
        if self.percent:
            self.scale = 1 / 100
            self.units = '%%'
        
    def autoscale(self, data):
        if len(data) > 0:
            vmax = numpy.max(data)
            if vmax > 1e6:
                self.scale = 1e6
                self.units = 'M'
            elif vmax > 1e3:
                self.scale = 1e3
                self.units = 'k'
            else:
                self.scale = 1
                self.units = ''
        else:
            self.scale = 1
            self.units = ''
        

_stat_info = dict(
    infected = StatInfoEntry(label = 'PLHIV'),
    prevalence = StatInfoEntry(label = 'Prevalence',
                               percent = True),
    incidence_per_capita = StatInfoEntry(label = 'Incidence\n(per M per y)',
                                         scale = 1e-6),
    drug_coverage = StatInfoEntry(label = 'ART\nCoverage',
                                  percent = True),
    AIDS = StatInfoEntry(label = 'AIDS'),
    dead = StatInfoEntry(label = 'HIV-Related\nDeaths'),
    viral_suppression = StatInfoEntry(label = 'Viral\nSupression',
                                      percent = True),
    new_infections = StatInfoEntry(label = 'New Infections'),
)


def get_stat_info(stat):
    try:
        return copy.copy(_stat_info[stat])
    except KeyError:
        return StatInfoEntry(label = stat.title())


def _none_func():
    def f(*args, **kwargs):
        return None
    return f

def data_infected_getter(parameters):
    return parameters.prevalence * parameters.population

# Everything not listed returns 'None', indicating no data.
data_hist_getter = collections.defaultdict(
    _none_func,
    infected = data_infected_getter,
    prevalence = operator.attrgetter('prevalence'),
    incidence_per_capita = operator.attrgetter('incidence_per_capita'),
    drug_coverage = operator.attrgetter('drug_coverage')
)


class DataGetter(dict):
    def __init__(self):
        self['drug_coverage'] = operator.attrgetter('proportions.treated')
        self['viral_suppress'] = self.viral_suppression_getter

    def __getitem__(self, key):
        try:
            super().__getitem__(key)
        except KeyError:
            # Default: return a attrgetter on 'key'.
            return operator.attrgetter(key)

    @staticmethod
    def viral_suppression_getter(results):
        return (numpy.asarray(results.viral_suppression)
                / numpy.asarray(results.infected))

data_getter = DataGetter()


def format_axes(ax, country, info,
                country_label, attr_label,
                plot_hist = False, tick_interval = 10):
    '''
    Do common formatting.
    '''
    if plot_hist:
        a = historical_data_start_year
    else:
        a = int(numpy.floor(t[0]))
    b = int(numpy.ceil(t[-1]))
    ticks = range(a, b, tick_interval)
    if ((b - a) % tick_interval) == 0:
        ticks = list(ticks) + [b]
    ax.set_xticks(ticks)
    ax.set_xlim(a, b)

    ax.grid(True, which = 'both', axis = 'both')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset = False))
    ax.yaxis.set_major_formatter(UnitsFormatter(info.units))
    # One minor tick between major ticks.
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    country_str = country_label_replacements.get(country, country)
    if country_label == 'ylabel':
        ax.set_ylabel(country_str, size = 'medium')
    elif country_label == 'title':
        ax.set_title(country_str, size = 'medium')

    if attr_label == 'ylabel':
        ax.set_ylabel(info.label, size = 'medium')
    elif attr_label == 'title':
        ax.set_title(info.label, size = 'medium')
