#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
run simulations.
'''

import joblib

import model


def _run_one(country, target):
    print('Running {}, {!s}.'.format(country, target))
    parameters = model.parameters.Parameters(country).mode()
    results = model.simulation.Simulation(parameters, target)
    model.results.dump(results)


def _main(targets = None):
    joblib.Parallel(n_jobs = -1)(
        joblib.delayed(_run_one)(country, target)
        for country in model.datasheet.get_country_list()
        for target in model.target.all_
        if not model.results.exists(country, target, 'mode'))

    model.multicountry.build_regionals(parameters_type = 'mode')


if __name__ == '__main__':
    _main()
