#!/usr/bin/python3
'''
Run simulations with parameter samples.
'''

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


def _run_country(country, target, samples):
    print('Running {}, {!s}.'.format(country, target))

    parametersamples = model.parameters.Sample.from_samples(country,
                                                            samples)

    multisim = model.multisim.MultiSim(parametersamples, target)

    return multisim


def _main():
    samples = model.samples.load()

    for country in countries:
        for target in model.targets.all_:
            if not model.results.samples.exists(country, target):
                results = _run_country(country, target, samples)
                model.results.samples.dump(country, target, results)


if __name__ == '__main__':
    _main()
