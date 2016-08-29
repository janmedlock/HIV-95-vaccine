#!/usr/bin/python3
'''
Make a table from the simulation output.
'''

import os
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model

countries = common.all_regions_and_countries

baseline = model.target.StatusQuo()
targets = [baseline, model.target.Vaccine(treatment_targets = baseline)]
targets = list(map(str, targets))

attrs = ['new_infections', 'infected', 'AIDS']

attr_names = dict(new_infections = 'New HIV Infections',
                  infected = 'PLHIV',
                  AIDS = 'People living with AIDS')

# Time points for comparison.
times = [2025, 2035]

stats = ('median', 'CI0', 'CI1')
alpha = 0.5


def _main():
    tuples = []
    for c in countries:
        for t in targets:
            tuples.append((c, t))
    ix = pandas.MultiIndex.from_tuples(tuples)

    tuples = []
    for t in times:
        for a in attrs:
            for s in stats:
                tuples.append((t, attr_names[a], s))
    cix = pandas.MultiIndex.from_tuples(tuples)

    df = pandas.DataFrame(index = ix, columns = cix)
    with model.results.samples.h5.open_() as results:
        for country in countries:
            for attr in attrs:
                for target in targets:
                    x = getattr(results[country][target], attr)
                    avg, CI = common.getstats(x, alpha = alpha)

                    for (v, s) in zip((avg, CI[0], CI[1]), stats):
                        z = numpy.interp(times, common.t, v)
                        for (i, t_) in enumerate(times):
                            df.loc[(country, target),
                                   (t_, attr_names[attr], s)] = z[i]

    # Round.
    # df = df.round()
    df = df.applymap(numpy.round)

    filename = '{}.csv'.format(common.get_filebase())
    df.to_csv(filename)

    return df


if __name__ == '__main__':
    df = _main()
