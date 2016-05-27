#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import os
import pickle
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

key = '90–90–90'

# Time points for comparison.
years = [2025, 2035]


def _main():
    countries = ['Global'] + sorted(model.get_country_list())

    d = pandas.Series(index = countries)
    d.name = 'Incidence increasing'
    for c in countries:
        with model.results.Results(c) as results:
            tx = results.getfield('incidence_per_capita')
            t, x = tx
            y = x[key]
            s = 0
            for z in y:
                v = numpy.interp(years, t + 2015, z)
                if v[-1] > v[0]:
                    s += 1
            d[c] = s / len(y)

    filename = '{}.csv'.format(common.get_filebase())
    d.to_csv(filename)

    return d


if __name__ == '__main__':
    d = _main()
