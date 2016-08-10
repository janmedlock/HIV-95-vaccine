#!/usr/bin/python3
'''
Build samples.h5.
'''

import numbers
import warnings

import numpy
import tables

import model


_stats_to_dump = ['new_infections', 'infected', 'incidence_per_capita',
                  'AIDS', 'dead']

def _main():
    filters = tables.Filters(complevel = 4,
                             complib = 'zlib',
                             shuffle = True,
                             fletcher32 = True)
    with tables.open_file('results/samples.h5',
                          mode = 'a',
                          filters = filters) as h5file:
        countries = model.regions.all_ + model.datasheet.get_country_list()
        for country in countries:
            for target in model.targets.all_:
                target = str(target)
                group = '/{}/{}'.format(country, target)
                stats_exist = group in h5file
                if not stats_exist:
                    print('{}, {}'.format(country, target))
                    with model.results.samples.open_(country,
                                                     target) as results:
                        for stat in _stats_to_dump:
                            out = getattr(results, stat)
                            with warnings.catch_warnings():
                                warnings.filterwarnings(
                                    'ignore',
                                    category = tables.NaturalNameWarning)
                                h5file.create_carray(group, stat,
                                                     obj = numpy.asarray(out),
                                                     createparents = True)


if __name__ == '__main__':
    _main()
