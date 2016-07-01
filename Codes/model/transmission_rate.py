'''
Estimate the gross transmission rate from incidence and prevalence data.
'''

import warnings

import numpy
from scipy import stats
import pandas


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
    return transmission_rates_vs_time.dropna()


def estimate(parameters, halflife = 1):
    '''
    Estimate the transmission rate at each time,
    then build a lognormal random variable using exponentially
    weighted statistics from the result.
    '''
    transmission_rates_vs_time = estimate_vs_time(parameters)
    if len(transmission_rates_vs_time) > 0:
        # Assuming transmission_rates_vs_time are lognormal(mu, sigma),
        # mu and sigma are the mean and stdev of
        # log(transmission_rates_vs_time).
        trt_log = transmission_rates_vs_time.apply(numpy.log)
        # Catch pandas 0.18 warnings.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            # Just use last values.
            mu = pandas.ewma(trt_log, halflife = halflife).iloc[-1]
            # The default, bias = False, seems to be ddof = 1.
            sigma = pandas.ewmstd(trt_log, halflife = halflife).iloc[-1]
        # pandas 0.18 syntax.
        # ew = trt_log.ewm(halflife = self.halflife)
        # mu = ew.mean().iloc[-1]
        # The default, bias = False, seems to be ddof = 1.
        # sigma = ew.std().iloc[-1]
        transmission_rate = stats.lognorm(sigma, scale = numpy.exp(mu))
        # scipy RVs don't define .mode (i.e. MLE),
        # so I explicitly add it so I can use it
        # as the point estimate later.
        transmission_rate.mode = numpy.exp(mu - sigma ** 2)
    else:
        transmission_rate = numpy.nan
    return transmission_rate


def set_rates(parameters):
    r'''
    Set the transmission rates in the parameters object.

    The force of infection is

    .. math:: \lambda =
              \frac{\beta_A A + \beta_U (U + D + T) + \beta_V V
              + 0 \cdot W}{N}
              = \frac{\beta I}{N},

    where :math:`\beta` is the estimated aggregate transmission rate and
    :math:`I = A + U + D + T + V + W` is PLHIV.
    Then

    .. math:: \begin{align}
              \beta I
              &= \beta_A A
              + \beta_U (U + D + T)
              + \beta_V V
              + 0 \cdot W \\
              &= \beta_U \left(U + D + T
              + \frac{\beta_A}{\beta_U} A
              + \frac{\beta_V}{\beta_U} V\right),
              \end{align}

    so

    .. math:: \beta_U
              = \frac{\beta I}
              {U + D + T
              + \frac{\beta_A}{\beta_U} A
              + \frac{\beta_V}{\beta_U} V}.
    '''
    assert numpy.isfinite(parameters.transmission_rate)
    assert (parameters.transmission_rate >= 0)

    # From Rakai study (Wawer, Grey, et al).
    n = parameters.coital_acts_per_year
    p = parameters.transmission_per_coital_act_acute
    rakai_acute = 1 - (1 - p) ** n
    p = parameters.transmission_per_coital_act_unsuppressed
    rakai_unsuppressed = 1 - (1 - p) ** n
    p = (parameters.transmission_per_coital_act_reduction_by_suppression
         * parameters.transmission_per_coital_act_unsuppressed)
    rakai_suppressed = 1 - (1 - p) ** n

    relative_rate_suppressed = rakai_suppressed / rakai_unsuppressed
    relative_rate_acute = rakai_acute / rakai_unsuppressed

    S, Q, A, U, D, T, V, W, Z, R = parameters.initial_conditions
    I = A + U + D + T + V + W
    assert (I > 0)

    parameters.transmission_rate_unsuppressed = (
        parameters.transmission_rate * I
        / (U + D + T + relative_rate_acute * A + relative_rate_suppressed * V))
    parameters.transmission_rate_suppressed = (
        relative_rate_suppressed * parameters.transmission_rate_unsuppressed)
    parameters.transmission_rate_acute = (
        relative_rate_acute * parameters.transmission_rate_unsuppressed)
