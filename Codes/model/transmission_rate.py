'''
Estimate the gross transmission rate from incidence and prevalence data.
'''

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
    transmission_rate = stats.gmean(transmission_rate_vs_t.dropna())
    return transmission_rate


def plot(parameters, ax = None, show = True):
    transmission_rates_vs_time = estimate_vs_time(parameters)
    transmission_rate = estimate(parameters)

    from matplotlib import pyplot
    if ax is None:
        ax = pyplot.gca()
    ax.plot(transmission_rate_vs_time.index,
            transmission_rate_vs_time,
            linestyle = 'None', marker = 'o')
    ax.axhline(transmission_rate, color = 'black', linestyle = 'dashed')
    ax.set_ylabel('Transmission rate (per year)')
    ax.set_title(parameters.country)
    if show:
        pyplot.show()
