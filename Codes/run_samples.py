#!/usr/bin/python3

import pickle

import numpy

import model


samplesfile = 'samples.pkl'
resultsfile = 'results.pkl'

# countries = model.get_country_list()
countries = ('United States of America',
             'South Africa',
             'Rwanda',
             'Uganda',
             'India',
             'Haiti')

t_end = 20

target = '909090'

def _run_country(country, samples):
    parameters = model.Parameters(country)

    parametersamples = model.ParameterSample.from_samples(country, samples)

    multisim = model.MultiSim(parametersamples, target)

    return multisim


def _main():
    with open(samplesfile, 'rb') as fd:
        samples = pickle.load(fd)

    results = {}
    for country in countries:
        results[country] = _run_country(country, samples)

    with open(resultsfile, 'wb') as fd:
        pickle.dump(results, fd)


if __name__ == '__main__':
    _main()

