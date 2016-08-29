#!/usr/bin/python3
'''
Build a patch for samples.h5.
'''

import itertools
import numbers
import warnings

import numpy
import tables

import model


_stats_to_dump = ['new_infections', 'infected', 'incidence_per_capita',
                  'AIDS', 'dead']

patchfile = 'samples_patch.h5'


def _main():
    filters = tables.Filters(complevel = 4,
                             complib = 'zlib',
                             shuffle = True,
                             fletcher32 = True)
    samples = model.results.samples.open_()
    patch = tables.open_file(patchfile, mode = 'w', filters = filters)

    countries = model.regions.all_ + model.get_country_list()
    for (country, target) in itertools.product(countries, model.targets.all_):
        target = str(target)
        group = '/{}/{}'.format(country, target)

        with model.results.samples.open_(country, target) as results, \
             warnings.catch_warnings():

            warnings.filterwarnings('ignore',
                                    category = tables.NaturalNameWarning)

            for stat in _stats_to_dump:
                arr_new = getattr(results, stat)
                try:
                    arr_old = samples.get_node(group, stat)
                except tables.NoSuchNodeError:
                    msg = '{} not in samples.h5: adding to patch.'
                    needs_update = True
                else:
                    # Compare but handle NaNs correctly.
                    if (numpy.ma.masked_invalid(arr_new)
                        != numpy.ma.masked_invalid(arr_old)).any():
                        msg = '{} out of date in samples.h5: adding to patch.'
                        needs_update = True
                    else:
                        msg = '{} up to date in samples.h5.'
                        needs_update = False

                print(msg.format(node))
                if needs_update:
                    patch.create_carray(group, stat,
                                        obj = numpy.asarray(arr_new),
                                        createparents = True)

    samples.close()
    patch.close()


if __name__ == '__main__':
    _main()
