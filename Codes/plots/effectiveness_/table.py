#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import pickle

import numpy
import pandas
import sys

sys.path.append('../..')
import model


def _main():
    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    # Time points for comparison.
    T = numpy.array([10, 20])

    results = pickle.load(open('../909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][levels[0]].t

    tuples = []
    for c in ['Global'] + countries:
        for l in ('Status Quo', '90–90–90'):
            tuples.append((c, l))
    ix = pandas.MultiIndex.from_tuples(tuples)

    tuples = []
    for T_ in T:
        year = int(T_ + 2015)
        for k in ('New HIV Infections', 'PLHIV', 'People living with AIDS'):
            tuples.append((year, k))
    cix = pandas.MultiIndex.from_tuples(tuples)

    df = pandas.DataFrame(index = ix, columns = cix)
    for (c, l) in ix:
        if c == 'Global':
            data = model.build_global(results)
        else:
            data = results[c]

        if l == 'Status Quo':
            k = kbaseline
        elif l == '90–90–90':
            k = k909090
        else:
            raise ValueError

        for (y, v) in cix:
            T_ = y - 2015
            if v == 'New HIV Infections':
                x = data[k].new_infections
            elif v == 'PLHIV':
                x = data[k].infected
            elif v == 'People living with AIDS':
                x = data[k].AIDS
            else:
                raise ValueError
            df.loc[(c, l), (y, v)] = numpy.interp(T_, t, x)

    # Round.
    # df = df.round()
    df = (df + 0.5).astype(int)

    df.to_csv('table.csv')

    return df


if __name__ == '__main__':
    df = _main()
