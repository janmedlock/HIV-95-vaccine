'''
Store and retrieve results from simulations with parameter samples.

.. todo:: Use HDF instead of pickle.  HDF can do random access instead
          of reading the whole file, so all the complicated caching
          I'm doing could hopefully be removed.
'''

import collections
import os

from .. import common
from ... import datasheet
from ... import multicountry
from ... import picklefile
from ... import regions


def get_path(country_or_region, target):
    if isinstance(target, type):
        # It's a class.
        target = target()
    if target is not None:
        path = os.path.join(common.resultsdir,
                            country_or_region,
                            '{}.pkl'.format(str(target)))
    else:
        path = os.path.join(common.resultsdir,
                            country_or_region)
    return path


def exists(country_or_region, target):
    resultsfile = get_path(country_or_region, target)
    return os.path.exists(resultsfile)


class Results:
    '''
    Class to load the data on demand.
    '''
    def __init__(self, country_or_region, target):
        self._country_or_region = country_or_region
        # Convert to string in case its an instance.
        self._target = str(target)

        if (not self.exists) and regions.is_country(self._country_or_region):
            raise FileNotFoundError("'{}', '{}' not found!".format(
                self._country_or_region, self._target))
        self._data = None

    def __enter__(self):
        return self

    def __exit__(self, type_, value, tb):
        pass

    def _load_data(self):
        if regions.is_region(self._country_or_region) and (not self.exists):
            print('Building {}, {}...'.format(self._country_or_region,
                                              self._target))
            self._build_regional()
        else:
            print('Loading data for {}, {}...'.format(self._country_or_region,
                                                      self._target))
            self._data = picklefile.load(self.path)
            if regions.is_country(self._country_or_region):
                self.correct_ni()

    def _build_regional(self):
        countries = regions.regions[self._country_or_region]
        # Use an OrderedDict so that the countries' Results._load_data()
        # are called in order later by multicountry.MultiCountry().
        data = collections.OrderedDict()
        for country in sorted(countries):
            try:
                data[country] = open_(country, self._target)
            except FileNotFoundError as err:
                print(err)

        if self._country_or_region == 'Global':
            self._data = multicountry.Global(data)
        else:
            self._data = multicountry.MultiCountry(data)

    def __getattr__(self, key):
        # Don't use ._data for special attrs.
        if key.startswith('__') and key.endswith('__'):
            raise AttributeError
        else:
            if self._data is None:
                self._load_data()
            return getattr(self._data, key)

    def keys(self):
        if self._data is None:
            self._load_data()
        return self._data.keys()

    def flush(self):
        del self._data
        self._data = None

    @property
    def path(self):
        return get_path(self._country_or_region, self._target)

    @property
    def exists(self):
        return exists(self._country_or_region, self._target)

    def correct_ni(self):
        '''
        Correct new infections, incidence, and incidence per capita
        from previous bug.
        '''
        import numpy
        from scipy import integrate

        from ... import parameters
        from ... import samples
        from ... import targets

        target = self._data.targets[0]
        if isinstance(self._data.targets[0], targets.Vaccine):
            country = self._data.country[0]

            samples_ = samples.load()
            nsamples = len(samples_)
            parameters_ = parameters.Sample.from_samples(country, samples_)
            tr_acute = numpy.empty(nsamples)
            tr_unsuppressed = numpy.empty(nsamples)
            tr_suppressed = numpy.empty(nsamples)
            for (i, p) in enumerate(parameters_):
                tr_acute[i] = p.transmission_rate_acute
                tr_unsuppressed[i] = p.transmission_rate_unsuppressed
                tr_suppressed[i] = p.transmission_rate_suppressed

            S = numpy.asarray(self._data.susceptible)
            Q = numpy.asarray(self._data.vaccinated)
            A = numpy.asarray(self._data.acute)
            U = numpy.asarray(self._data.undiagnosed)
            D = numpy.asarray(self._data.diagnosed)
            T = numpy.asarray(self._data.treated)
            V = numpy.asarray(self._data.viral_suppression)
            W = numpy.asarray(self._data.AIDS)
            N = S + Q + A + U + D + T + V

            force_of_infection = (
                tr_acute[:, numpy.newaxis] * A
                + tr_unsuppressed[:, numpy.newaxis] * (U + D + T)
                + tr_suppressed[:, numpy.newaxis] * V) / N

            dni = (force_of_infection * S
                   + (1 - target.vaccine_efficacy) * force_of_infection * Q)

            t = numpy.linspace(2015, 2035, 2401)
            self._data.new_infections = integrate.cumtrapz(dni, t, initial = 0)
            incidence = numpy.diff(self._data.new_infections) / numpy.diff(t)
            # Put NaNs in the first column to make it align with t.
            pad = numpy.nan * numpy.ones((nsamples, 1))
            self._data.incidence = numpy.hstack((pad, incidence))
            self._data.incidence_per_capita = (
                self._data.incidence / numpy.asarray(self._data.alive))
            print('Corrected new infections, incidence, incidence per capita.')


def open_(country_or_region, target):
    return Results(country_or_region, target)


def dump(country_or_region, target, results):
    resultsfile = get_path(country_or_region, target)
    resultsdir = os.path.dirname(resultsfile)
    if not os.path.exists(resultsdir):
        os.mkdir(resultsdir)
    picklefile.dump(results, resultsfile)
