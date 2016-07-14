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
        retval[str(target)] = r
    return retval


def _run_all(targets = None):
    countries = model.datasheet.get_country_list()
    results = collections.OrderedDict()
    for country in countries:
        print(country)
        results[country] = _run_one(country, targets = targets)
    model.results.dump_modes(results)
    return results


if __name__ == '__main__':
    results = _run_all()
