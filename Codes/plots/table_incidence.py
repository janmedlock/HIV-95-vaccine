#!/usr/bin/python3
'''
Make a table of the probability that `incidence[-1] > incidence[0]`.
'''

import os
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

countries = ['Global'] + sorted(model.datasheet.get_country_list())

target = model.targets.Vaccine(treatment_targets = model.targets.StatusQuo())

attr = 'incidence_per_capita'

# Time points for comparison.
times = [2025, 2035]


def _main():
    d = pandas.Series(index = countries)
    d.name = 'Incidence increasing'
    with model.results.ResultsCache() as results:
        for country in countries:
            try:
                t = results[country][target].t
                x = getattr(results[country][target], attr)
            except FileNotFoundError:
                pass
            else:
                s = 0
                for z in x:
                    v = numpy.interp(times, t, z)
                    if v[-1] > v[0]:
                        s += 1
                d[country] = s / len(x)

    filename = '{}.csv'.format(common.get_filebase())
    d.to_csv(filename)

    return d


if __name__ == '__main__':
    d = _main()
