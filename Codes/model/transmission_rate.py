'''
Estimate the gross transmission rate from incidence and prevalence data.
'''

import numpy
from scipy import stats


def estimate_vs_time(parameters):
    '''
    Estimate the transmission rate at each time.
    The transmission rate at a time is simply
    incidence / prevalence / (1 - prevalence).
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
