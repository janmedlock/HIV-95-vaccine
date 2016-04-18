'''
Parameter data.
'''

import copy
import pickle

import numpy
import pandas
from scipy import stats

from . import datasheet
from . import latin_hypercube_sampling
from . import R0


samplesfile = 'samples.pkl'


def triangular(mode, minimum, maximum):
    shape = (mode - minimum) / (maximum - minimum)
    loc = minimum
    scale = maximum - minimum
    return stats.triang(shape, loc, scale)


def uniform(minimum, maximum):
    loc = minimum
    scale = maximum - minimum
    return stats.uniform(loc, scale)


class Parameters:
    r'''
    Convert parameter data in datafile into object for use in simulations.
    '''

    # Hollingsworth et al, 2008.
    # 2.9 month duration of acute stage.
    progression_rate_acute = triangular(12 / 2.9, 2, 9.6)
    
    # From Morgan et al, 2002.
    # 9.4 years until AIDS untreated.
    progression_rate_unsuppressed = 1 / 9.4

    # From Cirroe et al, 2009.
    suppression_rate = uniform(0.5, 1.5)
    
    # From Morgan et al, 2002.
    # 2 years until death.
    death_rate_AIDS = 1 / 2

    # From Samji et al, 2013 & UNAIDS, 2014.
    death_years_lost_by_supression = uniform(5, 8)

    # From Wawer et al, 2005.
    transmission_per_coital_act_acute = triangular(0.0082, 0.0039, 0.0150)

    # From Hughes et al, 2012.
    # Geometric mean of male_to_female and female_to_male rates.
    _mode = stats.gmean((0.0019, 0.0010))
    _minimum = stats.gmean((0.0010, 0.00060))
    _maximum = stats.gmean((0.0037, 0.0017))
    transmission_per_coital_act_unsuppressed = triangular(_mode,
                                                          _minimum,
                                                          _maximum)

    # From Donnell et al, 2010.
    transmission_per_coital_act_reduction_by_suppression = triangular(0.08,
                                                                      0.002,
                                                                      0.57)

    # From Wawer et al, 2005.
    # 9ish per month.
    coital_acts_per_year = uniform(8 * 12, 9 * 12)

    def __init__(self, country):
        self.country = country

        data = datasheet.CountryData(country)
        # Import attributes from cd into self.
        for k in dir(data):
            a = getattr(data, k)
            if ((not k.startswith('_')) and (not callable(a))):
                setattr(self, k, getattr(data, k))

    def sample(self, nsamples = 1):
        if nsamples == 1:
            return ParameterSample(self)
        else:
            return [ParameterSample(self) for i in range(nsamples)]

    @classmethod
    def generate_samples(cls, nsamples):
        rvs = []
        for k in dir(cls):
            if not k.startswith('_'):
                a = getattr(cls, k)
                if hasattr(a, 'rvs'):
                    rvs.append(a)
        return latin_hypercube_sampling.lhs(rvs, nsamples)

    def __repr__(self):
        cls = self.__class__
        retval = '<{}.{}: country = {}\n'.format(cls.__module__,
                                                 cls.__name__,
                                                 self.country)
        retval += '\n'.join('{} = {}'.format(k, getattr(self, k))
                            for k in dir(self)
                            if ((k != 'country')
                                and (not k.startswith('_'))
                                and (not callable(getattr(self, k)))))
        retval += '>'
        return retval


