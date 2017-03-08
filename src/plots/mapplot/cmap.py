'''
Helper functions for dealing with :mod:`matplotlib.cm` colormaps.
'''

import collections

from matplotlib import colors as mcolors


def _get_linear_transform(a, b):
    '''
    Map [a, b] to [0, 1].
    '''

    def f(x):
        '''
        Map [a, b] to [0, 1].
        '''
        return (x - a) / (b - a)

    return f


class _CDict(collections.OrderedDict):
    '''
    An object to hold the data for a colormap.
    '''
    def __init__(self):
        super().__init__()
        self['red'] = []
        self['green'] = []
        self['blue'] = []

    def append(self, x0, c0, c1):
        for (i, k) in enumerate(self):
            self[k].append((x0, c0[i], c1[i]))

    def get_cmap(self, name):
        return mcolors.LinearSegmentedColormap(name, self)


def combine(clist):
    '''
    Combine multiple colormaps into one.

    Takes a list of (x0, x1, cmap) elements
    where cmap is the colormap to use in between x0 and x1.

    The x0 and x1 values must be non-decreasing.
    '''
    a = clist[0][0]
    b = clist[-1][1]
    f = _get_linear_transform(a, b)

    cdict = _CDict()

    for (x0, x1, cmap) in clist:
        def g(y):
            '''
            Map [0, 1] to [x0, x1].
            '''
            return y * (x1 - x0) + x0

        for (k, v) in cmap._segmentdata.items():
            for (y, c0, c1) in v:
                cdict[k].append((f(g(y)), c0, c1))

    return cdict.get_cmap('combined')


def build(clist):
    '''
    Build a colormap from a list of colors and the points where they change.

    The list should have elements
    (x0, x1, c0, c1)
    where c0 starts at x0 and transitions linearly to c1 at x1.

    The x0 and x1 values must be non-decreasing.
    '''
    a = clist[0][0]
    b = clist[-1][1]
    f = _get_linear_transform(a, b)

    cdict = _CDict()

    c0 = None
    for (x1, x2, c1, c2) in clist:
        if c0 is None:
            cdict.append(x1, c1, c1)
        else:
            cdict.append(x1, c0, c1)
        c0 = c2
    cdict.append(x2, c2, c2)

    return cdict.get_cmap('custom')
