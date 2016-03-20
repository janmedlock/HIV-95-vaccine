#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import pickle

import numpy
import pandas

import model


def _main():
    results = pickle.load(open('909090.pkl', 'rb'))

    df = pandas.DataFrame()

    for (c, r) in results.items():
        s = pandas.Series()

        s['DALYs 90-90-90'] = r.DALYs
        s['cost 90-90-90'] = r.cost
        s['DALYs baseline'] = r.baseline.DALYs
        s['cost baseline'] = r.baseline.cost
        s['incremental DALYs averted'] = r.incremental_DALYs
        s['incremental cost added'] = r.incremental_cost
        s['ICER DALYs'] = r.ICER_DALYs

        # Every 5 years.
        t = numpy.hstack((numpy.arange(0, r.t[-1], 5), r.t[-1]))

        for t_ in t:
            s['prevalence at {:g} years'.format(t_)] \
                = numpy.interp(t_, r.t, r.prevalence)

        infections_averted = (
            (r.baseline.new_infections - r.new_infections)
            / r.baseline.new_infections)
        # Skip t = 0
        for t_ in t[1 : ]:
            s['infections averted at {:g} years'.format(t_)] \
                = numpy.interp(t_, r.t, infections_averted)

        df[c] = s

    df = df.T

    df.to_csv('table909090.csv')

    return df


if __name__ == '__main__':
    _main()
