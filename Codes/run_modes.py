#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
run simulations.
'''

import collections

import joblib

import model


def _run_one(country, targets = None):
    if targets is None:
        targets = model.targets.all_
    parameters = model.parameters.Parameters(country)
    parameter_values = parameters.mode()
    results = joblib.Parallel(n_jobs = -1)(
        joblib.delayed(model.simulation.Simulation)(parameter_values,
                                                    target)
        for target in targets)
    retval = collections.OrderedDict()
    for (target, r) in zip(targets, results):
        target_ = str(target)
        retval[target_] = r
    return retval


def _build_global(results):
    countries = list(results.keys())
    if 'Global' in countries:
        countries.remove('Global')

    # Store results_[target][country].
    results_ = collections.OrderedDict()
    for country in countries:
        for (target, val) in results[country].items():
            if target not in results_:
                results_[target] = collections.OrderedDict()
            results_[target][country] = val

    results['Global'] = collections.OrderedDict()
    for (target, v) in results_.items():
        results['Global'][target] = model.global_.Global(v)

    # Put 'Global' first.
    retval = collections.OrderedDict()
    retval['Global'] = results['Global']
    for country in countries:
        retval[country] = results[country]
    return retval


def _run_all(targets = None):
    countries = model.datasheet.get_country_list('all')
    try:
        results = model.results.load_modes()
    except:
        results = collections.OrderedDict()
    updated = False
    for country in countries:
        if country not in results:
            print(country)
            results[country] = _run_one(country, targets = targets)
            updated = True
    if updated:
        results = _build_global(results)
        model.results.dump_modes(results)
    return results


if __name__ == '__main__':
    results = _run_all()
