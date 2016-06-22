'''
Estimate the gross transmission rate from incidence and prevalence data.
'''

import numpy
from scipy import stats


def estimate_vs_time(parameters):
    '''
    Estimate the transmission rate at each time.
    '''
    prevalence = parameters.prevalence.interpolate(method = 'index')
    incidence = parameters.incidence.interpolate(method = 'index')
    transmission_rates = incidence / prevalence / (1 - prevalence)
    return transmission_rates


def estimate(parameters):
    '''
    Estimate the transmission rate.
    '''
    transmission_rates_vs_time = estimate_vs_time(parameters)
    X = numpy.log(transmission_rates_vs_time.dropna())
    mu = numpy.mean(X)
    sigma = numpy.std(X, ddof = 1)
    transmission_rate = stats.lognorm(sigma, scale = numpy.exp(mu))
    transmission_rate.mode = numpy.exp(mu - sigma ** 2)
    return transmission_rate


def plot(parameters, ax = None, show = True):
    transmission_rates_vs_time = estimate_vs_time(parameters)
    transmission_rate = estimate(parameters)

    from matplotlib import pyplot
    if ax is None:
        ax = pyplot.gca()
    ax.plot(transmission_rates_vs_time.index,
            transmission_rates_vs_time,
            linestyle = 'None', marker = 'o')
    ax.axhline(transmission_rate.median(), color = 'black',
               linestyle = 'solid')
    for q in [0.25, 0.75]:
        ax.axhline(transmission_rate.ppf(q), color = 'black',
                   linestyle = 'dashed')
    ax.set_ylabel('Transmission rate (per year)')
    ax.set_title(parameters.country)
    if show:
        pyplot.show()
