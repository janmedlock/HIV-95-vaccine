#!/usr/bin/python3
'''
Run simulations with parameter samples.
'''

import model


countries = model.datasheet.get_country_list()
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


def _run_one(country, target):
    print('Running {}, {!s}.'.format(country, target))
    parameter_samples = model.parameters.Samples(country)
    results = model.simulation.MultiSim(parameter_samples, target)
    model.results.dump(results)


def _main():
    for country in countries:
        for target in model.target.all_:
            if not model.results.exists(country, target):
                _run_one(country, target)

    model.multicountry.build_regionals()


if __name__ == '__main__':
    _main()
