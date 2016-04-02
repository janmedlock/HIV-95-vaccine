#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import pickle

import numpy
import pandas

import model


def _main():
    countries_to_show = ['Global', 'Haiti', 'India', 'Rwanda',
                         'South Africa', 'Uganda',
                         'United States of America']

    k909090 = ('909090', 0)
    kbaseline = ('baseline', 0)

    # Time points for comparison.
    T = numpy.array([10, 20])


    results = pickle.load(open('909090.pkl', 'rb'))

    countries = list(results.keys())
    levels = list(results[countries[0]].keys())
    t = results[countries[0]][levels[0]].t

    df = pandas.DataFrame()
    for c in countries_to_show:
        if c == 'Global':
            data = model.build_global(results, countries, levels, t)
        else:
            data = results[c]

        infections_averted = (data[kbaseline].new_infections
                              - data[k909090].new_infections)

        PLHIV_averted = (data[kbaseline].infected
                         - data[k909090].infected)
        
        AIDS_averted = (data[kbaseline].AIDS
                        - data[k909090].AIDS)
        
        s = pandas.Series()
        for T_ in T:
            s['infections averted in {:g}'.format(T_ + 2015)] \
                = numpy.interp(T_, t, infections_averted)
            s['PLHIV averted in {:g}'.format(T_ + 2015)] \
                = numpy.interp(T_, t, PLHIV_averted)
            s['AIDS averted in {:g}'.format(T_ + 2015)] \
                = numpy.interp(T_, t, AIDS_averted)

        df[c] = s

    df = df.T

    df.round().to_csv('table.csv')

    return df


if __name__ == '__main__':
    df = _main()
