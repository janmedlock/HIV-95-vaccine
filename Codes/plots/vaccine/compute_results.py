#!/usr/bin/python3
'''
Run the 90-90-90 policies for all the countries.
'''

import collections
import itertools
import pickle
import sys

import joblib

import effectiveness
sys.path.append('../..')
import model


# countries = effectiveness.countries_to_plot
countries = model.get_country_list()

targets = ('baseline', '909090')

vaccine_targets = (0, 0.5, 0.75)
vaccine_efficacies = (0.5, 0.75)
vaccine_times_to_start = (2020, )
# vaccine_times_to_full_implementation = (2025, 2022)
vaccine_times_to_full_implementation = (2022, )

vaccine_info = []
if 0 in vaccine_targets:
    vaccine_info.append((0, ))
    vaccine_targets = [v for v in vaccine_targets if v!= 0]
params = (vaccine_times_to_start,
          vaccine_targets,
          vaccine_efficacies,
          vaccine_times_to_full_implementation)
for (ts, v, e, tfi) in itertools.product(*params):
    vaccine_info.append((v, e, ts, tfi))


def _get_key(targets, vaccine_target, *args):
    return (targets, vaccine_target) + args


def _get_kwds(vaccine_target, *args):
    kwds = {}
    if args:
        (vaccine_efficacy,
         vaccine_time_to_start,
         vaccine_time_to_full_implementation) = args
        kwds.update(vaccine_efficacy = vaccine_efficacy)
        vaccine_target_ = model.Target(vaccine_target,
                                       vaccine_time_to_start,
                                       vaccine_time_to_full_implementation)
    else:
        vaccine_target_ = model.Target(vaccine_target)
    kwds.update(targets_kwds = dict(vaccine_target = vaccine_target_))
    return kwds


def _run_one(key, parameters, targets_, **kwargs):
    print(parameters.country, targets_, kwargs)
    return (key, model.Simulation(parameters, targets_,
                                  baseline_targets = None,
                                  **kwargs))


def _run_country(country, parallel = True):
    parameters = model.ParameterMode.from_country(country)
    # parameters.progression_rate_suppressed \
    #     = parameters.progression_rate_unsuppressed
    # Need converted country name.
    country_ = parameters.country

    jobs = []
    keys_ordered = []
    for x in itertools.product(targets, vaccine_info):
        targets_, vaccine_info_ = x
        key = _get_key(targets_, *vaccine_info_)
        keys_ordered.append(key)
        jobs.append(joblib.delayed(_run_one)(
            key, parameters, targets_, **_get_kwds(*vaccine_info_)))

    if parallel:
        with joblib.Parallel(n_jobs = -1) as parallel_:
            results = parallel_(jobs)
    else:
        results = (f(*args, **kwds) for (f, args, kwds) in jobs)
    results = dict(results)

    # Order results
    results_ = collections.OrderedDict()
    for k in keys_ordered:
        results_[k] = results[k]

    return (country_, results_)


def _main(parallel = True):
    results = collections.OrderedDict()
    for country in countries:
        country_, results_ = _run_country(country, parallel = parallel)
        results[country_] = results_
    pickle.dump(results, open('results.pkl', 'wb'))


if __name__ == '__main__':
    _main()
