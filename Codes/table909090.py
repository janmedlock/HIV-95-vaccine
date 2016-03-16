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

    for (c, r) in  results.items():
        s = pandas.Series()

        stats = model.get_effectiveness_and_cost(r.t, r.state,
                                                 r.target,
                                                 r.parameters)
        stats_base = model.get_effectiveness_and_cost(r.t, r.state_base,
                                                      r.target_base,
                                                      r.parameters)
        stats_inc = model.get_cost_effectiveness_stats(*(stats + stats_base),
                                                       r.parameters)

        s['DALYs 90-90-90'] = stats[0]
        # s['QALYs 90-90-90'] = stats[1]
        s['cost 90-90-90'] = stats[2]
        s['DALYs baseline'] = stats_base[0]
        # s['QALYs baseline'] = stats_base[1]
        s['cost baseline'] = stats_base[2]
        s['incremental DALYs averted'] = stats_inc[0]
        # s['incremental QALYs added'] = stats_inc[1]
        s['incremental cost added'] = stats_inc[2]
        s['ICER DALYs'] = stats_inc[3]
        # s['ICER QALYs'] = stats_inc[4]

        # Every 5 years.
        tau = numpy.hstack((numpy.arange(0, r.t[-1], 5), r.t[-1]))

        prevalence = r.state[:, 1 : -2].sum(1) / r.state[:, : -2].sum(1)
        infections_averted = ((r.state_base[:, -1] - r.state[:, -1])
                              / r.state_base[:, -1])
    
        for tau_ in tau:
            s['prevalence at {:g} years'.format(tau_)] \
                = numpy.interp(tau_, r.t, prevalence)

        # Skip t = 0
        for tau_ in tau[1 : ]:
            s['infections averted at {:g} years'.format(tau_)] \
                = numpy.interp(tau_, r.t, infections_averted)

        df[c] = s

    df = df.T

    df.to_csv('909090.csv')

    return df


if __name__ == '__main__':
    _main()