class ParameterSample:
    def __init__(self, parameters, values = None):
        self.country = parameters.country

        if values is not None:
            values = list(values)

        # Import attributes from parameters into self,
        # but sample rvs.
        for k in dir(parameters):
            if not k.startswith('_'):
                a = getattr(parameters, k)
                if not callable(a):
                    if hasattr(a, 'rvs'):
                        if values is None:
                            setattr(self, k, a.rvs())
                        else:
                            setattr(self, k, values.pop(0))
                    else:
                        setattr(self, k, a)

        self.calculate_secondary_parameters()
        self.update_initial_conditions()

    @classmethod
    def from_samples(cls, country, samples):
        parameters = Parameters(country)
        for s in samples:
            yield cls(parameters, s)


    def calculate_secondary_parameters(self):
        life_span = 1 / self.death_rate
        time_with_AIDS = 1 / self.death_rate_AIDS
        time_in_suppression = (life_span
                               - self.death_years_lost_by_supression
                               - time_with_AIDS)
        self.progression_rate_suppressed = (1 / time_in_suppression
                                            - self.death_rate)

        self.transmission_rate_acute = (
            1 -
            (1 - self.transmission_per_coital_act_acute)
            ** self.coital_acts_per_year)

        self.transmission_rate_unsuppressed = (
            1 -
            (1 - self.transmission_per_coital_act_unsuppressed)
            ** self.coital_acts_per_year)

        self.transmission_rate_suppressed = (
            1 -
            (1 -
             self.transmission_per_coital_act_reduction_by_suppression
             * self.transmission_per_coital_act_unsuppressed)
            ** self.coital_acts_per_year)

        self.vaccine_efficacy = 0.5

        # One-time cost of new diagnosis.
        self.cost_of_testing_onetime_increasing = self.cost_test

        # One-time cost of new treatment.
        self.cost_of_treatment_onetime_constant = (self.cost_CD4
                                                   + self.cost_viral_load)

        ###############################################
        # Note: No cost for the nonadherence control! #
        ###############################################
        # Recurring cost of nonadherence.
        self.cost_nonadherence_recurring_increasing = 0

        # Recurring cost of treatment.
        # Treatment is ART + 1 viral load test per year
        # + 2 CD4 tests per year.
        self.cost_treatment_recurring_increasing = (self.cost_ART_annual
                                                    + self.cost_viral_load
                                                    + 2 * self.cost_CD4)

        # Recurring cost of AIDS.
        #
        # This is calculated as the annual cost of living with AIDS
        # (cost_AIDS_annual) plus the cost of AIDS death
        # (cost_AIDS_death * death_rate_AIDS).
        self.cost_AIDS_recurring_constant = (self.cost_AIDS_annual
                                             + (self.death_rate_AIDS
                                                * self.cost_AIDS_death))

        # Disability weights, assuming 1 year in symptomatic phase.
        years_in_symptomatic = 1
        disability_D = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.038)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.274))
        disability_T = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.078)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.314))
        disability_V = (
            ((1 - years_in_symptomatic * self.progression_rate_suppressed)
             * 0.039)
            + (years_in_symptomatic * self.progression_rate_suppressed
               * 0.157))

        # Entries are states S, Q, A, U, D, T, V, W, Z,
        # but not R.
        disability = numpy.array((0,            # S
                                  0,            # Q
                                  0.16,         # A
                                  0.038,        # U
                                  disability_D, # D
                                  disability_T, # T
                                  disability_V, # V
                                  0.582,        # W
                                  1))           # Z

        self.QALY_rates_per_person = 1 - disability

        self.DALY_rates_per_person = disability

    def update_initial_conditions(self):
        # Take AIDS people out of D only.
        proportionAIDS = (1 / (1
                               + self.death_rate_AIDS
                               / self.progression_rate_unsuppressed))
        newAIDS = proportionAIDS * self.initial_conditions['D']
        self.initial_conditions['W'] = newAIDS
        self.initial_conditions['D'] -= newAIDS

        # Vaccinated.
        self.initial_conditions['Q'] = 0

        # Add people dead from AIDS.
        self.initial_conditions['Z'] = 0
        # Add new infections.
        self.initial_conditions['R'] = 0

        # Order correctly.
        self.initial_conditions = self.initial_conditions.reindex(
            ('S', 'Q', 'A', 'U', 'D',
             'T', 'V', 'W', 'Z', 'R'))

        # Now convert to numpy object for speed.
        self.initial_conditions = self.initial_conditions.values

    @property
    def R0(self):
        try:
            return R0.R0(self)
        except AttributeError:
            return None

    def __repr__(self):
        cls = self.__class__
        retval = '<{}.{}: country = {}\n'.format(cls.__module__,
                                                 cls.__name__,
                                                 self.country)
        retval += '\n'.join('{} = {}'.format(k, getattr(self, k))
                            for k in dir(self)
                            if ((k != 'country')
                                and (not k.startswith('_'))
                                and (not callable(getattr(self, k)))))
        retval += '>'
        return retval
