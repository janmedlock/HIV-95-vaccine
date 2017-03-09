#!/usr/bin/python3
'''
Make a table from the simulation output.
'''

import os.path
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

stats = ['new_infections', 'infected', 'AIDS']

stat_names = dict(new_infections = 'Cumulative incidence',
                  infected = 'PLHIV',
                  AIDS = 'PLAIDS')

# Time points for comparison.
times = [2025, 2035]

summaries = ('median', 'CI0', 'CI1')
alpha = 0.5


def _get_summaries(x, alpha = 0.05):
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
    ix = pandas.MultiIndex.from_product((countries, targets))
    cix = pandas.MultiIndex.from_product((times,
                                          [stat_names[s] for s in stats],
                                          summaries))
    df = pandas.DataFrame(index = ix.sort_values(),
                          columns = cix.sort_values())
    for country in countries:
        print(country)
        for target in targets:
            results = model.results.load(country, target)
            for stat in stats:
                x = getattr(results, stat)
                avg, CI = _get_summaries(x, alpha = alpha)
                for (v, s) in zip((avg, CI[0], CI[1]), summaries):
                    z = numpy.interp(times, common.t, v)
                    df.loc[(country, target),
                           (slice(None), stat_names[stat], s)] = z

    # Round.
    # df = df.round()
    df = df.applymap(numpy.round)

    # Reorder.
    df = df.loc[ix].loc[:, cix]

    filename = '{}.csv'.format(common.get_filebase())
    df.to_csv(filename)

    return df


if __name__ == '__main__':
    df = _main()
