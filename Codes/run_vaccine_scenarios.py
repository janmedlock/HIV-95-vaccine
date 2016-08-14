#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
run simulations for the different vaccine sensitivity scenarios.

.. todo:: Update to use hdf5 well and save Simulation.keys().
'''

import joblib
import tables

import model


stats_to_save = ['infected', 'incidence', 'prevalence',
                 'incidence_per_capita', 'AIDS', 'dead',
                 'new_infections', 'alive']


def _run_one(country, targets = None):
    if targets is None:
        targets = model.targets.vaccine_scenarios
    parameters = model.parameters.Parameters(country)
    parameter_values = parameters.mode()
    results = joblib.Parallel(n_jobs = -1)(
        joblib.delayed(model.simulation.Simulation)(parameter_values,
                                                    target)
        for target in targets)
    retval = model.results.modes.ResultsCountry()
    for (target, r) in zip(targets, results):
        target_ = str(target)
        retval[target_] = r
    return retval


def _build_regionals(results, targets = None):
    if targets is None:
        targets = model.targets.vaccine_scenarios

    countries = list(results.keys())
    for region in model.regions.all_:
        if region in countries:
            countries.remove(region)

    for target in targets:
        val = {country: results[country][str(target)] for country in countries}
        for region in model.regions.all_:
            if region == 'Global':
                mc = model.multicountry.Global(val)
            else:
                val_ = {c: val[c] for c in val.keys()
                        if c in model.regions.regions[region]}
                mc = model.multicountry.MultiCountry(val_)
            results.dump(mc, region, target)


def _run_all(targets = None):
    countries = model.datasheet.get_country_list()
    results = model.results.modes.open_vaccine_scenarios(mode = 'a')
    for country in countries:
        if country not in results:
            print(country)
            results[country] = _run_one(country, targets = targets)
    _build_regionals(results, targets = targets)
    return results


if __name__ == '__main__':
    results = _run_all()
