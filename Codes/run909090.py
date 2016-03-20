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
    simulation = model.Simulation(country, '909090')
    # Need converted country name.
    country_ = simulation.parameters.country
    print('{}'.format(country_))
    return (country_, simulation)


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
