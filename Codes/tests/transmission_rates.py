#!/usr/bin/python3
'''
Test the estimation of transmission rates.
'''

import sys
import warnings

from matplotlib import pyplot
import numpy
import pandas
from scipy import stats

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

sys.path.append('..')
import model


def estimate_vs_time(parameters):
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
    # Interpolate in case of any missing data.
    prevalence = parameters.prevalence.interpolate(method = 'index')
    incidence = parameters.incidence.interpolate(method = 'index')

    transmission_rates_vs_time = incidence / prevalence / (1 - prevalence)

    # Remove nan entries.
    transmission_rates_vs_time.dropna(inplace = True)

    return transmission_rates_vs_time


def estimate_geometric_mean(parameters):
    '''
    Estimate the transmission rate at each time,
    then take the geometric mean over time.
    '''
    transmission_rates_vs_time = estimate_vs_time(parameters)

    return stats.gmean(transmission_rates_vs_time)


def estimate_lognormal(parameters):
    '''
    Estimate the transmission rate at each time,
    then build a lognormal random variable using statistics
    from the result.
    '''
    transmission_rates_vs_time = estimate_vs_time(parameters)

    gmean = stats.gmean(transmission_rates_vs_time)
    sigma = numpy.std(numpy.log(transmission_rates_vs_time), ddof = 1)

    # Note that the median of this lognormal RV is gmean.
    transmission_rates = stats.lognorm(sigma, scale = gmean)

    # scipy RVs don't define .mode (i.e. MLE),
    # so I explicitly add it so I can use it
    # as the point estimate later.
    transmission_rates.mode = gmean * numpy.exp(- sigma ** 2)

    return transmission_rates


def estimate_least_squares(parameters):
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
        parameters = model.Parameters(country)
        transmission_rates[country] = estimator(parameters)

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


def plot_vs_time(parameters,
                 label = 'estimates at each time',
                 marker = '.', markersize = 10,
                 legend = True,
                 *args, **kwargs):
    '''
    Get and plot the estimates of transmission rates vs time.
    '''
    transmission_rates_vs_time = estimate_vs_time(parameters)
    pyplot.plot(transmission_rates_vs_time.index,
                transmission_rates_vs_time,
                label = label,
                marker = marker, markersize = markersize,
                *args,
                **kwargs)

    pyplot.ylabel('Transmission rate (per year)')
    pyplot.title(parameters.country)
    if legend:
        pyplot.legend(loc = 'upper right', frameon = False)


def plot_geometric_mean(parameters):
    '''
    Plot the geometric-mean estimate of the transmision rate.
    '''
    plot_vs_time(parameters, legend = False)

    transmission_rates = estimate_geometric_mean(parameters)
    # Get next line properties (color, etc.).
    props = next(pyplot.gca()._get_lines.prop_cycler)
    pyplot.axhline(transmission_rates,
                   label = 'geometric mean',
                   **props)

    pyplot.legend(loc = 'upper right', frameon = False)


def plot_lognormal(parameters):
    '''
    Plot the lognormal estimate of the transmision rate.
    '''
    plot_vs_time(parameters, legend = False)

    transmission_rates = estimate_lognormal(parameters)
    # Get next line properties (color, etc.).
    props = next(pyplot.gca()._get_lines.prop_cycler)
    # We're going to vary linestyle for the different quantiles,
    # so remove linestyle from props, if it's there.
    props.pop('linestyle', None)
    pyplot.axhline(transmission_rates.median(),
                   label = 'lognormal median (= geometric mean)',
                   **props)
    for (i, q) in enumerate([0.25, 0.75]):
        pyplot.axhline(
            transmission_rates.ppf(q),
            label = 'lognormal inner 75%tile' if i == 0 else None,
            linestyle = 'dashed',
            **props)
    for (i, q) in enumerate([0.05, 0.95]):
        pyplot.axhline(
            transmission_rates.ppf(q),
            label = 'lognormal inner 90%tile' if i == 0 else None,
            linestyle = 'dotted',
            **props)

    pyplot.legend(loc = 'upper right', frameon = False)


if __name__ == '__main__':
    country = 'South Africa'
    print(country)
    # Read the incidence, prevalence, population, etc from the datasheet.
    parameters = model.Parameters(country)
    # transmission_rates = estimate_geometric_mean(parameters)
    # transmission_rates = estimate_lognormal(parameters)
    # transmission_rates = estimate_least_squares(parameters)
    # print(transmission_rates)
    # plot_geometric_mean(parameters)
    plot_lognormal(parameters)

    # transmission_rates = get_all(estimate_geometric_mean)
    # print(transmission_rates)

    pyplot.show()
