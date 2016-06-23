#!/usr/bin/python3
'''
Test the estimation of transmission rates.
'''

import sys

import numpy
import pandas
from scipy import stats

sys.path.append('..')
import model


def estimate_vs_time(country):
    r'''
    Estimate the transmission rate at each time.

    The per-capita incidence is

    .. math:: i(t) = \lambda(t) \frac{S(t)}{N(t)}
              = \beta \frac{I(t)}{N(t)} \frac{S(t)}{N(t)},

    assuming no differences in transmission between acute, unsuppressed,
    suppressed and AIDS classes (i.e. :math:`I = A + U + D + V + W`).

    If :math:`p = \frac{I}{N}` is the prevalence,

    .. math:: i(t) = \beta p(t) (1 - p(t)).

    Rearranging gives

    .. math:: \beta(t) = \frac{i(t)}{p(t) (1 - p(t))}.
    '''
    # Read the parameters, incidence, prevalence, etc from the datasheet.
    parameters = model.Parameters(country)

    # Interpolate in case of any missing data.
    prevalence = parameters.prevalence.interpolate(method = 'index')
    incidence = parameters.incidence.interpolate(method = 'index')

    transmission_rates_vs_time = incidence / prevalence / (1 - prevalence)

    # Remove nan entries.
    transmission_rates_vs_time.dropna(inplace = True)

    return transmission_rates_vs_time


def estimate_geometric_mean(country):
    '''
    Estimate the transmission rate at each time,
    then take the geometric mean over time.
    '''
    transmission_rates_vs_time = estimate_vs_time(country)

    return stats.gmean(transmission_rates_vs_time)


def estimate_lognormal(country):
    '''
    Estimate the transmission rate at each time,
    then build a lognormal random variable using statistics
    from the result.
    '''
    transmission_rates_vs_time = estimate_vs_time(country)

    gmean = stats.gmean(transmission_rates_vs_time)
    sigma = numpy.std(numpy.log(transmission_rates_vs_time), ddof = 1)

    # Note that the median of this lognormal RV is gmean.
    transmission_rates = stats.lognorm(sigma, scale = gmean)

    # scipy RVs don't define .mode (i.e. MLE),
    # so I explicitly add it so I can use it
    # as the point estimate later.
    transmission_rates.mode = gmean * numpy.exp(- sigma ** 2)

    return transmission_rates


def estimate_least_squares(country):
    r'''
    Estimate the transmission rates.

    The per-capita incidence is

    .. math:: i(t) = \lambda(t) \frac{S(t)}{N(t)}
              = \frac{\beta_U (U(t) + D(t)) + \beta_V V(t)}{N(t)}
              \frac{S(t)}{N(t)},

    assuming that acute transmission has only a small effect
    (:math:`\beta_A A(t) \ll \beta_U (U(t) + D(t))` and
    :math:`\beta_A A(t) \ll \beta_V V(t)`),
    that there are few treated people without viral suppression
    (:math:`T(t) \approx 0`), and that the AIDS class is small
    (:math:`W(t) \approx 0`).

    If :math:`p = \frac{U + D + V}{N}` is the prevalence and
    :math:`c = \frac{V}{U + D + V}` is the drug coverage,

    .. math:: i(t) = [\beta_U (1 - c(t)) + \beta_V c(t)] p(t) (1 - p(t)).

    Rearranging gives the least-squares problem

    .. math:: [(1 - c(t)) \beta_U + c(t) \beta_V]
              = \frac{i(t)}{p(t) (1 - p(t))},

    or

    .. math:: \mathbf{A} \mathbf{\beta} = \mathbf{b},

    with

    .. math:: \mathbf{A} =
              \begin{bmatrix}
              \vdots & \vdots \\
              1 - c(t) & c(t) \\
              \vdots & \vdots
              \end{bmatrix},

    .. math:: \mathbf{b} =
              \begin{bmatrix}
              \vdots \\
              \frac{i(t)}{p(t) (1 - p(t))} \\
              \vdots
              \end{bmatrix},

    and

    .. math:: \mathbf{\beta} =
              \begin{bmatrix}
              \beta_U \\ \beta_V
              \end{bmatrix}.
    '''
    # Read the parameters, incidence, prevalence, etc from the datasheet.
    parameters = model.Parameters(country)

    # Interpolate in case of any missing data.
    prevalence = parameters.prevalence.interpolate(method = 'index')
    incidence = parameters.incidence.interpolate(method = 'index')
    drug_coverage = parameters.drug_coverage.interpolate(method = 'index')

    # Set up A matrix and b vector.
    A = pandas.DataFrame([1 - drug_coverage, drug_coverage],
                         index = ('unsuppressed', 'suppressed')).T
    b = incidence / prevalence / (1 - prevalence)

    # Align them to the same years.
    A, b = A.align(b, axis = 0)

    # Drop years where there's missing data in either A or b.
    goodrows = A.notnull().all(axis = 1) & b.notnull()
    A = A[goodrows]
    b = b[goodrows]

    if len(A) > 0:
        betas, _, _, _ = numpy.linalg.lstsq(A, b)
    else:
        # No years with all data!
        betas = numpy.nan * numpy.ones(2)
    return pandas.Series(betas, index = A.columns)


def get_all(estimator):
    '''
    Use `estimator` to get the transmission rate for all countries.
    '''
    countries = model.get_country_list('IncidencePrevalence')
    transmission_rates = {}
    for country in countries:
        print('Estimating transmission rate for {}'.format(country))
        transmission_rates[country] = estimator(country)

    # Put the data in the right kind of pandas data structure.
    ndim = numpy.ndim(list(transmission_rates.values()))
    if ndim == 1:
        return pandas.Series(transmission_rates)
    elif ndim == 2:
        return pandas.DataFrame(transmission_rates).T
    else:
        # What else to do?
        # Maybe use pandas.Panel() if ndim == 3.
        return transmission_rates


if __name__ == '__main__':
    country = 'South Africa'
    print(country)
    transmission_rates = estimate_geometric_mean(country)
    # transmission_rates = estimate_lognormal(country)
    # transmission_rates = estimate_least_squares(country)
    print(transmission_rates)

    # transmission_rates = get_all(estimate_geometric_mean)
    # print(transmission_rates)
