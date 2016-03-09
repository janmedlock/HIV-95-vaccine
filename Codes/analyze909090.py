#!/usr/bin/python3
'''
Analyze the 90-90-90 policies for all the countries.

See :func:`model.analyze909090.analyze909090`.
'''

import pickle

import joblib

import model


def _main():
    results = {}
    with joblib.Parallel(n_jobs = -1) as parallel:
        results = parallel(
            joblib.delayed(model.analyze909090)(country)
            for country in model.get_country_list())

    results = {country: v for (country, v) in results}

    pickle.dump(results, open('analyze909090.pkl', 'wb'))


if __name__ == '__main__':
    _main()
