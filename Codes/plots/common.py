'''
Common plotting settings etc.
'''

import inspect
import os.path
import warnings

import matplotlib
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


countries_to_plot = (
    'Global',
    'India',
    'Nigeria',
    'Rwanda',
    'South Africa',
    'Uganda',
    'United States of America',
)


matplotlib.rc('axes.grid', which = 'both')  # major & minor


def get_filebase():
    stack = inspect.stack()
    caller = stack[1]
    filebase, _ = os.path.splitext(caller.filename)
    return filebase


def getstats(x, alpha = 0.5):
    avg = numpy.median(x, axis = 0)
    CI = numpy.percentile(x,
                          [100 * alpha / 2, 100 * (1 - alpha / 2)],
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
