#!/usr/bin/python3
'''
Make a table from the 90-90-90 runs.
'''

import pickle

import numpy
import pandas


def _main():
    results = pickle.load(open('analyze909090.pkl', 'rb'))
    countries, values = zip(*results.items())
    state, stats, stats_base, stats_inc = map(numpy.array, zip(*values))

    t = state[0, 0, :]
    prevalence = state[:, 1, :]
    infections_averted = state[:, 2, :]
    
    df = pandas.DataFrame(index = countries)
    df['DALYs 90-90-90'] = stats[:, 0]
    df['QALYs 90-90-90'] = stats[:, 1]
    df['cost 90-90-90'] = stats[:, 2]
    df['DALYs baseline'] = stats_base[:, 0]
    df['QALYs baseline'] = stats_base[:, 1]
    df['cost baseline'] = stats_base[:, 2]
    df['incremental DALYs averted'] = stats_inc[:, 0]
    df['incremental QALYs added'] = stats_inc[:, 1]
    df['incremental cost added'] = stats_inc[:, 2]
    df['ICER DALYs'] = stats_inc[:, 3]
    df['ICER QALYs'] = stats_inc[:, 4]

    tau_values = numpy.hstack((numpy.arange(0, t[-1], 10), t[-1]))
    for tau in tau_values:
        d = numpy.zeros(len(countries))
        for i in range(len(countries)):
            d[i] = numpy.interp(tau,
                                t,
                                prevalence[i])
        df['prevalence at {:g} years'.format(tau)] = d

    # Skip t = 0
    for tau in tau_values[1 : ]:
        d = numpy.zeros(len(countries))
        for i in range(len(countries)):
            d[i] = numpy.interp(tau,
                                t,
                                infections_averted[i])
        df['infections averted at {:g} years'.format(tau)] = d

    df.to_csv('909090.csv')

    return df

if __name__ == '__main__':
    _main()
