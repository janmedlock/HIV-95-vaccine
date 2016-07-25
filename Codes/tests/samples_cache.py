#!/usr/bin/python3
'''
Test :mod:`model.results.sample_cache`.
'''


import sys

import numpy

sys.path.append('..')
import model


if __name__ == '__main__':
    country = 'South Africa'
    target = 'Status Quo'
    attr = 'new_infections'

    with model.results.ResultsCache() as cache:
        ccache = cache[country]
        ctcache = ccache[target]
        val = getattr(ctcache, attr)
        print(numpy.shape(val))
