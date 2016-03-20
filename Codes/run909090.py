#!/usr/bin/python3
'''
Run the 90-90-90 policies for all the countries.
'''

import pickle

import joblib

import model


def _helper(country):
    '''
    Helper to build dictionary of results.
    '''
    parameters = model.Parameters(country)
    # Need converted country name.
    country_ = parameters.country

    results = {}
    for k in ('baseline', 'baseline+50-5', 'baseline+50-10',
              '909090', '909090+50-5', '909090+50-10'):
        results[k] = model.Simulation(country, k,
                                      run_baseline = False,
                                      parameters = parameters)

    print('{}'.format(country_))
    return (country_, results)


def _main(parallel = True):
    if parallel:
        with joblib.Parallel(n_jobs = -1) as p:
            results = p(joblib.delayed(_helper)(country)
                        for country in model.get_country_list())
    else:
        results = (_helper(country) for country in model.get_country_list())

    pickle.dump(dict(results), open('909090.pkl', 'wb'))


if __name__ == '__main__':
    _main()
