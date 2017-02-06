#!/usr/bin/python3
'''
Update the cache of percentiles from the runs with parameter distributions.
'''

import itertools
import warnings

import numpy
import tables

import model


regions_and_countries = model.regions.all_ + model.datasheet.get_country_list()

targets = model.target.all_

_stats_to_dump = ['new_infections', 'infected', 'incidence_per_capita',
                  'AIDS', 'dead']

CI_levels = ['median', 50, 80, 90, 95, 99]


def _main():
    with model.results.samples.stats.open_(mode = 'a') as h5file:
        for (region_or_country, target) in itertools.product(
                regions_and_countries, targets):
            target = str(target)
            results_exist = model.results.samples.exists(region_or_country,
                                                         target)
            stats_exist = '/{}/{}'.format(region_or_country, target) in h5file
            if results_exist and (not stats_exist):
                print('{}, {}'.format(region_or_country, target))
                with model.results.samples.open_(region_or_country,
                                                 target) as results:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            'ignore',
                            category = tables.NaturalNameWarning)
                        # For NaNs.
                        warnings.filterwarnings(
                            'ignore',
                            category = RuntimeWarning)
                        rtgroup = h5file.create_group(
                            '/{}'.format(region_or_country),
                            target,
                            createparents = True)
                        for stat in _stats_to_dump:
                            vals = getattr(results, stat)
                            rtsgroup = h5file.create_group(rtgroup,
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
                                h5file.create_carray(rtsgroup, name,
                                                     obj = obj)


if __name__ == '__main__':
    _main()
