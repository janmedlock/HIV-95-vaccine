#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.

.. todo:: Update with `results.Results` -> `results.data`.
          See `infections_averted_map.py`.
'''

import os
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

alpha = 0.5

keys_ordered = ('Status Quo', '90–90–90')

# Time points for comparison.
years = [2025, 2035]

measures = ('New HIV Infections', 'PLHIV', 'People living with AIDS')

def _main():
    countries = ['Global'] + sorted(model.get_country_list())

    stats = ('median', 'CI0', 'CI1')

    tuples = []
    for c in countries:
        for k in keys_ordered:
            tuples.append((c, k))
    ix = pandas.MultiIndex.from_tuples(tuples)

    tuples = []
    for y in years:
        for m in measures:
            for s in stats:
                tuples.append((y, m, s))
    cix = pandas.MultiIndex.from_tuples(tuples)

    df = pandas.DataFrame(index = ix, columns = cix)
    for c in countries:
        with model.results.Results(c) as results:
            for m in measures:
                if m == 'New HIV Infections':
                    tx = results.getfield('new_infections')
                elif m == 'PLHIV':
                    tx = results.getfield('infected')
                elif m == 'People living with AIDS':
                    tx = results.getfield('AIDS')
                else:
                    raise ValueError
                t, x = tx
                for k in keys_ordered:
                    avg, CI = common.getstats(x[k], alpha = alpha)

                    for (v, s) in zip((avg, CI[0], CI[1]), stats):
                        z = numpy.interp(years, t, v)
                        for (i, y) in enumerate(years):
                            df.loc[(c, k), (y, m, s)] = z[i]

    # Round.
    # df = df.round()
    df = (df + 0.5).astype(int)

    filename = '{}.csv'.format(common.get_filebase())
    df.to_csv(filename)

    return df


if __name__ == '__main__':
    df = _main()
