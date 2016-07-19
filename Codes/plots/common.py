'''
Common plotting settings etc.
'''

import inspect
import os.path

import matplotlib
from matplotlib import cm
from matplotlib import colors
from matplotlib import ticker
import numpy

# import seaborn
import sys
sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import seaborn_quiet as seaborn


countries_to_plot = ('Global',
                     'India',
                     'Rwanda',
                     'South Africa',
                     'United States of America')


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
    q = numpy.percentile(x, p, axis = 0)
    C = numpy.outer(p, numpy.ones(numpy.shape(x)[1]))
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
    return colors.LinearSegmentedColormap(cmap_base + '_reflected', cdict)


cmap_base = 'afmhot'
cmap = cmap_reflected(cmap_base)


_cp = seaborn.color_palette('Paired', 8)
_ix = [4, 5, 0, 1, 2, 3, 6, 7]
colors_paired = [_cp[i] for i in _ix]


def get_target_label(target):
    retval = str(target)
    i = retval.find('(')
    if i != -1:
        retval = retval[ : i]
    return retval
