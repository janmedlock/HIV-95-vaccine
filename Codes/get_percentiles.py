#!/usr/bin/python3
'''
Update the cache of percentiles from the runs with parameter distributions.
'''

import itertools
import warnings

import numpy
import tables

import model


stats_to_save = ['infected', 'incidence', 'prevalence',
                 'incidence_per_capita', 'AIDS', 'dead',
                 'new_infections', 'alive']

CI_levels = ['median', 50, 80, 90, 95, 99]


def _main():
    with model.results.samples.stats.load(mode = 'a') as h5file:
        countries = model.datasheet.get_country_list()
        for (country, target) in itertools.product(countries,
                                                   model.targets.all_):
            target = str(target)
            results_exist = model.results.samples.exists(country, target)
            stats_exist = '/{}/{}'.format(country, target) in h5file
            if results_exist and (not stats_exist):
                print('{}, {}'.format(country, target))
                with model.results.samples.Results(country, target) as results:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            'ignore',
                            category = tables.NaturalNameWarning)
                        # For NaNs.
                        warnings.filterwarnings(
                            'ignore',
                            category = RuntimeWarning)
                        ctgroup = h5file.create_group(
                            '/{}'.format(country),
                            target,
                            createparents = True)
                        for stat in stats_to_save:
                            vals = getattr(results, stat)
                            ctsgroup = h5file.create_group(ctgroup,
                                                           stat)
                            for lev in CI_levels:
                                if lev == 'median':
                                    obj = numpy.median(vals, axis = 0)
                                    name = 'median'
                                else:
                                    obj = numpy.percentile(vals,
                                                           [50 - lev / 2,
                                                            50 + lev / 2],
                                                           axis = 0)
                                    name = 'CI{}'.format(lev)
                                h5file.create_carray(ctsgroup, name,
                                                     obj = obj)


if __name__ == '__main__':
    _main()
