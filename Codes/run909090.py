#!/usr/bin/python3
'''
Run the 90-90-90 policies for all the countries.
'''

import pickle

import joblib

import model


countries = ('United States of America',
             'South Africa',
             'Rwanda',
             'Uganda',
             'India',
             'Haiti')

targets = ('baseline', '909090')

vaccine_levels = (0, 0.5)
vaccine_start_times = (5, 10)


def _helper(country):
    '''
    Helper to build dictionary of results.
    '''
    parameters = model.Parameters(country)
    # Need converted country name.
    country_ = parameters.country

    results = {}
    for t in targets:
        for v in vaccine_levels:
            if v > 0:
                for vt in vaccine_start_times:
                    k = (t, v, vt)
                    results[k] = model.Simulation(country, t,
                                                  vaccine_target = v,
                                                  vaccine_start_time = vt,
                                                  run_baseline = False,
                                                  parameters = parameters)
            else:
                # Don't need to run multiple vaccine_start_times
                # when vaccine_target == 0.
                k = (t, v)
                results[k] = model.Simulation(country, t,
                                              vaccine_target = v,
                                              run_baseline = False,
                                              parameters = parameters)

    print('{}'.format(country_))
    return (country_, results)


def _main(parallel = True):
    if parallel:
        with joblib.Parallel(n_jobs = -1) as p:
            results = p(joblib.delayed(_helper)(country)
                        for country in countries)
    else:
        results = (_helper(country) for country in model.get_country_list())

    pickle.dump(dict(results), open('909090.pkl', 'wb'))


if __name__ == '__main__':
    _main()
