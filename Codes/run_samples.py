#!/usr/bin/python3

import pickle

import numpy

import model


samplesfile = 'samples.pkl'
resultsfile = 'results.pkl'

countries = model.get_country_list()
# Move these to the front.
countries_to_plot = ['United States of America',
                     'South Africa',
                     'Uganda',
                     'Nigeria',
                     'India',
                     'Rwanda']
for c in countries_to_plot:
    countries.remove(c)
countries = countries_to_plot + countries

t_end = 20

target = '909090'

def _run_country(country, samples):
    print('Running {}.'.format(country))

    parameters = model.Parameters(country)

    parametersamples = model.ParameterSample.from_samples(country, samples)

    multisim = model.MultiSim(parametersamples, target)

    return multisim


def _main():
    with open(samplesfile, 'rb') as fd:
        samples = pickle.load(fd)

    print('Loaded {} samples.'.format(len(samples)))

    results = {}
    for country in countries:
        results[country] = _run_country(country, samples)

        with open(resultsfile, 'wb') as fd:
            pickle.dump(results, fd)


if __name__ == '__main__':
    _main()

