#!/usr/bin/python3
'''
Run the 90-90-90 policies for all the countries.
'''

import collections
import pickle

import joblib

import model


t_end = 20

countries = ('United States of America',
             'South Africa',
             'Rwanda',
             'Uganda',
             'India',
             'Haiti')
countries = ('United States of America', )

targets = ('baseline', '909090')

vaccine_times_to_start = (10, 5)
vaccine_levels = (0, 0.5, 0.75, 0.5)
vaccine_times_to_full_implementation = (5, 2)
vaccine_efficacies = (0.5, 0.75)


def _runone(country, t, parameters, **kwargs):
    print(country, t, kwargs)
    return model.Simulation(country, t,
                            parameters = parameters,
                            t_end = t_end,
                            run_baseline = False,
                            **kwargs)


def _helper(country):
    parameters = model.Parameters(country)
    # Need converted country name.
    country_ = parameters.country

    results = collections.OrderedDict()
    for t in targets:
        for v in vaccine_levels:
            if v > 0:
                for e in vaccine_efficacies:
                    for ts in vaccine_times_to_start:
                        for tfi in vaccine_times_to_full_implementation:
                            k = (t, v, e, ts, tfi)
                            results[k] = _runone(
                                country, t, parameters,
                                target_kwds = dict(
                                    vaccine_target = v,
                                    vaccine_time_to_start = ts,
                                    vaccine_time_to_full_implementation = tfi),
                                parameter_kwds = dict(
                                    vaccine_efficacy = e))
            else:
                # Don't need to run multiple vaccine parameters
                # when vaccine_target == 0.
                k = (t, v)
                results[k] = _runone(country, t,
                                     parameters,
                                     target_kwds = dict(
                                         vaccine_target = v))

    print('{}'.format(country_))
    return (country_, results)


def _main(parallel = True):
    if parallel:
        with joblib.Parallel(n_jobs = -1) as p:
            results = p(joblib.delayed(_helper)(country)
                        for country in countries)
    else:
        results = (_helper(country) for country in countries)

    pickle.dump(dict(results), open('909090.pkl', 'wb'))


if __name__ == '__main__':
    _main()
