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


# targets = [model.Targets959595()] + model.AllVaccineTargets
targets = [model.Targets959595(), model.TargetsVaccine()]


def _run_country(country, target, samples):
    print('Running {}, {!s}.'.format(country, target))

    parameters = model.Parameters(country)

    parametersamples = model.ParameterSample.from_samples(country, samples)

    multisim = model.MultiSim(parametersamples, target)

    return multisim


def _main():
    samples = model.samples.load()

    for country in countries:
        for target in targets:
            if not model.results.exists(country, target):
                results = _run_country(country, target, samples)
                model.results.dump(country, target, results)


if __name__ == '__main__':
    _main()
