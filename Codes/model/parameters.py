'''
Parameter data.
'''

import numpy
import pandas
from scipy import stats
from scipy import optimize

from . import datasheet
from . import latin_hypercube_sampling
from . import R0
from . import transmission_rate


def uniform(minimum, maximum):
    loc = minimum
    scale = maximum - minimum
    retval = stats.uniform(loc, scale)
    retval.mode = (minimum + maximum) / 2
    retval.min = minimum
    retval.max = maximum
    return retval


def triangular(mode, minimum, maximum):
    shape = (mode - minimum) / (maximum - minimum)
    loc = minimum
    scale = maximum - minimum
    retval = stats.triang(shape, loc, scale)
    retval.mode = mode
    retval.min = minimum
    retval.max = maximum
    return retval


def beta(mode, minimum, maximum, lambda_ = 4):
    mu = (minimum + maximum + lambda_ * mode) / (lambda_ + 2)
    v = ((mu - minimum) * (2 * mode - minimum - maximum)
         / (mode - mu) / (maximum - minimum))
    w = v * (maximum - mu) / (mu - minimum)
    loc = minimum
    scale = maximum - minimum
    retval = stats.beta(v, w, loc, scale)
    retval.mode = mode
    retval.min = minimum
    retval.max = maximum
    return retval


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
    death_years_lost_by_suppression = uniform(5, 8)

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
    transmission_per_coital_act_reduction_by_suppression = beta(0.08,
                                                                0.002,
                                                                0.57)

    # Quantile used to get sample from estimated transmission_rate.
    transmission_rate_quantile = uniform(0, 1)

    # From Wawer et al, 2005.
    # 9ish per month.
    coital_acts_per_year = uniform(8 * 12, 9 * 12)

    vaccine_efficacy = 0.5

    def __init__(self, country):
        self.country = country

        data = datasheet.country_data[country]
        # Import attributes from cd into self.
        for k in dir(data):
            a = getattr(data, k)
            if ((not k.startswith('_')) and (not callable(a))):
                setattr(self, k, getattr(data, k))

        # AIDS.  Will be updated later.
        self.initial_conditions['W'] = 0

        # Vaccinated.
        self.initial_conditions['Q'] = 0

        # Deaths from AIDS.
        self.initial_conditions['Z'] = 0
        # New infections.
        self.initial_conditions['R'] = 0

        # Order correctly and convert to float.
        self.initial_conditions = self.initial_conditions.reindex(
            ('S', 'Q', 'A', 'U', 'D',
             'T', 'V', 'W', 'Z', 'R')).astype(float)

    def sample(self, nsamples = 1):
        if nsamples == 1:
            return ParameterSample(self)
        else:
            return [ParameterSample(self) for i in range(nsamples)]

    def mode(self):
        return ParameterMode(self)

    @classmethod
    def generate_samples(cls, nsamples):
        rvs = []
        for k in dir(cls):
            if not k.startswith('_'):
                a = getattr(cls, k)
                if hasattr(a, 'rvs'):
                    rvs.append(a)
        return latin_hypercube_sampling.lhs(rvs, nsamples)

    @classmethod
    def get_rv_names(cls):
        rvs = []
        for k in dir(cls):
            if not k.startswith('_'):
                a = getattr(cls, k)
                if hasattr(a, 'rvs'):
                    rvs.append(k)
        return rvs

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


class _ParameterSuper:
    def __init__(self, parameters):
        self.country = parameters.country

        self.calculate_secondary_parameters()
        self.update_initial_conditions()

    def calculate_secondary_parameters(self):
        life_span = 1 / self.death_rate
        time_with_AIDS = 1 / self.death_rate_AIDS
        time_in_suppression = (life_span
                               - self.death_years_lost_by_suppression
                               - time_with_AIDS)
        self.progression_rate_suppressed = (1 / time_in_suppression
                                            - self.death_rate)

        # Random variable.
        transmission_rate_rv = transmission_rate.estimate(self)
        # Sample using the quantile.
        self.transmission_rate = transmission_rate_rv.ppf(
            self.transmission_rate_quantile)
        transmission_rate.set_rates(self)

        # One-time cost of new diagnosis.
        # self.cost_of_testing_onetime_increasing = self.cost_test

        # One-time cost of new treatment.
        # self.cost_of_treatment_onetime_constant = (self.cost_CD4
        #                                            + self.cost_viral_load)

        ###############################################
        # Note: No cost for the nonadherence control! #
        ###############################################
        # Recurring cost of nonadherence.
        # self.cost_nonadherence_recurring_increasing = 0

        # Recurring cost of treatment.
        # Treatment is ART + 1 viral load test per year
        # + 2 CD4 tests per year.
        # self.cost_treatment_recurring_increasing = (self.cost_ART_annual
        #                                             + self.cost_viral_load
        #                                             + 2 * self.cost_CD4)

        # Recurring cost of AIDS.
        #
        # This is calculated as the annual cost of living with AIDS
        # (cost_AIDS_annual) plus the cost of AIDS death
        # (cost_AIDS_death * death_rate_AIDS).
        # self.cost_AIDS_recurring_constant = (self.cost_AIDS_annual
        #                                      + (self.death_rate_AIDS
        #                                         * self.cost_AIDS_death))

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

        ics = self.initial_conditions.copy()
        newAIDS = proportionAIDS * ics['D']
        ics['W'] = newAIDS
        ics['D'] -= newAIDS

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


class ParameterSample(_ParameterSuper):
    def __init__(self, parameters, values = None):
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

        super().__init__(parameters)

    @classmethod
    def from_samples(cls, country, samples):
        parameters = Parameters(country)
        for s in samples:
            yield cls(parameters, s)


class ParameterMode(_ParameterSuper):
    def __init__(self, parameters):
        # Import attributes from parameters into self,
        # but use mode of rvs.
        for k in dir(parameters):
            if not k.startswith('_'):
                a = getattr(parameters, k)
                if not callable(a):
                    if isinstance(a, (stats.distributions.rv_continuous,
                                      stats.distributions.rv_discrete,
                                      stats.distributions.rv_frozen)):
                        setattr(self, k, self.mode(a))
                    else:
                        setattr(self, k, a)

        super().__init__(parameters)

    @staticmethod
    def mode(D, _force_compute = False):
        if hasattr(D, 'mode') and not _force_compute:
            return D.mode
        else:
            def f(x):
                return - D.logpdf(x)
            x0 = D.mean()
            if numpy.isscalar(x0):
                res = optimize.minimize_scalar(f,
                                               method = 'Brent',
                                               options = dict(maxiter = 10000,
                                                              xtol = 1e-12))
                if not res.success:
                    raise RuntimeError('Optimizer failed to find mode.')
                return res.x
            else:
                res = optimize.minimize(f, D.mean())
                if not res.success:
                    raise RuntimeError('Optimizer failed to find mode.')
                return numpy.squeeze(res.x)

    @classmethod
    def from_country(cls, country):
        parameters = Parameters(country)
        return cls(parameters)
