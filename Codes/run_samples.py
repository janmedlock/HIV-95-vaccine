#!/usr/bin/python3

import os.path
import pickle

import numpy

import model


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
    samples = model.samples.load()

    for country in countries:
        if not model.results.exists(country):
            results = _run_country(country, samples)
            model.results.dump(country, results)


if __name__ == '__main__':
    _main()
