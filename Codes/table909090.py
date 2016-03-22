#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import pickle

import numpy
import pandas


def _main():
    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    results = pickle.load(open('909090.pkl', 'rb'))

    df = pandas.DataFrame()

    for (c, r) in results.items():
        s = pandas.Series()

        s['DALYs 90-90-90'] = r[k909090].DALYs
        s['cost 90-90-90'] = r[k909090].cost
        s['DALYs baseline'] = r[kbaseline].DALYs
        s['cost baseline'] = r[kbaseline].cost

        t = r[k909090].t

        # Every 5 years.
        T = numpy.hstack((numpy.arange(0, t[-1], 5), t[-1]))

        for T_ in T:
            s['prevalence at {:g} years'.format(T_)] \
                = numpy.interp(T_, t, r[k909090].prevalence)

        infections_averted = (
            (r[kbaseline].new_infections - r[k909090].new_infections)
            / r[kbaseline].new_infections)
        # Skip t = 0
        for T_ in T[1 : ]:
            s['infections averted at {:g} years'.format(T_)] \
                = numpy.interp(T_, t, infections_averted)

        df[c] = s

    df = df.T

    df.to_csv('table909090.csv')

    return df


if __name__ == '__main__':
    _main()
