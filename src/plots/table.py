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
targets = [baseline, model.target.Vaccine(treatment_target = baseline)]
targets = list(map(str, targets))

attrs = ['new_infections', 'infected', 'AIDS']

attr_names = dict(new_infections = 'New HIV Infections',
                  infected = 'PLHIV',
                  AIDS = 'People living with AIDS')

# Time points for comparison.
times = [2025, 2035]

stats = ('median', 'CI0', 'CI1')
alpha = 0.5


def _get_stats(x, alpha = 0.05):
    y = numpy.asarray(x).copy()

    # Set columns with NaNs to 0.
    ix = numpy.any(numpy.isnan(y), axis = 0)
    y[..., ix] = 0

    avg = numpy.median(y, axis = 0)
    CI = numpy.percentile(y,
                          [100 * alpha / 2, 100 * (1 - alpha / 2)],
                          axis = 0)
    # avg = numpy.mean(y, axis = 0)
    # std = numpy.std(y, axis = 0, ddof = 1)
    # CI = numpy.vstack((avg - std, avg + std))

    # Set the columns where y has NaNs to NaN.
    avg[..., ix] = numpy.nan
    CI[..., ix] = numpy.nan

    return (avg, CI)


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
                    avg, CI = _get_stats(x, alpha = alpha)

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
