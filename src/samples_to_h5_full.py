#!/usr/bin/python3
'''
Convert the samples results to full h5 files,
not just for a few selected attrs.
'''

import numbers
import warnings

import numpy
import tables

import model


def _dump(h5file, group, name, obj):
    if isinstance(obj[0], (numbers.Number, numpy.ndarray, numpy.record)):
        out = numpy.asarray(obj)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                                    category = tables.NaturalNameWarning)
            return h5file.create_carray(group, name, obj = out,
                                        createparents = True)
    elif isinstance(obj[0], (model.proportions.Proportions,
                             model.control_rates.ControlRates,
                             model.targets._TargetValues)):
        for key in obj[0].keys():
            if isinstance(obj[0], model.targets._TargetValues):
                # The target values are the same for all simulations
                # so only save one copy.
                out = obj[0][key]
            else:
                out = [o[key] for o in obj]
            _dump(h5file, '{}/{}'.format(group, name), key, out)
        return getattr(h5file.root, group)
    else:
        raise ValueError("Unknown type '{}'!".format(type(obj[0])))


def _main():
    with model.results.samples.h5.open_(mode = 'a') as h5file:
        if '/samples' not in h5file:
            samples = model.samples.load()
            _dump(h5file, '/', 'samples', samples)

        countries = model.datasheet.get_country_list()
        for country in countries:
            for target in model.targets.all_:
                target = str(target)
                results_exist = model.results.samples.exists(country, target)
                stats_exist = '/{}/{}'.format(country, target) in h5file
                if results_exist and (not stats_exist):
                    print('{}, {}'.format(country, target))
                    with model.results.samples.open_(country,
                                                     target) as results:
                        group = '/{}/{}'.format(country, target)
                        for key in results.keys():
                            _dump(h5file, group, key, getattr(results, key))


if __name__ == '__main__':
    _main()
